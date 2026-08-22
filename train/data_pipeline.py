# -*- coding: utf-8 -*-
"""2.1 数据管线完整版：统计集抽帧缓存 + 动作标注对齐 + 训练/验证 split。

设计（2026-08-22）：
- 统计集 = chunk_0000~0031（视频 0~640s，帧 0~38399），训练数据
- 测试集 = chunk_0032~0034（640~700s），评测隔离（不进训练）
- 抽帧：ffmpeg 一次调用 -vf fps=60,scale=256:256 抽全部训练帧，
  存 uint8 RGB 分块 .npy（每块 1024 帧，共 7.5 块≈7.3GB）
- 动作标注：帧号→行号（统计集内连续），每帧取 18 步动作块（25 维打包），
  一次性载入内存（~66MB）
- 采样：随机 batch，每 batch N 帧 → img_proc 批量预处理 → 训练循环
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import polars as pl
import torch

sys.path.insert(0, str(Path(r"D:/2+课产品/NitroGen")))

sys.stdout.reconfigure(encoding="utf-8")

VIDEO = Path(r"D:/2+课产品/TOP 1 IN 2S _ Ranked 2v2 w_ oKhaliD (1).mp4")
SHARD = Path(r"D:/2+课产品/_data/SHARD_0088/Z1r1S--MJS4")
CACHE_DIR = Path(__file__).resolve().parent / "cache"

CHUNK_SIZE = 1200
FPS = 60
IMG_SIZE = 256
FRAMES_PER_BLOCK = 1024
ACTION_HORIZON = 18
ACTION_DIM = 25

BUTTONS = [
    "back", "dpad_down", "dpad_left", "dpad_right", "dpad_up", "east",
    "guide", "left_shoulder", "left_thumb", "left_trigger", "north",
    "right_shoulder", "right_thumb", "right_trigger", "south", "start", "west",
]
# 17 键标注 → 21 键模型列（课程 common.py BUTTON_TO_MODEL_COL，G1 源码法）
BUTTON_TO_MODEL_COL = {
    "back": 0, "dpad_down": 1, "dpad_left": 2, "dpad_right": 3, "dpad_up": 4,
    "east": 5, "guide": 6, "left_shoulder": 7, "left_thumb": 8, "left_trigger": 9,
    "north": 10, "right_shoulder": 14, "right_thumb": 15, "right_trigger": 16,
    "south": 18, "start": 19, "west": 20,
}

# 统计集/测试集区间（帧号）
TRAIN_START = 0
TRAIN_END = 32 * CHUNK_SIZE          # 0~38399
TEST_START = 32 * CHUNK_SIZE         # 38400
TEST_END = 35 * CHUNK_SIZE           # 41999


def build_frame_cache(force: bool = False, max_frames: int | None = None) -> int:
    """ffmpeg 一次抽统计集全部训练帧 → 256×256 uint8 分块 .npy。返回帧数。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    blocks = sorted(CACHE_DIR.glob("frames_*.npy"))
    if blocks and not force:
        # 已有缓存 → 返回总帧数
        return sum(int(np.load(p, mmap_mode="r").shape[0]) for p in blocks)

    # 训练区间：0~640s
    total_frames = TRAIN_END - TRAIN_START
    if max_frames:
        total_frames = min(total_frames, max_frames)
    duration = total_frames / FPS

    tmp = CACHE_DIR / "_raw_frames"
    tmp.mkdir(exist_ok=True)
    # 清旧
    for p in tmp.glob("f_*.npy"):
        p.unlink()

    # ffmpeg 一次抽帧：-ss 0 -t duration -vf fps=60,scale=256:256 -f rawvideo rgb24
    # 输出到 stdout 由 python 读（避免 3.8 万张 PNG 文件管理）
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-ss", "0", "-t", f"{duration:.2f}",
         "-i", str(VIDEO),
         "-vf", f"fps={FPS},scale={IMG_SIZE}:{IMG_SIZE}",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    frame_bytes = IMG_SIZE * IMG_SIZE * 3
    buf = bytearray()
    block = np.empty((0, IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    blk_idx = 0
    count = 0
    reached_max = False
    while True:
        chunk = proc.stdout.read(1 << 20)  # 1MB
        if not chunk:
            break
        buf.extend(chunk)
        while len(buf) >= frame_bytes:
            arr = np.frombuffer(bytes(buf[:frame_bytes]), dtype=np.uint8)
            buf = buf[frame_bytes:]
            frame = arr.reshape(IMG_SIZE, IMG_SIZE, 3)
            block = np.concatenate([block, frame[None]], axis=0)
            count += 1
            if block.shape[0] >= FRAMES_PER_BLOCK:
                np.save(CACHE_DIR / f"frames_{blk_idx:03d}.npy", block)
                blk_idx += 1
                block = np.empty((0, IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
            if max_frames and count >= max_frames:
                reached_max = True
                break
        if reached_max:
            break
    if block.shape[0]:
        np.save(CACHE_DIR / f"frames_{blk_idx:03d}.npy", block)
    proc.stdout.close()
    proc.wait()
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 抽帧失败: {err[:500]}")
    print(f"抽帧完成: {count} 帧 → {CACHE_DIR}")
    return count


def load_frames() -> np.ndarray:
    """加载全部训练帧（内存映射，不一次读入）。返回帧数组。"""
    blocks = sorted(CACHE_DIR.glob("frames_*.npy"))
    if not blocks:
        raise FileNotFoundError("帧缓存为空，先 build_frame_cache()")
    return np.concatenate([np.load(p, mmap_mode="r") for p in blocks], axis=0)


def _build_action_block(df: pl.DataFrame, start_row: int) -> np.ndarray:
    """从标注 df 的 start_row 取 18 步动作块，打包成 (18, 25)。"""
    n = df.height
    if start_row + ACTION_HORIZON > n:
        start_row = n - ACTION_HORIZON
    acts = df.slice(start_row, ACTION_HORIZON)
    rows = acts.to_numpy()
    cols = df.columns
    out = np.zeros((ACTION_HORIZON, ACTION_DIM), dtype=np.float32)
    for i, r in enumerate(rows):
        d = {c: r[j] for j, c in enumerate(cols)}
        btns21 = np.zeros(21, dtype=np.float32)
        for b, col in BUTTON_TO_MODEL_COL.items():
            btns21[col] = float(d[b])
        jl = np.array(d["j_left"], dtype=np.float32)
        jr = np.array(d["j_right"], dtype=np.float32)
        # 布局 [buttons(21), j_left(2), j_right(2)]，摇杆归一化 [0,1]
        out[i] = np.concatenate([btns21, (jl + 1) / 2, (jr + 1) / 2])
    return out


def build_actions_cache() -> np.ndarray:
    """载入统计集全部动作标注 (38400, 18, 25) 并缓存 .npy。"""
    cache = CACHE_DIR / "actions.npy"
    if cache.exists():
        return np.load(cache, mmap_mode="r")

    dfs = []
    for c in range(32):
        p = SHARD / f"Z1r1S--MJS4_chunk_{c:04d}" / "actions_processed.parquet"
        df = pl.read_parquet(p)
        # 统一列类型：j_left/j_right → List(Float64)；布尔键 → Int64
        casts = []
        for col in df.columns:
            if col in ("j_left", "j_right"):
                casts.append(pl.col(col).cast(pl.List(pl.Float64)))
            elif col in BUTTONS:
                casts.append(pl.col(col).cast(pl.Int64))
        if casts:
            df = df.with_columns(casts)
        dfs.append(df)
    df = pl.concat(dfs)

    blocks = []
    step = 512
    for start in range(0, df.height, step):
        end = min(start + step, df.height)
        # 帧号 = 行号（统计集内连续）
        blocks.append(np.stack([_build_action_block(df, r) for r in range(start, end)]))
    actions = np.concatenate(blocks, axis=0)  # (38400, 18, 25)
    np.save(cache, actions)
    print(f"动作标注缓存: {actions.shape} → {cache}")
    return actions


def split_indices(val_ratio: float = 0.05, seed: int = 42):
    """训练/验证 split：统计集内随机划分（不打乱时序，按帧号）。"""
    n = TRAIN_END - TRAIN_START
    idx = np.arange(n)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    n_val = int(n * val_ratio)
    val = np.sort(perm[:n_val])
    train = np.sort(perm[n_val:])
    return train, val


def make_batch(frames: np.ndarray, actions: np.ndarray, idxs: np.ndarray,
               img_proc) -> dict:
    """从索引集采样一个 batch（每帧 1 张 + 18 步动作），img_proc 批量预处理。

    返回 tokenizer.encode 兼容的输入（frames/dropped_frames/buttons/j_left/j_right）。
    """
    n = len(idxs)
    imgs = [frames[i] for i in idxs]
    pv = img_proc(imgs, return_tensors="pt")["pixel_values"]  # (N,3,256,256)
    return {
        "frames": pv,
        "dropped_frames": torch.zeros(n, dtype=torch.bool),
        "buttons": torch.from_numpy(actions[idxs][:, :, :21]),
        "j_left": torch.from_numpy(actions[idxs][:, :, 21:23]),
        "j_right": torch.from_numpy(actions[idxs][:, :, 23:25]),
        "game": None,
    }


if __name__ == "__main__":
    # 快速自测：抽 20 帧 + 动作块 + batch
    import numpy as np
    CACHE_DIR.mkdir(exist_ok=True)
    for p in CACHE_DIR.glob("_test_*"):
        p.unlink()
    print("抽 20 帧测试...")
    n = build_frame_cache(force=True, max_frames=20)
    print(f"  frames={n}")
    f = load_frames()
    print(f"  shape={f.shape} dtype={f.dtype}")
    acts = build_actions_cache()
    print(f"  actions={acts.shape}")
    from transformers import AutoImageProcessor
    proc = AutoImageProcessor.from_pretrained("google/siglip2-large-patch16-256")
    train, val = split_indices()
    print(f"  split: train={len(train)} val={len(val)}")
    b = make_batch(f, acts, train[:4], proc)
    print(f"  batch frames={tuple(b['frames'].shape)} buttons={tuple(b['buttons'].shape)}")
