# 🚀 HƯỚNG DẪN ĐẨY GITHUB & CÀI ĐẶT CHẠY DỰ ÁN (TỪ FILE ZIP / CLONE)

Tài liệu này hướng dẫn chi tiết cách đưa dự án lên GitHub an toàn và cách tải file `.zip` (hoặc `git clone`) về bất kỳ máy tính nào khác để chạy ngay lập tức.

---


```

---

## PHẦN 2: CÁCH TẢI FILE ZIP VỀ MÁY MỚI VÀ CHẠY NGAY

Khi tải file `.zip` từ GitHub về máy tính mới (hoặc `git clone`), thư mục sẽ chưa có `node_modules` và file `.env`. Bạn chỉ cần thực hiện **3 bước** dưới đây:

### Yêu cầu cài đặt trước trên máy:
1. **Node.js** (Phiên bản v18 trở lên) - Tải tại: [https://nodejs.org](https://nodejs.org)
2. **MQTT Broker (Mosquitto)** *(Tùy chọn nếu muốn test kết nối MQTT thực tế, hoặc chạy qua Docker)*

---

### Bước 1: Cài đặt tự động toàn bộ thư viện & tạo file `.env`
Giải nén file `.zip`, mở Terminal (PowerShell hoặc CMD) ngay tại thư mục gốc `library-kiosk` và chạy **1 lệnh duy nhất**:

```bash
npm run setup
```

> **Lệnh `npm run setup` sẽ tự động làm hết cho bạn:**
> * Cài đặt `node_modules` cho Backend (`server`).
> * Cài đặt `node_modules` cho Giao diện Web (`client`).
> * Cài đặt `node_modules` cho Bộ giả lập phần cứng (`tools/device-simulator`).
> * Tự động tạo file `server/.env` và `client/.env` từ file mẫu `.env.example`.

---

### Bước 2: Cấu hình Database & Email trong `server/.env`
Mở file `server/.env` vừa được tạo ra và kiểm tra:

```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/library_kiosk
MQTT_BROKER_URL=mqtt://localhost:1883
KIOSK_DEVICE_ID=kiosk_01
CLIENT_URL=http://localhost:5173
FINE_PER_DAY_VND=5000
BANK_BIN=970422
BANK_ACCOUNT=000124135246

# Cấu hình gửi Gmail biên lai điện tử (Tùy chọn)
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=xxxx xxxx xxxx xxxx
```

* **Cách 1 (Dùng MongoDB cài trên máy - Local):** Giữ nguyên `MONGODB_URI=mongodb://localhost:27017/library_kiosk`.
* **Cách 2 (Dùng MongoDB Atlas trên đám mây):** Thay `MONGODB_URI` bằng đường dẫn `mongodb+srv://...` của bạn.
* **Gửi biên lai qua Gmail thật:** Điền `EMAIL_USER` (địa chỉ Gmail) và `EMAIL_PASS` (Mật khẩu ứng dụng Google 16 ký tự). Nếu để trống, hệ thống vẫn chạy bình thường và tạo link xem biên lai giả lập trên cửa sổ Terminal của Server.

**Khởi tạo dữ liệu mẫu (Sách, Bạn đọc PTIT, Phiếu mượn quá hạn/còn hạn):**
```bash
npm run seed
```

---

### Bước 3: Khởi chạy hệ thống (Mở 3 cửa sổ Terminal tại thư mục gốc `library-kiosk`)

* **Terminal 1 — Chạy Backend Server (Cổng 5000):**
  ```bash
  npm run server:dev
  ```

* **Terminal 2 — Chạy Giao diện Web Kiosk & Admin (Cổng 5173):**
  ```bash
  npm run client:dev
  ```
  * Giao diện **Kiosk Tự Phục Vụ**: [http://localhost:5173/kiosk](http://localhost:5173/kiosk)
  * Giao diện **Quản Trị Thủ Thư (Admin)**: [http://localhost:5173/admin](http://localhost:5173/admin)

* **Terminal 3 — Chạy Bộ Giả Lập Thiết Bị Phần Cứng ESP32 & Đầu Đọc RFID:**
  ```bash
  npm run sim
  ```

---

## PHẦN 3: KỊCH BẢN DEMO & THỬ NGHIỆM TRÊN SIMULATOR

Tại cửa sổ **Terminal 3 (`npm run sim`)** hoặc **Thanh công cụ Demo góc dưới màn hình Kiosk**, bạn có thể bấm phím để giả lập quẹt thẻ RFID:

| Phím / Nút Demo | Thẻ RFID được quét | Kịch bản kiểm thử |
| :---: | :--- | :--- |
| **`[1]`** | `E2801192` — **Nguyễn Văn A** | Đăng nhập bạn đọc chính (Có 1 sách quá hạn 3 ngày & 1 sách còn hạn). |
| **`[2]`** | `A1B2C3D4` — **Lập Trình Hệ Thống Nhúng IoT** | Sách đang mượn **QUÁ HẠN 3 NGÀY**. Khi quét ở mục **Trả sách**, hệ thống khóa nút Hoàn thành, yêu cầu quét **VietQR nộp phạt 15.000đ** trước khi hoàn tất. |
| **`[3]`** | `D4C3B2A1` — **Thiết Kế Mạng Viễn Thông Thế Hệ Mới** | Sách đang mượn **CÒN HẠN**. Dùng để test **Trả sách đúng hạn (0đ)** hoặc **Gia hạn thêm 14 ngày**. |
| **`[4]`, `[5]`, `[6]`** | `B3C4D5E6`, `C5D6E7F8`, `E9F0A1B2` | Sách có sẵn trong kho. Dùng ở mục **Mượn sách** để quét nhiều cuốn vào giỏ và xác nhận mượn 1 lần. |
| **`[7]`** | `A8B9C0D1` — **Trần Thị Mai** | Thẻ bạn đọc thứ 2. Nếu quẹt khi Nguyễn Văn A chưa đăng xuất, Kiosk sẽ **chặn cảnh báo bảo mật phiên**. |
| **`[8]`** | `99999999` — **Thẻ lạ chưa đăng ký** | Kiosk báo lỗi từ chối, còi Buzzer kêu 3 tiếng bíp và nháy đèn LED Đỏ. |

---

## PHẦN 4: LƯU Ý CÁC TÍNH NĂNG BẢO VỆ ĐÃ TÍCH HỢP

1. **Không tự ý nhảy trang khi quẹt thẻ ở Trang chủ:** Quẹt thẻ sinh viên ở màn hình chính chỉ đăng nhập và chào bạn đọc, giữ nguyên ở Trang chủ để bạn đọc chủ động chọn mục (*Mượn / Trả / Gia hạn / Thông tin cá nhân*).
2. **Chống ghi đè phiên (Anti-Session Hijacking):** Khi Độc giả A đang thao tác, nếu Độc giả B vô tình quẹt thẻ vào, hệ thống sẽ từ chối và giữ nguyên phiên của Độc giả A cho đến khi bấm **Kết thúc phiên / Hoàn thành**.
3. **Gộp chung 1 biên lai Email duy nhất cho mỗi phiên trả sách:** Dù trả cùng lúc nhiều cuốn (cả sách quá hạn đã nộp phạt lẫn sách đúng hạn), hệ thống chỉ gửi **1 email biên lai tổng hợp duy nhất** khi bấm **Hoàn thành trả sách**.

