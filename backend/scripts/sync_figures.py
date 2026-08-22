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
DEMO_SRC = Path(r"D:/2+课产品/_data/frames/Z1r1S--MJS4/seq")


def main():
    if SRC.exists():
        (DST / "curves").mkdir(parents=True, exist_ok=True)
        n = 0
        for p in SRC.glob("*.png"):
            shutil.copy2(p, DST / p.name)
            n += 1
        for p in (SRC / "curves").glob("*.png"):
            shutil.copy2(p, DST / "curves" / p.name)
            n += 1
        print(f"synced {n} figures -> {DST}")
    else:
        print(f"SKIP: 课程结果图不存在 {SRC}")

    if DEMO_SRC.exists():
        (DST / "demo").mkdir(parents=True, exist_ok=True)
        m = 0
        for p in DEMO_SRC.glob("seq01_f*.png"):
            shutil.copy2(p, DST / "demo" / p.name)
            m += 1
        print(f"synced {m} demo frames -> {DST / 'demo'}")
    else:
        print(f"SKIP: 演示帧图不存在 {DEMO_SRC}")


if __name__ == "__main__":
    main()
