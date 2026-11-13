# Khởi chạy AI Search Service
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$PythonExec = "python"
if (Test-Path "venv\Scripts\python.exe") {
    $PythonExec = "venv\Scripts\python.exe"
}

Write-Host "🤖 Đang khởi chạy AI Search Service tại http://127.0.0.1:8000..." -ForegroundColor Cyan
& $PythonExec -m uvicorn main:app --host 0.0.0.0 --port 8000
