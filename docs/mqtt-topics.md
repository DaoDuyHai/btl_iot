# Quy ước Topic & Payload MQTT (MQTT Contract)

## Device ID mặc định: `kiosk_01`

### 1. ESP32 -> Server (Events)

#### `kiosk/kiosk_01/scan`
ESP32 gửi lên khi phát hiện thẻ RFID.
```json
{
  "uid": "E2801192",
  "type": "rfid",
  "timestamp": 1728639000
}
```

#### `kiosk/kiosk_01/status` (Heartbeat - mỗi 30s)
```json
{
  "status": "online",
  "rssi": -62,
  "uptime": 3600
}
```

#### `kiosk/kiosk_01/status` (LWT - Last Will and Testament)
Broker tự động bắn khi ESP32 mất kết nối đột ngột:
```json
{
  "status": "offline"
}
```

---

### 2. Server -> ESP32 (Commands)

#### `kiosk/kiosk_01/command`
* **Phản hồi thành công (Beep 1 lần + LED Xanh):**
```json
{
  "action": "feedback",
  "status": "success"
}
```

* **Phản hồi lỗi (Beep 2 lần + LED Đỏ):**
```json
{
  "action": "feedback",
  "status": "error"
}
```

* **Khởi động lại ESP32 từ xa:**
```json
{
  "action": "reboot"
}
```

