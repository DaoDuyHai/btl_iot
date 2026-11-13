# Khởi chạy AI Search Service
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "[*] Kích hoạt Python Virtualenv..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

Write-Host "🤖 Đang khởi chạy AI Search Service tại http://127.0.0.1:8000..." -ForegroundColor Cyan
if (Test-Path "venv\Scripts\uvicorn.exe") {
    & ".\venv\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8000 --reload
} else {
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}
