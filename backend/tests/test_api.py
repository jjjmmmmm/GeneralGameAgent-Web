# -*- coding: utf-8 -*-
"""S4 seam：FastAPI 四端点行为测试（TestClient，不启动真服务）。"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.main import app  # noqa: E402

client = TestClient(app)


def test_results_lists_baseline():
    r = client.get("/api/results")
    assert r.status_code == 200
    body = r.json()
    assert any(v["version"] == "baseline" for v in body["versions"])


def test_metrics_baseline():
    r = client.get("/api/metrics", params={"version": "baseline"})
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "baseline"
    assert body["metrics"]["btn_accuracy"] == 0.883
    assert body["verdict"] == {"btn_accuracy_pass": True, "jl_corr_pass": False}


def test_metrics_unknown_version_404():
    r = client.get("/api/metrics", params={"version": "nope"})
    assert r.status_code == 404


def test_segments_has_21():
    r = client.get("/api/segments", params={"version": "baseline"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["segments"]) == 21
    seg = body["segments"][0]
    assert {"start", "end", "file", "top5_frames", "top5_diffs"} <= set(seg)


def test_frames_pagination():
    r = client.get("/api/frames", params={"version": "baseline", "limit": 50, "offset": 100})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 200
    assert len(body["frames"]) == 50
    assert body["frames"][0]["idx"] == 100


def test_button_freq_has_stat_and_test():
    r = client.get("/api/button-freq", params={"version": "baseline"})
    assert r.status_code == 200
    freq = r.json()["button_freq"]
    assert "stat" in freq and "test" in freq
    assert "right_trigger" in freq["stat"]


def test_demo_has_5_frames():
    r = client.get("/api/demo", params={"version": "baseline"})
    assert r.status_code == 200
    assert len(r.json()["demo"]) == 5


def test_figure_png():
    r = client.get("/api/figures/joystick_distribution.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert len(r.content) > 1000


def test_figure_curves_subdir():
    r = client.get("/api/figures/curves/seq_060.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_figure_missing_404():
    r = client.get("/api/figures/no_such.png")
    assert r.status_code == 404


def test_figure_demo_subpath():
    r = client.get("/api/figures/demo/seq01_f0.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_figure_traversal_blocked():
    r = client.get("/api/figures/../results/baseline.json")
    assert r.status_code == 404
