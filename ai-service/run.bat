@echo off
setlocal
title PTIT Library Kiosk - AI Search Service

echo ========================================================
echo   AI SEARCH SERVICE - PTIT LIBRARY KIOSK (FastAPI)
echo ========================================================
echo.

cd /d "%~dp0"

REM 1. Kich hoat Virtual Environment neu ton tai
if exist "venv\Scripts\activate.bat" (
    echo [*] Dang kich hoat virtual environment venv...
    call "venv\Scripts\activate.bat"
) else (
    echo [*] Su dung Python he thong...
)

echo [*] Khoi chay FastAPI tai http://127.0.0.1:8000...
echo [*] Swagger API Docs: http://127.0.0.1:8000/docs
echo.

REM 2. Chay FastAPI bang python
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
if %ERRORLEVEL% NEQ 0 (
    if exist "venv\Scripts\python.exe" (
        "venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    )
)
if %ERRORLEVEL% NEQ 0 (
    py -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
)

echo.
echo [!] AI Service da dung.
pause
