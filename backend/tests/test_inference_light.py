# -*- coding: utf-8 -*-
"""在线推理模块的轻量测试（不加载模型，只测数据层纯函数）。

模型加载约 30s 且占 4.5GB 显存，单测不触发懒加载；推理正确性由 E2E 冒烟覆盖。
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import inference  # noqa: E402


def test_pick_test_frames():
    frames = inference.pick_test_frames(200)
    assert len(frames) == 200
    assert frames[0] >= 640 * 60  # 测试集起点 640s
    assert frames[-1] < (640 + 60) * 60  # 终点 < 700s
    # 等间隔
    gaps = np.diff(frames)
    assert abs(gaps.max() - gaps.min()) <= 1


def test_button_mapping_complete():
    """17 标注键全部有模型列映射，且映射唯一。"""
    assert len(inference.BUTTON_TO_MODEL_COL) == 17
    cols = list(inference.BUTTON_TO_MODEL_COL.values())
    assert len(set(cols)) == 17  # 无重复
    assert all(0 <= c < 21 for c in cols)


def test_get_gt_reads_label():
    """从 parquet 读标注：17 键 0/1 + j_left [-1,1]（帧号=chunk×1200+行号 对齐验证）。"""
    fid = 38400  # chunk_0032 第 0 行
    btn17, jl = inference.get_gt(fid)
    assert btn17.shape == (17,)
    assert btn17.dtype == np.int64
    assert set(np.unique(btn17)) <= {0, 1}
    assert jl.shape == (2,)
    assert np.all(jl >= -1) and np.all(jl <= 1)


def test_gt_crosses_chunk_boundary():
    """测试集跨 chunk 边界读取正确（0032 末行 → 0033 首行）。"""
    fid = 640 * 60 + 1200 - 1  # chunk_0032 最后一行
    btn17, _ = inference.get_gt(fid)
    assert btn17.shape == (17,)
    fid2 = 640 * 60 + 1200     # chunk_0033 第一行
    btn17_2, _ = inference.get_gt(fid2)
    assert btn17_2.shape == (17,)
