# -*- coding: utf-8 -*-
"""指标计算公共库（S2 seam）——与课程 scripts/evaluate.py 口径完全一致。

设计：所有函数为纯函数（输入 dict 列表，输出数值），后端 API 与阶段 2 评测共用。
口径来源：GeneralGameAgent/scripts/evaluate.py（M3/M4 验收）：
  - 按键准确率：每帧 17 键全对比例，再对全部帧求平均
  - 触发精确率：Σboth / Σpred（pred 全量事件）
  - 触发召回率：Σboth / Σgt（gt 全量事件）
  - F1：2PR/(P+R)
  - 摇杆 MSE：每帧 mean((pred-gt)^2)，再平均
  - 摇杆相关系数：每帧 np.corrcoef，NaN（方差为 0）帧剔除后平均
"""
from __future__ import annotations

import math
from typing import Any


def btn_accuracy(n_correct: int, n_total: int = 17) -> float:
    """单帧 17 键全对比例。"""
    return n_correct / n_total if n_total > 0 else 0.0


def trigger_metrics(n_both: int, n_pred: int, n_gt: int) -> dict[str, float]:
    """聚合触发精确率/召回率/F1（与 evaluate.py 一致，分母防 0）。"""
    precision = n_both / max(1, n_pred)
    recall = n_both / max(1, n_gt)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def aggregate_frames(frames: list[dict[str, Any]]) -> dict[str, Any]:
    """从每帧明细聚合出与 evaluate.py 完全一致的合计指标。

    输入 frames 项需含：accuracy, jl_mse, jl_corr(可 None), pred_press, gt_press, both。
    输出：btn_accuracy, precision, recall, f1, jl_mse, jl_corr（与课程口径一一对应）。
    """
    n = len(frames)
    if n == 0:
        return {}

    accs = [f["accuracy"] for f in frames]
    mses = [f["jl_mse"] for f in frames]
    corrs = [f["jl_corr"] for f in frames if f.get("jl_corr") is not None]
    n_both = sum(f["both"] for f in frames)
    n_pred = sum(f["pred_press"] for f in frames)
    n_gt = sum(f["gt_press"] for f in frames)

    trig = trigger_metrics(n_both, n_pred, n_gt)
    return {
        "btn_accuracy": sum(accs) / n,
        "precision": trig["precision"],
        "recall": trig["recall"],
        "f1": trig["f1"],
        "jl_mse": sum(mses) / n,
        "jl_corr": sum(corrs) / len(corrs) if corrs else float("nan"),
        "events": {"pred": n_pred, "gt": n_gt, "both": n_both},
    }


def m4_verdict(metrics: dict[str, float]) -> dict[str, bool]:
    """M4 验收判定（与 evaluate.py 阈值一致）。"""
    return {
        "btn_accuracy_pass": metrics.get("btn_accuracy", 0) >= 0.5,
        "jl_corr_pass": metrics.get("jl_corr", -1) >= 0.4,
    }


def clamp_pct(v: float) -> float:
    return round(max(0.0, min(1.0, v)) * 100, 1)


def fmt_pct(v: float) -> str:
    if math.isnan(v):
        return "nan"
    return f"{clamp_pct(v)}%"
