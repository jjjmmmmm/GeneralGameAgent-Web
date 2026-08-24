# -*- coding: utf-8 -*-
"""诊断脚本：现有 ft 权重在训练集（chunk 0000~0031）上的摇杆相关。

目的：区分摇杆相关低的两种成因——
  A) 学不会：训练集（模型见过的帧）上摇杆相关也低 → 换数据无用，需摇杆加权 loss
  B) 泛化差：训练集上明显更高（>0.3），测试集低 → 多视频训练可能提升泛化

用法：python diagnose_train_set.py [--n 200] [--k 3]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(r"D:/2+课产品/NitroGen")))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from nitrogen.inference_session import InferenceSession  # noqa: E402

# 复用 evaluate_ft.py 的抽帧/标注/推理/指标组件（同口径）
from evaluate_ft import CHUNK_SIZE, evaluate  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

TRAIN_CHUNKS = 32  # chunk 0000~0031 = 帧 0~38399 = 0~640s
NG = r"D:/2+课产品/_models/ng.pt"
FT = str(Path(__file__).resolve().parent / "ckpt" / "ft_lora.pt")


def pick_train_frames(n: int) -> list[int]:
    total = TRAIN_CHUNKS * CHUNK_SIZE
    step = total / n
    return [int(i * step) for i in range(n)]


def run(name: str, ckpt: str, frames: list[int], k: int) -> dict:
    print(f"=== {name} ===")
    t0 = time.time()
    sess = InferenceSession.from_ckpt(ckpt, old_layout=False, cfg_scale=1.0, context_length=1)
    print(f"加载 {time.time()-t0:.0f}s")
    m = evaluate(sess, frames, k)
    print(f"  btn_accuracy={m['btn_accuracy']:.4f}  recall={m['recall']:.4f}  "
          f"jl_mse={m['jl_mse']:.4f}  jl_corr={m['jl_corr']:+.4f}")
    print(f"  events: {m['events']}")
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--ft", default=str(Path(__file__).resolve().parent / "ckpt" / "ft_lora.pt"))
    args = ap.parse_args()

    frames = pick_train_frames(args.n)
    print(f"训练集 {len(frames)} 帧（chunk 0000~0031，0~640s），K={args.k} 多数票")

    base = run("baseline (ng.pt)", NG, frames, args.k)
    ft = run(f"ft ({Path(args.ft).name})", args.ft, frames, args.k)

    print("\n=== 诊断结论（训练集摇杆相关） ===")
    print(f"  训练集 jl_corr: baseline {base['jl_corr']:+.3f} | ft {ft['jl_corr']:+.3f}")
    print(f"  参考：旧 ft 训练集 +0.042 / 测试集 +0.126；目标 ≥0.4")
    if ft["jl_corr"] >= 0.4:
        print(f"  → ft 训练集相关 {ft['jl_corr']:+.3f} ≥ 0.4：模型已学会摇杆映射")
    elif ft["jl_corr"] >= 0.1:
        print(f"  → ft 训练集相关 {ft['jl_corr']:+.3f} 明显抬头（旧 ft +0.042）：摇杆加权生效")
    else:
        print(f"  → ft 训练集相关 {ft['jl_corr']:+.3f} 未抬头（旧 ft +0.042）：加权不足或需调参")


if __name__ == "__main__":
    main()
