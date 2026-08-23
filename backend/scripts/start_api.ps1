# 启动后端 API（uvicorn :8000），托管方式避免被工具环境杀进程
$py = 'D:\2+课产品\GeneralGameAgent\GeneralGameAgent\.venv\Scripts\python.exe'
$be = 'D:\2+课产品\GeneralGameAgent-Web\GeneralGameAgent-Web\backend'
$log = "$be\_uvicorn.log"
$cmd = "cd /d `"$be`" && $py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > `"$log`" 2>&1"
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = "cmd.exe /c `"$cmd`"" }
Write-Output "PID=$($r.ProcessId)"
