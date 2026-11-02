# PHÂN TÍCH CẤU TRÚC VÀ BỐ CỤC BÁO CÁO BÀI TẬP LỚN IoT

## Đề tài: Xây dựng nền tảng IoT quản lý vườn thông minh tích hợp trợ lý AI Synthia

Tài liệu này phân tích cấu trúc, bố cục chi tiết và nội dung của báo cáo mẫu (chuẩn của Học viện Công nghệ Bưu chính Viễn thông - PTIT) để làm prompt mẫu khi yêu cầu AI viết báo cáo cho đề tài tương tự.

---

## I. CẤU TRÚC TỔNG QUAN CỦA BÁO CÁO

Báo cáo được chia thành 5 chương chính, đi từ lý thuyết tổng quan, phân tích thiết kế, triển khai thực tế đến đánh giá kết quả, kèm theo phần mở đầu, kết luận, tài liệu tham khảo và phụ lục.

### 1. Trang bìa & Thông tin hành chính

- **Đơn vị chủ quản:** Học viện Công nghệ Bưu chính Viễn thông - Khoa Công nghệ Thông tin I.
- **Tên môn học:** Internet of Things (IoT) và ứng dụng.
- **Tên đề tài:** Xây dựng nền tảng IoT quản lý vườn thông minh tích hợp trợ lý AI Synthia.
- **Thông tin nhóm:** Giảng viên hướng dẫn, Nhóm, Lớp, Danh sách sinh viên (Họ tên, Mã sinh viên), Thời gian (Năm).

### 2. Các phần mở đầu

- **Lời cảm ơn:** Tri ân giảng viên, nêu bật ý nghĩa thực tiễn của đề tài và tiếp thu góp ý.
- **Mục lục:** Hệ thống tiêu đề các chương, mục rõ ràng.
- **Danh mục từ viết tắt:** Bảng tra cứu các thuật ngữ chuyên ngành (ADC, AI, API, MQTT, REST, WebSocket, v.v.).
- **Danh mục hình vẽ:** Liệt kê sơ đồ, biểu đồ và hình ảnh thực tế.
- **Danh mục bảng biểu:** Liệt kê các bảng thông số kỹ thuật, cấu trúc CSDL, API.

---

## II. CHI TIẾT NỘI DUNG TỪNG CHƯƠNG (DÙNG LÀM PROMPT CHO AI)

### LỜI MỞ ĐẦU

- **Bối cảnh:** Vấn đề canh tác truyền thống (phụ thuộc kinh nghiệm, dễ thừa/thiếu nước, khó quản lý từ xa).
- **Giải pháp:** Ứng dụng IoT (ESP32 + Cảm biến + MQTT + Server + Web) kết hợp Mô hình ngôn ngữ lớn (LLM/Gemini) và Trợ lý ảo AI.
- **Tổ chức báo cáo:** Tóm tắt ngắn gọn nội dung 5 chương chính.

### CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI

- **1.1. Đặt vấn đề:** Phân tích nhu cầu thực tế của việc quản lý vườn thông minh.
- **1.2. Mục tiêu của đề tài:** Các mục tiêu cụ thể từ phần cứng, truyền thông, lưu trữ, giao diện đến tích hợp AI.
- **1.3. Phạm vi và đối tượng nghiên cứu:**
  - _Đối tượng nghiên cứu:_ ESP32, cảm biến, MQTT, Spring Boot, Redis, MySQL, FastAPI, Gemini.
  - _Phạm vi đề tài:_ Quy mô 1 nút thiết bị mô phỏng, 1 máy bơm, phục vụ chủ vườn.
- **1.4. Phương pháp thực hiện:** Nghiên cứu tài liệu, phân tích - thiết kế hướng sự kiện, phát triển lặp/tăng dần, thực nghiệm và quản lý mã nguồn bằng Git.
- **1.5. Kết quả dự kiến:** Mô hình phần cứng, nền tảng phần mềm Docker, tài liệu API, báo cáo.

### CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG

- **2.1. Tổng quan về IoT:** Khái niệm, kiến trúc 4 lớp (Cảm nhận, Mạng, Xử lý/Trung gian, Ứng dụng), ứng dụng trong nông nghiệp thông minh.
- **2.2. Vi điều khiển ESP32:** Thông số kỹ thuật, sơ đồ chân, lưu ý khối ADC.
- **2.3. Các cảm biến và thiết bị chấp hành:**
  - DHT11 (Nhiệt độ, độ ẩm không khí).
  - BH1750 (Ánh sáng - Lux).
  - Cảm biến độ ẩm đất (Analog).
  - Module relay và máy bơm nước mini DC.
- **2.4. Giao thức MQTT:** Khái niệm, mô hình Pub/Sub, Topic, QoS (0, 1, 2), Retained messages, LWT, so sánh MQTT và HTTP, Eclipse Mosquitto Broker.
- **2.5. Nền tảng Java Spring Boot:** Spring Boot, Spring Integration MQTT, Spring Data JPA & Flyway.
- **2.6. WebSocket và STOMP:** Giao thức thời gian thực, giao tiếp song công.
- **2.7. Cơ sở dữ liệu:** MySQL (bền vững) và Redis (bộ nhớ đệm trạng thái thời gian thực).
- **2.8. Trí tuệ nhân tạo:** Google Gemini, kỹ thuật Prompting, Tool Calling, FastAPI framework.
- **2.9. Dịch vụ thời tiết:** OpenWeatherMap API.
- **2.10. Container hóa:** Docker và Docker Compose.

### CHƯƠNG 3. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

- **3.1. Phân tích yêu cầu:**
  - Tác nhân (Người dùng, ESP32, Bộ lập lịch, Dịch vụ ngoài).
  - Yêu cầu chức năng (Thu thập dữ liệu, giám sát, điều khiển bơm, tưới theo ngưỡng, lịch sử, AI chat, tự động hóa, thông báo email, Swagger UI).
  - Yêu cầu phi chức năng (Thời gian thực, an toàn thiết bị, tin cậy, hiệu năng, bảo mật, mở rộng).
  - Biểu đồ Use Case.
- **3.2. Thiết kế kiến trúc tổng thể:** Mô hình hướng sự kiện kết hợp microservice.
- **3.3. Thiết kế phần cứng:** Danh sách linh kiện, sơ đồ khối, sơ đồ nguyên lý kết nối chân.
- **3.4. Thiết kế giao tiếp MQTT:** Cấu trúc Topic chuẩn (`smartgarden/device/{uid}/{type}`), định dạng thông điệp JSON, bảng lệnh điều khiển.
- **3.5. Thiết kế cơ sở dữ liệu:**
  - MySQL (ERD, cấu trúc bảng `devices`, `telemetry_logs`, `threshold_settings`).
  - Redis (Cấu trúc khóa lưu trữ trạng thái `device:state:{uid}`).
- **3.6. Thiết kế REST API:** Bảng liệt kê các API endpoints theo chuẩn tiền tố `/api/v1`.
- **3.7. Thiết kế các luồng xử lý:**
  - Luồng khởi động & kết nối thiết bị.
  - Luồng thu thập & xử lý dữ liệu cảm biến.
  - Luồng điều khiển máy bơm thủ công.
  - Luồng tưới tự động theo ngưỡng (kèm lưu đồ thuật toán).
  - Luồng trò chuyện với trợ lý AI.
  - Luồng tự động hóa chủ động bằng AI.
- **3.8. Thiết kế dịch vụ AI:** Cấu trúc yêu cầu/phản hồi và các định dạng dòng NDJSON.

### CHƯƠNG 4. TRIỂN KHAI HỆ THỐNG

- **4.1. Môi trường và công cụ phát triển:** Bảng tổng hợp công nghệ phần cứng & phần mềm.
- **4.2. Triển khai firmware ESP32:** Thư viện, cấu trúc chương trình (setup/loop không chặn), đọc và chuẩn hóa dữ liệu cảm biến, xử lý lệnh, **cơ chế an toàn tự tắt máy bơm 2 lớp**, tự động kết nối lại.
- **4.3. Backend Spring Boot:** Cấu trúc mã nguồn (Package structure), cấu hình MQTT Integration, xử lý thông điệp, điều khiển bơm, tưới tự động, tích hợp AI, thông báo WebSocket và Email.
- **4.4. Dịch vụ AI (Python/FastAPI):** Xây dựng System Prompt, phân tích phản hồi mô hình, trả lời dạng stream (StreamingResponse).
- **4.5. Giao diện web:** Các trang HTML, Tailwind CSS, tích hợp Chart.js và SockJS/Stomp.js.
- **4.6. Đóng gói Docker Compose:** Cấu hình multi-container (Mosquitto, MySQL, Redis, FastAPI, Spring Boot) và biến môi trường (`.env`).

### CHƯƠNG 5. KẾT QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ

- **5.1. Mô hình phần cứng:** Hình ảnh thực tế và nhật ký Serial Monitor.
- **5.2. Kết quả giao diện:** Trang chủ, trang điều khiển, dashboard lịch sử, AI Chat Synthia, Swagger UI, dữ liệu lưu trong MySQL & Redis.
- **5.3. Kiểm thử hệ thống:** Kịch bản kiểm thử chức năng (TC01-TC13) và kiểm thử trợ lý AI (AI01-AI08).
- **5.4. Đánh giá hệ thống:** Ưu điểm (kiến trúc, real-time, an toàn bơm, AI thông minh) và Hạn chế (chưa phân quyền, chưa mã hóa TLS, phụ thuộc mạng).

### PHẦN KẾT LUẬN & TÀI LIỆU THAM KHẢO

- **Kết luận:** Tổng kết các kết quả đạt được so với mục tiêu ban đầu.
- **Hướng phát triển:** Bảo mật (OAuth2/JWT, TLS), mở rộng cảm biến/thiết bị, tối ưu năng lượng, ứng dụng di động.
- **Tài liệu tham khảo:** Danh mục chuẩn IEEE/APA.
- **Phụ lục:** Hướng dẫn cài đặt chi tiết (`.env`, Docker Compose, nạp firmware Arduino IDE).

---
