# 启动本地开发：后端 uvicorn :8000 + 前端 vite :5173（托管方式，避免被杀进程）
$ErrorActionPreference = 'Continue'

$py = 'D:\2+课产品\GeneralGameAgent\GeneralGameAgent\.venv\Scripts\python.exe'
$be = 'D:\2+课产品\GeneralGameAgent-Web\GeneralGameAgent-Web\backend'
$fe = 'D:\2+课产品\GeneralGameAgent-Web\GeneralGameAgent-Web\frontend'

$beCmd = "cd /d `"$be`" && $py -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
$feCmd = "cd /d `"$fe`" && npm run dev -- --port 5173 --host 127.0.0.1"

$r1 = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = "cmd.exe /c `"$beCmd`"" }
$r2 = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = "cmd.exe /c `"$feCmd`"" }

Write-Output "backend PID=$($r1.ProcessId)"
Write-Output "frontend PID=$($r2.ProcessId)"
Write-Output "api:   http://127.0.0.1:8000/api/health"
Write-Output "front: http://127.0.0.1:5173/"
