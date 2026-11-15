@echo off
chcp 65001 > nul
echo ========================================================
echo   🤖 KHỞI CHẠY AI SEARCH SERVICE (PTIT LIBRARY KIOSK)
echo ========================================================
cd /d "%~dp0"

:: 1. Kiểm tra môi trường ảo venv, nếu chưa có thì tự động tạo & cài thư viện
if not exist venv\Scripts\activate.bat (
    echo [*] Chưa tìm thấy môi trường venv. Đang tự động tạo venv và cài đặt thư viện...
    python -m venv venv
    if %ERRORLEVEL% EQU 0 (
        call venv\Scripts\activate.bat
        echo [*] Đang cài đặt thư viện từ requirements.txt...
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    ) else (
        echo [!] Không thể tạo venv tự động. Đảm bảo máy tính đã cài Python 3.10+ và tick "Add Python to PATH".
    )
) else (
    echo [*] Kích hoạt Virtual Environment venv...
    call venv\Scripts\activate.bat
)

:: 2. Khởi chạy FastAPI
echo [*] Đang khởi chạy FastAPI tại http://127.0.0.1:8000...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Thử khởi chạy bằng uvicorn trong Scripts...
    venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload
)
pause
