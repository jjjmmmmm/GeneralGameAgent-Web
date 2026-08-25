@echo off
title GeneralGameAgent-Web Launcher
cd /d "%~dp0"
echo Starting backend (:8000) and frontend (:5173) ...
..\..\GeneralGameAgent\GeneralGameAgent\.venv\Scripts\python.exe backend\scripts\start_web.py
pause
