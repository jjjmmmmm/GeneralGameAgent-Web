# -*- coding: utf-8 -*-
"""素材管理模块测试（纯函数 + 临时素材生命周期，不涉及真实上传/拆帧）。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import assets  # noqa: E402


def test_parse_frame_spec_range():
    assert assets.parse_frame_spec("1~5") == [1, 2, 3, 4, 5]
    assert assets.parse_frame_spec("1-5") == [1, 2, 3, 4, 5]


def test_parse_frame_spec_mixed():
    assert assets.parse_frame_spec("1,3,5") == [1, 3, 5]
    assert assets.parse_frame_spec("1~3,7") == [1, 2, 3, 7]


def test_parse_frame_spec_reversed_range():
    assert assets.parse_frame_spec("5~1") == [1, 2, 3, 4, 5]


def test_parse_frame_spec_invalid():
    with pytest.raises(ValueError):
        assets.parse_frame_spec("abc")
    with pytest.raises(ValueError):
        assets.parse_frame_spec("1~x")


def test_asset_lifecycle(tmp_path, monkeypatch):
    """创建素材 → 列表可见 → 删除 → 列表不可见。"""
    monkeypatch.setattr(assets, "ASSETS_DIR", tmp_path / "assets")
    aid = assets.create_asset("测试素材")
    lst = assets.list_assets()
    assert len(lst) == 1 and lst[0]["id"] == aid and lst[0]["name"] == "测试素材"
    assets.delete_asset(aid)
    assert assets.list_assets() == []
