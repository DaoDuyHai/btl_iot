@echo off
chcp 65001 > nul
echo ========================================================
echo   🤖 KHỞI CHẠY AI SEARCH SERVICE (PTIT LIBRARY KIOSK)
echo ========================================================
cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    echo [*] Kich hoat Virtual Environment venv...
    call venv\Scripts\activate.bat
)

echo [*] Dang khoi chay FastAPI tai http://127.0.0.1:8000...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Thu khoi chay bang uvicorn trong Scripts...
    venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload
)
pause
