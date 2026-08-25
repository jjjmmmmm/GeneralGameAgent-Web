# -*- coding: utf-8 -*-
"""一键启动工作台：uvicorn 后端（:8000）+ vite 前端（:5173），就绪后自动打开浏览器。

双击入口：仓库根 `start_web.bat`
日志：backend/_uvicorn.log、frontend/_vite.log（每次启动覆盖）
关闭启动窗口或按 Ctrl+C 即停止两个服务。
"""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # backend/scripts -> backend -> 仓库根
BE = REPO / "backend"
FE = REPO / "frontend"
BE_LOG = BE / "_uvicorn.log"
FE_LOG = FE / "_vite.log"
BE_URL = "http://127.0.0.1:8000/api/health"
FE_URL = "http://127.0.0.1:5173/"

# venv 可能位置：仓库旁的工作区 GeneralGameAgent/.venv（课程环境），或已配置的其他位置
_VENV_CANDIDATES = [
    REPO.parent.parent / "GeneralGameAgent" / "GeneralGameAgent" / ".venv" / "Scripts" / "python.exe",
    REPO.parent / "GeneralGameAgent" / "GeneralGameAgent" / ".venv" / "Scripts" / "python.exe",
    REPO / ".venv" / "Scripts" / "python.exe",
]
VENV_PY = next((p for p in _VENV_CANDIDATES if p.exists()), _VENV_CANDIDATES[0])


def check(url: str, timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status < 400
    except Exception:
        return False


def wait(url: str, name: str, timeout: int = 150) -> bool:
    print(f"等待 {name} 就绪 ...", flush=True)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if check(url):
            print(f"  {name} OK（{time.time()-t0:.0f}s）", flush=True)
            return True
        time.sleep(2)
    print(f"  {name} 超时未就绪（{timeout}s）。请查看日志：{BE_LOG} / {FE_LOG}", flush=True)
    return False


def main() -> int:
    if not VENV_PY.exists():
        print(f"未找到 venv Python：{VENV_PY}")
        print("请确认 D:\\2+课产品\\GeneralGameAgent\\GeneralGameAgent\\.venv 存在。")
        input("按回车退出...")
        return 1
    if not (FE / "node_modules").exists():
        print("前端依赖未安装，请先执行：cd frontend && npm install")
        input("按回车退出...")
        return 1

    print("=== 启动后端（uvicorn :8000）===", flush=True)
    with open(BE_LOG, "w", encoding="utf-8") as f:
        p_be = subprocess.Popen(
            [str(VENV_PY), "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(BE), stdout=f, stderr=subprocess.STDOUT,
        )

    print("=== 启动前端（vite :5173）===", flush=True)
    with open(FE_LOG, "w", encoding="utf-8") as f:
        p_fe = subprocess.Popen(
            ["cmd", "/c", "npm run dev -- --host 127.0.0.1"],
            cwd=str(FE), stdout=f, stderr=subprocess.STDOUT,
        )

    ok_be = wait(BE_URL, "后端")
    ok_fe = wait(FE_URL, "前端")

    if ok_be and ok_fe:
        print("\n工作台已就绪：http://127.0.0.1:5173（后端 http://127.0.0.1:8000）", flush=True)
        webbrowser.open(FE_URL)
        print("服务运行中。关闭本窗口或按 Ctrl+C 停止。日志：backend/_uvicorn.log、frontend/_vite.log", flush=True)
    else:
        print("\n启动未完全就绪，请查看上述日志。", flush=True)

    # 保持前台运行；两个子进程任一退出或窗口关闭时收尾
    try:
        while p_be.poll() is None and p_fe.poll() is None:
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    p_be.terminate()
    p_fe.terminate()
    print("服务已停止。", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
