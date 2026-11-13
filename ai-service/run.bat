@echo off
chcp 65001 > nul
echo ========================================================
echo   🤖 KHỞI CHẠY AI SEARCH SERVICE (PTIT LIBRARY KIOSK)
echo ========================================================
cd /d "%~dp0"

if exist venv\Scripts\python.exe (
    set PYTHON_EXEC=venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

echo [*] Dang chay FastAPI tai cong 8000...
%PYTHON_EXEC% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
