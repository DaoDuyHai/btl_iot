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

:: 2. Khởi chạy AI Search Service (Python FastAPI - Port 8000)
echo [1/4] Khởi chạy AI Search Service (Python FastAPI - Port 8000)...
start "Kiosk - 1. AI Search Service (Port 8000)" cmd /k "npm run ai:dev"

:: Chờ 2 giây
timeout /t 2 /nobreak > nul

:: 3. Khởi chạy Backend Server (Port 5000)
echo [2/4] Khởi chạy Backend Server (Node.js Express + Socket.IO + MQTT)...
start "Kiosk - 2. Backend Server (Port 5000)" cmd /k "npm run server:dev"

:: Chờ 2 giây
timeout /t 2 /nobreak > nul

:: 4. Khởi chạy Frontend React (Port 5173)
echo [3/4] Khởi chạy Frontend Kiosk & Admin (React + Vite)...
start "Kiosk - 3. Frontend Web App (Port 5173)" cmd /k "npm run client:dev"

:: Chờ 2 giây
timeout /t 2 /nobreak > nul

:: 5. Khởi chạy Virtual IoT Hardware Simulator
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
echo  💡 Hướng dẫn kiểm thử:
echo     1. Mở màn hình Kiosk (http://localhost:5173/kiosk) -> Vào mục "Trợ lý AI Tìm Sách".
echo     2. Thử gõ câu hỏi cảm xúc: "Hôm nay tôi đang rất mệt, tôi muốn có cuốn sách giúp tôi thư giãn"
echo     3. Thử câu hỏi đời thường: "nay tôi tâm trạng không tốt, tôi cần 1 cuốn truyện hài"
echo     4. Thử câu hỏi chủ đề ngắn: "tiếng anh", "tiếng nhật", "lập trình python"
echo     5. Quẹt thẻ sinh viên và sách tại http://localhost:8888 để test mượn/trả/phạt.
echo.
echo ===============================================================================
pause
