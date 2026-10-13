# Kiến Trúc Hệ Thống & Luồng Dữ Liệu (Architecture & Data Flow)

## 1. Tổng quan kiến trúc
Hệ thống Kiosk Thư viện thông minh được thiết kế theo mô hình **Event-driven IoT Architecture** (Kiến trúc hướng sự kiện).

```
[ Thẻ RFID ]
     │ (13.56MHz RF)
     ▼
[ RC522 + ESP32 ] ──(MQTT QoS 1)──► [ Mosquitto Broker ]
                                            │
                                            ▼ (MQTT Client)
                                     [ Node.js Backend ] ◄──(Mongoose)──► [ MongoDB ]
                                            │
                                            ▼ (WebSocket / Socket.IO)
                                     [ React UI ]
                                   (Kiosk & Admin)
```

## 2. Máy trạng thái Kiosk (Finite State Machine - FSM)
1. **IDLE (Chờ):** Màn hình hiển thị "Mời bạn quẹt thẻ sinh viên".
2. **AUTHENTICATED (Đã xác thực):** Người dùng quẹt thẻ bạn đọc hợp lệ ➜ Hiển thị thông tin & mở giỏ mượn.
3. **BATCH_SCANNING (Quét liên tục):** Người dùng lướt từng cuốn sách qua RC522 ➜ ESP32 gửi UID ➜ Server kiểm tra & đẩy vào giỏ trên Web.
4. **CONFIRMING (Xác nhận):** Người dùng bấm "Mượn tất cả" ➜ Server tạo Transaction trong MongoDB ➜ ESP32 kêu bíp thành công.
5. **TIMEOUT (Hết giờ):** Nếu sau 45s không có tương tác, hệ thống tự động reset về IDLE.

