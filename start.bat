@echo off
chcp 65001 > nul
title Smart Library Kiosk - Trình Khởi Chạy Dự Án

echo ===============================================================================
echo     📚 HỆ THỐNG SMART LIBRARY KIOSK - HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG
echo ===============================================================================
echo.
echo  Đang chuẩn bị khởi chạy các dịch vụ...
echo.

:: 1. Kiểm tra Mosquitto nếu có docker
docker-compose up -d mosquitto 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] Đã khởi chạy MQTT Mosquitto Broker qua Docker (Port 1883).
) else (
    echo [!] Không chạy Docker Mosquitto. Hệ thống sẽ kết nối MQTT Broker theo file server/.env
)
echo.

:: 2. Khởi chạy Backend Server (Port 5000)
echo [1/3] Khởi chạy Backend Server (Node.js Express + Socket.IO + MQTT)...
start "Kiosk - 1. Backend Server (Port 5000)" cmd /k "npm run server:dev"

:: Chờ 2 giây
timeout /t 2 /nobreak > nul

:: 3. Khởi chạy Frontend React (Port 5173)
echo [2/3] Khởi chạy Frontend Kiosk & Admin (React + Vite)...
start "Kiosk - 2. Frontend Web App (Port 5173)" cmd /k "npm run client:dev"

:: Chờ 2 giây
timeout /t 2 /nobreak > nul

:: 4. Khởi chạy Virtual IoT Hardware Simulator
echo [3/3] Khởi chạy Virtual IoT Hardware Simulator...
start "Kiosk - 3. IoT Hardware Simulator (Interactive Console)" cmd /k "npm run sim:local"

echo.
echo ===============================================================================
echo  ✅ ĐÃ KHỞI CHẠY TOÀN BỘ HỆ THỐNG TRONG CÁC CỬA SỔ TERMINAL RIÊNG BIỆT!
echo ===============================================================================
echo.
echo  📌 Các địa chỉ truy cập trên trình duyệt:
echo     • Màn hình Kiosk tự phục vụ:    http://localhost:5173/kiosk
echo     • Trang Quản trị Thủ thư:       http://localhost:5173/admin
echo     • Web Bảng Điều Khiển Quẹt Thẻ:   http://localhost:8888
echo.
echo  💡 Hướng dẫn kiểm thử chức năng:
echo     1. Mở màn hình Kiosk trên trình duyệt (http://localhost:5173/kiosk).
echo     2. Tại cửa sổ "Kiosk - 3. IoT Hardware Simulator" (hoặc mở http://localhost:8888):
echo        - Bấm [1] : Quẹt thẻ Sinh viên (Nguyễn Văn A - E2801192) để Đăng nhập Kiosk.
echo        - Bấm [2] : Quẹt sách Quá hạn -> Test tính phạt và sinh mã VietQR thanh toán.
echo        - Bấm [4], [5] : Quẹt sách kho -> Test mượn sách mới theo giỏ hàng.
echo        - Bấm [3] : Quẹt sách đang mượn -> Test trả sách hoặc gia hạn.
echo.
echo ===============================================================================
pause
