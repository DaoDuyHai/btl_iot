@echo off
chcp 65001 > nul
title Smart Library Kiosk - Trình Khởi Chạy Dự Án

echo ===============================================================================
echo     📚 HỆ THỐNG SMART LIBRARY KIOSK - HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG
echo ===============================================================================
echo.
echo  Đang kiểm tra môi trường và chuẩn bị khởi chạy các dịch vụ...
echo.

:: 1. Tự động khởi tạo file .env nếu chưa có
if not exist "server\.env" (
    echo [*] Chưa có server/.env -> Đang tự động sao chép từ server/.env.example...
    copy "server\.env.example" "server\.env" > nul
)
if not exist "client\.env" (
    echo [*] Chưa có client/.env -> Đang tự động sao chép từ client/.env.example...
    copy "client\.env.example" "client\.env" > nul
)

:: 2. Kiểm tra node_modules, nếu chưa cài thì tự động cài đặt
if not exist "server\node_modules" (
    echo [*] Phát hiện lần đầu chạy (chưa cài dependencies). Đang tự động cài đặt...
    call npm run setup
) else (
    if not exist "client\node_modules" (
        echo [*] Đang cài đặt thư viện cho Client...
        call npm --prefix client install
    )
    if not exist "tools\device-simulator\node_modules" (
        echo [*] Đang cài đặt thư viện cho IoT Simulator...
        call npm --prefix tools\device-simulator install
    )
)

:: 3. Khởi chạy Mosquitto MQTT Broker & MongoDB qua Docker nếu có Docker
docker-compose up -d mosquitto mongo 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] Đã khởi chạy MQTT Mosquitto Broker (Port 1883) và MongoDB (Port 27017) qua Docker.
) else (
    echo [!] Không dùng Docker. Hệ thống sẽ kết nối MQTT Broker & MongoDB cục bộ theo file server/.env.
)
echo.

:: 4. Khởi chạy AI Search Service (Python FastAPI - Port 8000)
echo [1/4] Khởi chạy AI Search Service (Python FastAPI - Port 8000)...
start "Kiosk - 1. AI Search Service (Port 8000)" cmd /k "npm run ai:dev"

:: Chờ 2 giây
timeout /t 2 /nobreak > nul

:: 5. Khởi chạy Backend Server (Port 5000)
echo [2/4] Khởi chạy Backend Server (Node.js Express + Socket.IO + MQTT)...
start "Kiosk - 2. Backend Server (Port 5000)" cmd /k "npm run server:dev"

:: Chờ 2 giây
timeout /t 2 /nobreak > nul

:: 6. Khởi chạy Frontend React (Port 5173)
echo [3/4] Khởi chạy Frontend Kiosk & Admin (React + Vite)...
start "Kiosk - 3. Frontend Web App (Port 5173)" cmd /k "npm run client:dev"

:: Chờ 2 giây
timeout /t 2 /nobreak > nul

:: 7. Khởi chạy Virtual IoT Hardware Simulator
echo [4/4] Khởi chạy Virtual IoT Hardware Simulator...
start "Kiosk - 4. IoT Hardware Simulator (Interactive Console)" cmd /k "npm run sim:local"

echo.
echo ===============================================================================
echo  ✅ ĐÃ KHỞI CHẠY TOÀN BỘ HỆ THỐNG TRONG CÁC CỬA SỔ TERMINAL RIÊNG BIỆT!
echo ===============================================================================
echo.
echo  📌 Các địa chỉ truy cập trên trình duyệt:
echo     • Màn hình Kiosk tự phục vụ:       http://localhost:5173/kiosk
echo     • Trang Quản trị Thủ thư:          http://localhost:5173/admin
echo     • Web Bảng Điều Khiển Quẹt Thẻ:    http://localhost:8888
echo     • Giao diện Trợ lý AI (FastAPI):   http://localhost:8000/docs
echo.
echo  💡 Lưu ý lần đầu chạy:
echo     - Nếu cơ sở dữ liệu MongoDB mới tinh chưa có sách/thẻ, hãy mở Terminal chạy:
echo       npm run seed
echo.
echo ===============================================================================
pause
