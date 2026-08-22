# -*- coding: utf-8 -*-
"""在线推理服务：懒加载 InferenceSession + 单帧/批量推理。

设计（用户 2026-08-22 确认）：
  - 懒加载：首次调用才加载 ng.pt（约 30s），加载完缓存复用；启动 Web 不加载
  - 集成进 FastAPI（不另起 serve 进程），复用 spike 验证过的推理路径
  - 数据对齐：帧号 = chunk×1200 + 行号；PRED_ROW=0（D7 实测排除时序偏移）
  - 17 键标注 ↔ 21 键模型列映射复用课程 common.py 结论（硬编码，自包含）
"""
from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

import matplotlib.image as mpimg
import numpy as np
import polars as pl
import torch

_NITROGEN_DIR = Path(r"D:/2+课产品/NitroGen")
import sys

if str(_NITROGEN_DIR) not in sys.path:
    sys.path.insert(0, str(_NITROGEN_DIR))

from nitrogen.inference_session import InferenceSession  # noqa: E402

# ---- 数据布局常量（D5/T1 查证，硬编码保证自包含）----
SHARD = Path(r"D:/2+课产品/_data/SHARD_0088/Z1r1S--MJS4")
VIDEO = Path(r"D:/2+课产品/TOP 1 IN 2S _ Ranked 2v2 w_ oKhaliD (1).mp4")
CKPT = Path(r"D:/2+课产品/_models/ng.pt")

CHUNK_SIZE = 1200
FPS = 60
MODEL_BUTTON_DIM = 21
BTN_THRESHOLD = 0.5
PRED_ROW = 0

BUTTONS = [
    "back", "dpad_down", "dpad_left", "dpad_right", "dpad_up", "east",
    "guide", "left_shoulder", "left_thumb", "left_trigger", "north",
    "right_shoulder", "right_thumb", "right_trigger", "south", "start", "west",
]

# 标注键 → 模型 buttons 21 维列号
BUTTON_TO_MODEL_COL = {
    "back": 0, "dpad_down": 1, "dpad_left": 2, "dpad_right": 3, "dpad_up": 4,
    "east": 5, "guide": 6, "left_shoulder": 7, "left_thumb": 8, "left_trigger": 9,
    "north": 10, "right_shoulder": 14, "right_thumb": 15, "right_trigger": 16,
    "south": 18, "start": 19, "west": 20,
}

TEST_CHUNKS = ["0032", "0033", "0034"]
TEST_START_SEC = 640
TEST_DURATION_SEC = 60

# ---- 懒加载单例 ----
_session = None
_session_lock = threading.Lock()
_chunk_cache: dict[str, pl.DataFrame] = {}

TMP_FRAMES = Path(__file__).resolve().parent.parent / "data" / "_tmp_frames"


def _load_session():
    """懒加载（线程安全）。首次约 30s，需显式提示。"""
    global _session
    if _session is not None:
        return _session
    with _session_lock:
        if _session is None:
            TMP_FRAMES.mkdir(parents=True, exist_ok=True)
            _session = InferenceSession.from_ckpt(
                str(CKPT), old_layout=False, cfg_scale=1.0, context_length=1
            )
    return _session


def is_loaded() -> bool:
    return _session is not None


def fetch_frame(fid: int) -> np.ndarray:
    """按帧号从视频抽帧，返回 HxWx3 uint8。"""
    sec = fid / FPS
    p = TMP_FRAMES / f"f{fid}.png"
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


def _chunk_df(cid: str) -> pl.DataFrame:
    if cid not in _chunk_cache:
        _chunk_cache[cid] = pl.read_parquet(
            SHARD / f"Z1r1S--MJS4_chunk_{cid}" / "actions_processed.parquet"
        )
    return _chunk_cache[cid]


def get_gt(fid: int) -> tuple[np.ndarray, np.ndarray]:
    """按帧号取标注：17 键按钮 + j_left[-1,1]。"""
    cid = f"{fid // CHUNK_SIZE:04d}"
    row = fid % CHUNK_SIZE
    df = _chunk_df(cid)
    r = df.slice(row, 1)
    btn17 = np.array([int(r[b].item()) for b in BUTTONS], dtype=int)
    jl = np.array(r["j_left"].to_list()[0], dtype=float)
    return btn17, jl


def predict_fid(fid: int, k: int = 1) -> dict:
    """单帧推理：抽帧 → K 次多数票 → 返回 pred/gt 对齐结果。

    K=1 时单次；K>=2 时按钮多数票（flow matching 随机性控制）。
    返回 17 键视图（与标注对齐），避免前端处理 21→17 映射。
    """
    session = _load_session()
    img = fetch_frame(fid)
    gt_btn17, gt_jl = get_gt(fid)

    votes = np.zeros((MODEL_BUTTON_DIM,), dtype=int)
    last_pred = None
    t0 = time.time()
    for _ in range(k):
        session.reset()
        pred = session.predict(img)
        votes += (pred["buttons"][PRED_ROW] > BTN_THRESHOLD).astype(int)
        last_pred = pred
    dt = time.time() - t0

    pred_btn21 = (votes >= (k + 1) // 2).astype(int)
    pred_btn17 = np.array(
        [pred_btn21[BUTTON_TO_MODEL_COL[b]] for b in BUTTONS], dtype=int
    )
    pred_jl = last_pred["j_left"][PRED_ROW].astype(float)

    n_gt = int(gt_btn17.sum())
    n_pred = int(pred_btn17.sum())
    n_both = int(((pred_btn17 == 1) & (gt_btn17 == 1)).sum())
    n_correct = int((pred_btn17 == gt_btn17).sum())
    accuracy = n_correct / len(BUTTONS)
    jl_mse = float(np.mean((pred_jl - gt_jl) ** 2))

    return {
        "fid": fid,
        "sec": round(fid / FPS, 2),
        "infer_s": round(dt, 3),
        "buttons": {
            "gt": [b for b, v in zip(BUTTONS, gt_btn17) if v],
            "pred": [b for b, v in zip(BUTTONS, pred_btn17) if v],
            "n_gt": n_gt, "n_pred": n_pred, "n_both": n_both,
            "n_correct": n_correct, "accuracy": accuracy,
        },
        "j_left": {
            "gt": gt_jl.tolist(), "pred": pred_jl.tolist(),
            "mse": jl_mse,
        },
    }


def pick_test_frames(n: int = 200) -> list[int]:
    """测试集 3600 帧等间隔取 n 帧。"""
    total = len(TEST_CHUNKS) * CHUNK_SIZE
    step = total / n
    return [TEST_START_SEC * FPS + int(i * step) for i in range(n)]


def run_evaluate(n: int = 200, k: int = 3, progress_cb=None) -> dict:
    """批量评测测试集：K 次多数票，输出 metrics（与课程 evaluate.py 口径一致）。"""
    from . import metrics_lib

    session = _load_session()
    frames = pick_test_frames(n)
    t_start = time.time()

    rows = []
    agg = {"n_pred": 0, "n_gt": 0, "n_both": 0, "accs": [], "jl_mse": [], "jl_corr": []}

    for i, fid in enumerate(frames):
        img = fetch_frame(fid)
        gt_btn17, gt_jl = get_gt(fid)
        votes = np.zeros((MODEL_BUTTON_DIM,), dtype=int)
        last_pred = None
        for _ in range(k):
            session.reset()
            pred = session.predict(img)
            votes += (pred["buttons"][PRED_ROW] > BTN_THRESHOLD).astype(int)
            last_pred = pred
        pred_btn21 = (votes >= (k + 1) // 2).astype(int)
        pred_btn17 = np.array([pred_btn21[BUTTON_TO_MODEL_COL[b]] for b in BUTTONS], dtype=int)
        pred_jl = last_pred["j_left"][PRED_ROW].astype(float)

        n_pred = int(pred_btn17.sum())
        n_gt = int(gt_btn17.sum())
        n_both = int(((pred_btn17 == 1) & (gt_btn17 == 1)).sum())
        n_correct = int((pred_btn17 == gt_btn17).sum())
        acc = n_correct / len(BUTTONS)
        jl_mse = float(np.mean((pred_jl - gt_jl) ** 2))
        std_p, std_g = np.std(pred_jl), np.std(gt_jl)
        jl_corr = float(np.corrcoef(pred_jl, gt_jl)[0, 1]) if std_p > 1e-6 and std_g > 1e-6 else float("nan")

        agg["n_pred"] += n_pred
        agg["n_gt"] += n_gt
        agg["n_both"] += n_both
        agg["accs"].append(acc)
        agg["jl_mse"].append(jl_mse)
        agg["jl_corr"].append(jl_corr)
        rows.append({
            "idx": i, "fid": fid,
            "pred_press": n_pred, "gt_press": n_gt, "both": n_both,
            "correct_keys": f"{n_correct}/17", "accuracy": round(acc, 4),
            "jl_mse": round(jl_mse, 4), "jl_corr": None if jl_corr != jl_corr else round(jl_corr, 4),
        })
        if progress_cb and (i + 1) % 20 == 0:
            progress_cb(i + 1, n)

    n = len(rows)
    metrics = metrics_lib.aggregate_frames([
        {
            "accuracy": r["accuracy"], "jl_mse": r["jl_mse"], "jl_corr": r["jl_corr"],
            "pred_press": r["pred_press"], "gt_press": r["gt_press"], "both": r["both"],
        }
        for r in rows
    ])
    metrics["avg_infer_s"] = round((time.time() - t_start) / n, 3)
    metrics["total_s"] = round(time.time() - t_start, 1)

    return {"frames": rows, "metrics": metrics}
