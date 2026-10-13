# Tài Liệu REST API & WebSocket Events

## 1. REST API Endpoints (Base URL: `http://localhost:5000/api`)

### Độc giả (Readers)
* `GET /readers`: Lấy danh sách độc giả
* `GET /readers/by-rfid/:rfid`: Tra cứu độc giả theo mã RFID
* `POST /readers`: Tạo độc giả mới

### Sách (Books)
* `GET /books`: Danh sách sách trong kho
* `GET /books/by-rfid/:rfid`: Tra cứu thông tin sách theo RFID
* `POST /books`: Thêm sách mới

### Mượn / Trả (Loans)
* `POST /loans/borrow`: Mượn sách theo đợt `{ readerId, bookIds: [] }`
* `POST /loans/return`: Trả sách `{ bookRfid }`
* `GET /loans/history`: Lịch sử mượn trả toàn hệ thống

### Quản lý thiết bị (Devices)
* `GET /devices/kiosk_01/status`: Kiểm tra trạng thái Kiosk
* `POST /devices/kiosk_01/command`: Gửi lệnh còi/đèn từ xa

---

## 2. WebSocket / Socket.IO Events

| Tên Event | Chiều gửi | Dữ liệu kèm theo | Mô tả |
| :--- | :--- | :--- | :--- |
| `card:scanned` | Server ➔ Client | `{ uid, type, timestamp }` | Phát hiện có thẻ quẹt tại Kiosk |
| `kiosk:status` | Server ➔ Client | `{ status, rssi, uptime }` | Nhịp tim online/offline của Kiosk |
| `loan:updated` | Server ➔ Client | `{ loanId, status }` | Cập nhật khi mượn/trả thành công |

