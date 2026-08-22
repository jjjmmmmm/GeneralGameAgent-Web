# -*- coding: utf-8 -*-
"""阶段 0 spike：1 个训练 step 跑通（loss 有限且下降 + 显存 <8G）。

数据：统计集抽 4 batch（每 batch 1 帧 + 18 步动作块），帧号=chunk×1200+行号 对齐。
流程：加载 ng.pt → tokenizer.encode 构造 data → forward → flow matching loss → backward → 1 step。
关键：tokenizer.encode 内部 pack_actions 会归一化摇杆并打包成 25 维，输入给原始 buttons/j_left/j_right。
输出：loss 前/后值 + 显存峰值记录。
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(r"D:/2+课产品/NitroGen")))
import numpy as np
import polars as pl
import torch

sys.stdout.reconfigure(encoding="utf-8")

CKPT = r"D:/2+课产品/_models/ng.pt"
SHARD = Path(r"D:/2+课产品/_data/SHARD_0088/Z1r1S--MJS4")
VIDEO = Path(r"D:/2+课产品/TOP 1 IN 2S _ Ranked 2v2 w_ oKhaliD (1).mp4")

CHUNK_SIZE = 1200
FPS = 60
# 17 键标注 → 21 键模型列（课程 common.py MODEL_COL_TO_BUTTON 反查）
BTN_TO_MODEL_COL = {
    "back": 0, "dpad_down": 1, "dpad_left": 2, "dpad_right": 3, "dpad_up": 4,
    "east": 5, "guide": 6, "left_shoulder": 7, "left_thumb": 8, "left_trigger": 9,
    "north": 10, "right_shoulder": 14, "right_thumb": 15, "right_trigger": 16,
    "south": 18, "start": 19, "west": 20,
}


def load_chunk(cid: str) -> pl.DataFrame:
    return pl.read_parquet(SHARD / f"Z1r1S--MJS4_chunk_{cid}" / "actions_processed.parquet")


def build_sample_raw(fid: int, chunk_cache: dict) -> dict:
    """按帧号取 18 步动作块的原始标注（buttons 21 维、j_left/j_right [-1,1] 原值）。"""
    cid = f"{fid // CHUNK_SIZE:04d}"
    row = fid % CHUNK_SIZE
    if cid not in chunk_cache:
        chunk_cache[cid] = load_chunk(cid)
    df = chunk_cache[cid]
    if row + 18 > df.height:
        row = df.height - 18

    acts = df.slice(row, 18)
    n = acts.height
    buttons = np.zeros((n, 21), dtype=np.float32)
    jl = np.zeros((n, 2), dtype=np.float32)
    jr = np.zeros((n, 2), dtype=np.float32)
    for i in range(n):
        d = {c: acts.row(i)[j] for j, c in enumerate(df.columns)}
        for b, col in BTN_TO_MODEL_COL.items():
            buttons[i, col] = float(d[b])
        jl[i] = np.array(d["j_left"], dtype=np.float32)
        jr[i] = np.array(d["j_right"], dtype=np.float32)
    return {"buttons": buttons, "j_left": jl, "j_right": jr}


def fetch_frame(fid: int, tmp_dir: Path) -> np.ndarray:
    """按帧号抽帧（ffmpeg -ss 精确到秒），返回 HxWx3 uint8。"""
    import subprocess
    import matplotlib.image as mpimg
    sec = fid / FPS
    p = tmp_dir / f"f{fid}.png"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{sec:.3f}",
         "-i", str(VIDEO), "-frames:v", "1", "-q:v", "2", str(p)],
        check=True, capture_output=True,
    )
    img = mpimg.imread(str(p))
    p.unlink()
    if img.dtype != np.uint8:
        img = (img * 255).astype(np.uint8) if img.max() <= 1.0 else img.astype(np.uint8)
    if img.shape[-1] == 4:
        img = img[..., :3]
    return img


def main():
    from nitrogen.inference_session import load_model

    fids = [0, 1200, 2400, 3600]  # 统计集 4 帧（4 batch）
    chunk_cache = {}
    tmp_dir = Path(r"D:/2+课产品/GeneralGameAgent-Web/GeneralGameAgent-Web/train/_tmp_frames")
    tmp_dir.mkdir(exist_ok=True)

    print("=== 加载模型 ===")
    model, tokenizer, img_proc, ckpt_config, game_mapping, _ = load_model(CKPT)
    tokenizer.train()  # load_model 里调了 tokenizer.eval()，训练数据构造必须切回 training 模式

    # 贴近真实 LoRA 训练配置：冻结视觉编码器（显存大头），只训主干+动作头
    model.vision_encoder.requires_grad_(False)
    model.vision_encoder.eval()

    # 1) 逐样本 tokenizer.encode（frame_per_sample=1，无 batch），再拼 batch
    print("\n=== 构造训练数据 ===")
    batch = None
    for fid in fids:
        frame = fetch_frame(fid, tmp_dir)
        pv = img_proc([frame], return_tensors="pt")["pixel_values"]  # (1,3,256,256)
        raw = build_sample_raw(fid, chunk_cache)
        sample = {
            "frames": pv,                                    # (1,3,256,256)
            "dropped_frames": torch.zeros(1, dtype=torch.bool),
            "buttons": raw["buttons"][None],    # (1,18,21) numpy，pack_actions 用 np.concatenate
            "j_left": raw["j_left"][None],      # (1,18,2)
            "j_right": raw["j_right"][None],    # (1,18,2)
            "game": None,
        }
        tokenized = tokenizer.encode(sample)
        for k, v in tokenized.items():
            if isinstance(v, torch.Tensor):
                tokenized[k] = v.unsqueeze(0)
            elif isinstance(v, np.ndarray):
                tokenized[k] = torch.tensor(v).unsqueeze(0)
            else:
                tokenized[k] = [v]
        if batch is None:
            batch = tokenized
        else:
            for k, v in tokenized.items():
                if isinstance(v, torch.Tensor):
                    batch[k] = torch.cat([batch[k], v], dim=0)

    print("batch keys:", list(batch.keys()))
    for k, v in batch.items():
        if isinstance(v, torch.Tensor):
            print(f"  {k}: {tuple(v.shape)} {v.dtype}")

    # 2) M0 验收核心：训练 20 步，前 5 步 loss 均值 vs 后 5 步 loss 均值
    #    flow matching 的 t/noise 每次 forward 随机采样，单步 loss 不可比；
    #    统计均值消除随机性，才是有意义的"loss 下降"判定。
    model.train()
    data = {k: (v.to("cuda") if isinstance(v, torch.Tensor) else v) for k, v in batch.items()}
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)

    N_STEPS = 20
    losses = []
    for step in range(N_STEPS):
        torch.manual_seed(1000 + step)
        opt.zero_grad()
        loss = model(data)["loss"]
        loss.backward()
        opt.step()
        losses.append(loss.item())
        if step % 5 == 0 or step == N_STEPS - 1:
            print(f"[step {step:2d}] loss = {loss.item():.6f}")

    head = sum(losses[:5]) / 5
    tail = sum(losses[-5:]) / 5
    print(f"\n=== loss 均值对比: 前5步 {head:.6f} -> 后5步 {tail:.6f} (下降 {head - tail:+.6f}) ===")
    print(f"=== {'PASS' if tail < head else 'FAIL'}: 后段均值低于前段 ===")

    # 3) 显存
    max_mem = torch.cuda.max_memory_allocated() / 1024**3
    print(f"=== 显存峰值: {max_mem:.2f} GB (<8G {'PASS' if max_mem < 8 else 'FAIL'}) ===")

    return head, tail, max_mem


if __name__ == "__main__":
    t0 = time.time()
    head, tail, mem = main()
    print(f"\nDONE in {time.time()-t0:.0f}s | loss {head:.6f} -> {tail:.6f} | max_mem {mem:.2f}GB")
