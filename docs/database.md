# Thiết Kế Cơ Sở Dữ Liệu MongoDB (Database Schema)

## 1. Collection: `readers` (Bạn đọc / Sinh viên)
```json
{
  "_id": "ObjectId(...)",
  "studentId": "B21DCCN001",
  "name": "Nguyễn Văn A",
  "email": "vana@ptit.edu.vn",
  "rfidCard": "E2801192",
  "active": true,
  "createdAt": "2026-10-11T00:00:00Z"
}
```

## 2. Collection: `books` (Kho sách)
```json
{
  "_id": "ObjectId(...)",
  "isbn": "978-604-0-12345-6",
  "title": "Lập trình C++ Nâng Cao",
  "author": "GS. Phạm Văn B",
  "category": "CNTT",
  "rfidTag": "A1B2C3D4",
  "status": "available", // "available" | "borrowed" | "maintenance"
  "createdAt": "2026-10-11T00:00:00Z"
}
```

## 3. Collection: `loans` (Lịch sử mượn/trả)
```json
{
  "_id": "ObjectId(...)",
  "readerId": "ObjectId(readers)",
  "bookId": "ObjectId(books)",
  "borrowDate": "2026-10-11T00:00:00Z",
  "dueDate": "2026-10-25T00:00:00Z",
  "returnDate": null,
  "status": "borrowing", // "borrowing" | "returned" | "overdue"
  "fineAmount": 0,
  "isPaid": false
}
```

## 4. Collection: `device_logs` (Nhật ký thiết bị Kiosk)
```json
{
  "_id": "ObjectId(...)",
  "deviceId": "kiosk_01",
  "event": "scan", // "scan" | "heartbeat" | "offline" | "error"
  "payload": { "uid": "E2801192" },
  "rssi": -60,
  "timestamp": "2026-10-11T00:00:00Z"
}
```

