# -*- coding: utf-8 -*-
"""阶段 3 数据准备：逐帧对比数据 → backend/data/results/comparison.json。

前端 v2 曲线叠加需要每帧 gt / baseline pred / ft pred 的摇杆值 + 按键事件。
评测 baseline(ng.pt) 与 ft(LoRA) 各 200 帧，逐帧保存 jl + buttons。

用法：python export_comparison.py [--n 200] [--k 3]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(r"D:/2+课产品/NitroGen")))

from nitrogen.inference_session import InferenceSession  # noqa: E402
from evaluate_ft import BUTTONS, fetch_frame, get_gt, pick_frames, predict_vote  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(__file__).resolve().parent.parent / "backend" / "data" / "results" / "comparison.json"
BASE_CKPT = r"D:/2+课产品/_models/ng.pt"
FT_CKPT = str(Path(__file__).resolve().parent / "ckpt" / "ft_lora.pt")


def collect(sess, frames, k):
    """逐帧收集 gt/base/ft 的 jl + 按键。"""
    rows = []
    for fid in frames:
        img = fetch_frame(fid)
        gt_btn17, gt_jl = get_gt(fid)
        pred_btn17, pred_jl = predict_vote(sess, img, k)
        rows.append({
            "fid": fid,
            "sec": round(fid / 60, 2),
            "gt_jl": gt_jl.tolist(),
            "pred_jl": pred_jl.tolist(),
            "gt_btns": [b for b, v in zip(BUTTONS, gt_btn17) if v],
            "pred_btns": [b for b, v in zip(BUTTONS, pred_btn17) if v],
            "acc": round(float((pred_btn17 == gt_btn17).mean()), 4),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    frames = pick_frames(args.n)
    print(f"测试集 {len(frames)} 帧，K={args.k}")

    t0 = time.time()
    print("baseline...")
    base_sess = InferenceSession.from_ckpt(BASE_CKPT, old_layout=False, cfg_scale=1.0, context_length=1)
    base_rows = collect(base_sess, frames, args.k)
    print(f"  {time.time()-t0:.0f}s")

    t0 = time.time()
    print("ft...")
    ft_sess = InferenceSession.from_ckpt(FT_CKPT, old_layout=False, cfg_scale=1.0, context_length=1)
    ft_rows = collect(ft_sess, frames, args.k)
    print(f"  {time.time()-t0:.0f}s")

    # 合并
    merged = []
    for b, f in zip(base_rows, ft_rows):
        merged.append({
            "fid": b["fid"], "sec": b["sec"],
            "gt_jl": b["gt_jl"], "base_jl": b["pred_jl"], "ft_jl": f["pred_jl"],
            "gt_btns": b["gt_btns"], "base_btns": b["pred_btns"], "ft_btns": f["pred_btns"],
            "base_acc": b["acc"], "ft_acc": f["acc"],
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "version": "comparison",
        "label": "微调前后逐帧对比（gt / baseline / ft）",
        "source": "train/export_comparison.py",
        "n": len(merged),
        "k": args.k,
        "frames": merged,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {OUT} ({OUT.stat().st_size/1024:.0f} KB)")
    print("样例:", json.dumps(merged[0], ensure_ascii=False))


if __name__ == "__main__":
    main()
