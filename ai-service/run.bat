@echo off
setlocal
title PTIT Library Kiosk - AI Search Service

echo ========================================================
echo   AI SEARCH SERVICE - PTIT LIBRARY KIOSK (FastAPI)
echo ========================================================
echo.

cd /d "%~dp0"

REM 1. Uu tien dung python trong venv neu ton tai
set "PYTHON_EXE=python"
if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
    echo [*] Su dung moi truong ao venv: venv\Scripts\python.exe
) else (
    echo [*] Su dung Python he thong...
)

echo [*] Khoi chay FastAPI tai http://127.0.0.1:8000...
echo [*] Swagger API Docs: http://127.0.0.1:8000/docs
echo.

REM 2. Chay FastAPI uvicorn
"%PYTHON_EXE%" -m uvicorn main:app --host 0.0.0.0 --port 8000
if %ERRORLEVEL% NEQ 0 (
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
)
if %ERRORLEVEL% NEQ 0 (
    py -m uvicorn main:app --host 0.0.0.0 --port 8000
)

echo.
echo [!] AI Service da dung.
pause
