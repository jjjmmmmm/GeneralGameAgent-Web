# -*- coding: utf-8 -*-
"""S2 seam：metrics_lib 与课程 evaluate.py 口径完全一致。

用 baseline.json 的 200 帧真实明细做回归：
aggregate_frames 重算出的合计，必须与课程 test_set_metrics.md 的合计一致。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import metrics_lib  # noqa: E402


def load_baseline():
    p = Path(__file__).resolve().parent.parent / "data" / "results" / "baseline.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_aggregate_matches_course_metrics():
    """从 200 帧明细重算的合计 ≈ 课程 test_set_metrics.md 数值。

    课程 md 中数值以 .1%/.3f 格式化输出（如 88.3%、0.063），存在舍入误差，
    故用 1e-3 容差；events（整数）必须完全一致。
    """
    data = load_baseline()
    agg = metrics_lib.aggregate_frames(data["frames"])
    m = data["metrics"]
    for k in ("btn_accuracy", "precision", "recall", "f1", "jl_mse", "jl_corr"):
        assert abs(agg[k] - m[k]) < 1e-3, f"{k}: {agg[k]} != {m[k]}"
    assert agg["events"] == m["events"]


def test_course_known_values():
    """课程记录的具体数值（M3/M4 验收口径）。"""
    data = load_baseline()
    m = data["metrics"]
    assert m["btn_accuracy"] == 0.883
    assert m["recall"] == 0.042
    assert m["f1"] == 0.079
    assert round(m["jl_corr"], 3) == 0.063


def test_verdict_baseline():
    """M4 判定：按键达标、摇杆未达标。"""
    data = load_baseline()
    v = metrics_lib.m4_verdict(data["metrics"])
    assert v["btn_accuracy_pass"] is True
    assert v["jl_corr_pass"] is False


def test_verdict_synthetic_pass():
    """合成达标数据。"""
    metrics = {"btn_accuracy": 0.9, "jl_corr": 0.7}
    v = metrics_lib.m4_verdict(metrics)
    assert v == {"btn_accuracy_pass": True, "jl_corr_pass": True}


def test_trigger_metrics_known():
    """events → P/R/F1 与课程一致（31/400/17），容差 1e-3（md 舍入）。"""
    trig = metrics_lib.trigger_metrics(17, 31, 400)
    assert abs(trig["precision"] - 0.548) < 1e-3
    assert abs(trig["recall"] - 0.042) < 1e-3
    assert abs(trig["f1"] - 0.079) < 1e-3
