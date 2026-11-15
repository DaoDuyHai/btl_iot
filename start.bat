@echo off
setlocal
title Smart Library Kiosk - Project Launcher

echo ===============================================================================
echo     HE THONG SMART LIBRARY KIOSK - HOC VIEN CONG NGHE BUU CHINH VIEN THONG
echo ===============================================================================
echo.
echo  Dang kiem tra moi truong va chuan bi khoi chay cac dich vu...
echo.

REM 1. Tu dong khoi tao file .env neu chua co
if not exist "server\.env" (
    echo [*] Chua co server/.env - Dang tu dong sao chep tu server/.env.example...
    copy "server\.env.example" "server\.env" > nul
)
if not exist "client\.env" (
    echo [*] Chua co client/.env - Dang tu dong sao chep tu client/.env.example...
    copy "client\.env.example" "client\.env" > nul
)

REM 2. Kiem tra node_modules, neu chua cai thi tu dong cai dat
if not exist "server\node_modules" (
    echo [*] Phat hien lan dau chay (chua cai dependencies). Dang tu dong cai dat...
    call npm run setup
) else (
    if not exist "client\node_modules" (
        echo [*] Dang cai dat thu vien cho Client...
        call npm --prefix client install
    )
)

REM 3. Khoi chay Mosquitto MQTT Broker va MongoDB qua Docker neu co Docker
docker-compose up -d mosquitto mongo 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Da khoi chay MQTT Mosquitto Broker (Port 1883) va MongoDB (Port 27017) qua Docker.
) else (
    echo [!] Khong dung Docker. He thong se ket noi MQTT Broker va MongoDB cuc bo theo file server/.env.
)
echo.

REM 4. Khoi chay AI Search Service (Python FastAPI - Port 8000)
echo [1/3] Khoi chay AI Search Service (Python FastAPI - Port 8000)...
start "Kiosk - 1. AI Search Service (Port 8000)" cmd /k "npm run ai:dev"

REM Cho 2 giay
timeout /t 2 /nobreak > nul

REM 5. Khoi chay Backend Server (Port 5000)
echo [2/3] Khoi chay Backend Server (Node.js Express + Socket.IO + MQTT)...
start "Kiosk - 2. Backend Server (Port 5000)" cmd /k "npm run server:dev"

REM Cho 2 giay
timeout /t 2 /nobreak > nul

REM 6. Khoi chay Frontend React (Port 5173)
echo [3/3] Khoi chay Frontend Kiosk and Admin (React + Vite)...
start "Kiosk - 3. Frontend Web App (Port 5173)" cmd /k "npm run client:dev"

echo.
echo ===============================================================================
echo  [OK] DA KHOI CHAY TOAN BO HE THONG TRONG CAC CUA SO TERMINAL RIENG BIET!
echo ===============================================================================
echo.
echo  Cac dia chi truy cap tren trinh duyet:
echo     - Man hinh Kiosk tu phuc vu:       http://localhost:5173/kiosk
echo     - Trang Quan tri Thu thu:          http://localhost:5173/admin
echo     - Giao dien Tro ly AI (FastAPI):   http://localhost:8000/docs
echo     - Kiem tra ket noi Backend:        http://localhost:5000/api/health
echo.
echo  Luu y lan dau chay:
echo     - Neu co so du lieu MongoDB moi tinh chua co sach/the, hay mo Terminal chay:
echo       npm run seed
echo.
echo ===============================================================================
pause
