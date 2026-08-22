# -*- coding: utf-8 -*-
"""同步课程结果图到 backend/data/figures（PNG 不入仓，运行时同步）。

用法：cd backend && python scripts/sync_figures.py
"""
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SRC = Path(r"D:/2+课产品/GeneralGameAgent/GeneralGameAgent/results/figures")
DST = Path(__file__).resolve().parent.parent / "data" / "figures"


def main():
    if not SRC.exists():
        print(f"SKIP: 课程结果图不存在 {SRC}")
        return
    (DST / "curves").mkdir(parents=True, exist_ok=True)
    n = 0
    for p in SRC.glob("*.png"):
        shutil.copy2(p, DST / p.name)
        n += 1
    for p in (SRC / "curves").glob("*.png"):
        shutil.copy2(p, DST / "curves" / p.name)
        n += 1
    print(f"synced {n} figures -> {DST}")


if __name__ == "__main__":
    main()
