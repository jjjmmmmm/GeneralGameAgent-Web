# -*- coding: utf-8 -*-
"""2.6 将 ft 评测结果写入 backend/data/results/ft.json（前端 /api/results 自动多版本）。

复用 evaluate_ft 的评测逻辑，同时输出 frames 明细 + metrics（baseline 与 ft 都写，
前端 v2 对比视图直接可用）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(r"D:/2+课产品/NitroGen")))

from nitrogen.inference_session import InferenceSession  # noqa: E402
from evaluate_ft import (  # noqa: E402
    BUTTONS, fetch_frame, get_gt, pick_frames, predict_vote,
)

sys.stdout.reconfigure(encoding="utf-8")

OUT_JSON = Path(__file__).resolve().parent.parent / "backend" / "data" / "results" / "ft.json"
BASE_CKPT = r"D:/2+课产品/_models/ng.pt"


def run_with_frames(sess, frames, k):
    rows = []
    agg = {"accs": [], "mse": [], "corr": [], "n_pred": 0, "n_gt": 0, "n_both": 0}
    for i, fid in enumerate(frames):
        img = fetch_frame(fid)
        gt_btn17, gt_jl = get_gt(fid)
        pred_btn17, pred_jl = predict_vote(sess, img, k)
        n_correct = int((pred_btn17 == gt_btn17).sum())
        acc = n_correct / len(BUTTONS)
        mse = float(np.mean((pred_jl - gt_jl) ** 2))
        sp, sg = np.std(pred_jl), np.std(gt_jl)
        corr = float(np.corrcoef(pred_jl, gt_jl)[0, 1]) if sp > 1e-6 and sg > 1e-6 else float("nan")
        n_pred = int(pred_btn17.sum()); n_gt = int(gt_btn17.sum())
        n_both = int(((pred_btn17 == 1) & (gt_btn17 == 1)).sum())
        agg["accs"].append(acc); agg["mse"].append(mse); agg["corr"].append(corr)
        agg["n_pred"] += n_pred; agg["n_gt"] += n_gt; agg["n_both"] += n_both
        rows.append({
            "idx": i, "fid": fid,
            "pred_press": n_pred, "gt_press": n_gt, "both": n_both,
            "correct_keys": f"{n_correct}/17", "accuracy": round(acc, 4),
            "jl_mse": round(mse, 4), "jl_corr": None if corr != corr else round(corr, 4),
        })
    n = len(rows)
    precision = agg["n_both"] / max(1, agg["n_pred"])
    recall = agg["n_both"] / max(1, agg["n_gt"])
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    corrs = [c for c in agg["corr"] if c == c]
    metrics = {
        "btn_accuracy": round(sum(agg["accs"]) / n, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "jl_mse": round(sum(agg["mse"]) / n, 4),
        "jl_corr": round(sum(corrs) / len(corrs), 4) if corrs else None,
        "events": {"pred": agg["n_pred"], "gt": agg["n_gt"], "both": agg["n_both"]},
        "m4": {"btn_accuracy_target": 0.5, "jl_corr_target": 0.4},
    }
    return {"metrics": metrics, "frames": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--ft", default=str(Path(__file__).resolve().parent / "ckpt" / "ft_lora.pt"))
    args = ap.parse_args()

    frames = pick_frames(args.n)
    print(f"测试集 {len(frames)} 帧，K={args.k}")

    print("评测 ft...")
    ft_sess = InferenceSession.from_ckpt(args.ft, old_layout=False, cfg_scale=1.0, context_length=1)
    ft_data = run_with_frames(ft_sess, frames, args.k)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({
        "version": "ft",
        "label": "微调后（LoRA r8）",
        "source": "train/export_ft_json.py",
        "metrics": ft_data["metrics"],
        "frames": ft_data["frames"],
        "segments": [],
        "demo": [],
        "button_freq": {},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {OUT_JSON}")
    print("metrics:", json.dumps(ft_data["metrics"], ensure_ascii=False))


if __name__ == "__main__":
    main()
