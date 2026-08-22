# -*- coding: utf-8 -*-
"""2.5 测试集评测：baseline vs ft（K=3 多数票，与课程 evaluate.py 口径一致）。

测试集 = chunk_0032~0034（640~700s），等间隔采样 N 帧（默认 200）。
输出对比指标：按键准确率 / 触发精确率 / 触发召回率 / F1 / 摇杆 MSE / 摇杆相关。

用法：python evaluate_ft.py [--n 200] [--k 3] [--ft train/ckpt/ft_lora.pt]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import matplotlib.image as mpimg
import numpy as np
import polars as pl
import torch

sys.path.insert(0, str(Path(r"D:/2+课产品/NitroGen")))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from nitrogen.inference_session import InferenceSession  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

VIDEO = Path(r"D:/2+课产品/TOP 1 IN 2S _ Ranked 2v2 w_ oKhaliD (1).mp4")
SHARD = Path(r"D:/2+课产品/_data/SHARD_0088/Z1r1S--MJS4")
CHUNK_SIZE = 1200
FPS = 60
TEST_CHUNKS = ["0032", "0033", "0034"]
TEST_START_SEC = 640
BTN_THRESHOLD = 0.5
PRED_ROW = 0
MODEL_BUTTON_DIM = 21

BUTTONS = [
    "back", "dpad_down", "dpad_left", "dpad_right", "dpad_up", "east",
    "guide", "left_shoulder", "left_thumb", "left_trigger", "north",
    "right_shoulder", "right_thumb", "right_trigger", "south", "start", "west",
]
BUTTON_TO_MODEL_COL = {
    "back": 0, "dpad_down": 1, "dpad_left": 2, "dpad_right": 3, "dpad_up": 4,
    "east": 5, "guide": 6, "left_shoulder": 7, "left_thumb": 8, "left_trigger": 9,
    "north": 10, "right_shoulder": 14, "right_thumb": 15, "right_trigger": 16,
    "south": 18, "start": 19, "west": 20,
}

_chunk_cache: dict[str, pl.DataFrame] = {}
TMP = Path(__file__).resolve().parent / "cache" / "_eval_tmp"


def _chunk(cid: str) -> pl.DataFrame:
    if cid not in _chunk_cache:
        _chunk_cache[cid] = pl.read_parquet(SHARD / f"Z1r1S--MJS4_chunk_{cid}" / "actions_processed.parquet")
    return _chunk_cache[cid]


def get_gt(fid: int) -> tuple[np.ndarray, np.ndarray]:
    cid = f"{fid // CHUNK_SIZE:04d}"
    row = fid % CHUNK_SIZE
    df = _chunk(cid)
    r = df.slice(row, 1)
    btn17 = np.array([int(r[b].item()) for b in BUTTONS], dtype=int)
    jl = np.array(r["j_left"].to_list()[0], dtype=float)
    return btn17, jl


def fetch_frame(fid: int) -> np.ndarray:
    sec = fid / FPS
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / f"f{fid}.png"
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


def pick_frames(n: int) -> list[int]:
    total = len(TEST_CHUNKS) * CHUNK_SIZE
    step = total / n
    return [TEST_START_SEC * FPS + int(i * step) for i in range(n)]


def predict_vote(sess: InferenceSession, img: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    votes = np.zeros((MODEL_BUTTON_DIM,), dtype=int)
    last = None
    for _ in range(k):
        sess.reset()
        last = sess.predict(img)
        votes += (last["buttons"][PRED_ROW] > BTN_THRESHOLD).astype(int)
    pred21 = (votes >= (k + 1) // 2).astype(int)
    pred17 = np.array([pred21[BUTTON_TO_MODEL_COL[b]] for b in BUTTONS], dtype=int)
    pred_jl = last["j_left"][PRED_ROW].astype(float)
    return pred17, pred_jl


def evaluate(sess, frames, k) -> dict:
    agg = {"accs": [], "mse": [], "corr": [], "n_pred": 0, "n_gt": 0, "n_both": 0}
    for fid in frames:
        img = fetch_frame(fid)
        gt_btn17, gt_jl = get_gt(fid)
        pred_btn17, pred_jl = predict_vote(sess, img, k)
        n_correct = int((pred_btn17 == gt_btn17).sum())
        agg["accs"].append(n_correct / len(BUTTONS))
        agg["mse"].append(float(np.mean((pred_jl - gt_jl) ** 2)))
        sp, sg = np.std(pred_jl), np.std(gt_jl)
        agg["corr"].append(float(np.corrcoef(pred_jl, gt_jl)[0, 1]) if sp > 1e-6 and sg > 1e-6 else float("nan"))
        agg["n_pred"] += int(pred_btn17.sum())
        agg["n_gt"] += int(gt_btn17.sum())
        agg["n_both"] += int(((pred_btn17 == 1) & (gt_btn17 == 1)).sum())

    n = len(frames)
    precision = agg["n_both"] / max(1, agg["n_pred"])
    recall = agg["n_both"] / max(1, agg["n_gt"])
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    corrs = [c for c in agg["corr"] if c == c]
    return {
        "btn_accuracy": sum(agg["accs"]) / n,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "jl_mse": sum(agg["mse"]) / n,
        "jl_corr": sum(corrs) / len(corrs) if corrs else float("nan"),
        "events": {"pred": agg["n_pred"], "gt": agg["n_gt"], "both": agg["n_both"]},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--ft", default=str(Path(__file__).resolve().parent / "ckpt" / "ft_lora.pt"))
    args = ap.parse_args()

    frames = pick_frames(args.n)
    print(f"测试集 {len(frames)} 帧（640~700s），K={args.k} 多数票")

    print("=== baseline (ng.pt) ===")
    t0 = time.time()
    base_sess = InferenceSession.from_ckpt(
        r"D:/2+课产品/_models/ng.pt", old_layout=False, cfg_scale=1.0, context_length=1)
    print(f"加载 {time.time()-t0:.0f}s")
    base_metrics = evaluate(base_sess, frames, args.k)

    print("=== ft (LoRA) ===")
    t0 = time.time()
    ft_sess = InferenceSession.from_ckpt(args.ft, old_layout=False, cfg_scale=1.0, context_length=1)
    print(f"加载 {time.time()-t0:.0f}s")
    ft_metrics = evaluate(ft_sess, frames, args.k)

    print("\n=== 对比 ===")
    keys = ["btn_accuracy", "precision", "recall", "f1", "jl_mse", "jl_corr"]
    for k in keys:
        b, f = base_metrics[k], ft_metrics[k]
        print(f"  {k:14s}: baseline {b:+.4f} | ft {f:+.4f} | delta {f-b:+.4f}")
    print(f"  events: baseline {base_metrics['events']} | ft {ft_metrics['events']}")

    # M4 判定
    print("\n=== M4 判定 ===")
    print(f"  baseline 摇杆相关 ≥0.4: {base_metrics['jl_corr'] >= 0.4}")
    print(f"  ft       摇杆相关 ≥0.4: {ft_metrics['jl_corr'] >= 0.4}")
    print(f"  ft 召回率 vs baseline: {ft_metrics['recall']:.4f} vs {base_metrics['recall']:.4f} "
          f"({'2x+' if ft_metrics['recall'] >= 2*max(base_metrics['recall'],1e-9) else '未达2x'})")


if __name__ == "__main__":
    main()
