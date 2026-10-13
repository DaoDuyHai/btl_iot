# Sơ đồ đấu nối chân ESP32 (Pinout & Wiring)

## 1. Module RFID RC522 (Giao tiếp SPI)
| Chân RC522 | Chân ESP32 (GPIO) | Ghi chú |
| :--- | :--- | :--- |
| **VCC** | **3V3** (3.3V) | *Tuyệt đối không cấp 5V gây hỏng mạch* |
| **RST** | **GPIO 22** | Chân Reset |
| **GND** | **GND** | Chân Mass chung |
| **MISO** | **GPIO 19** | SPI Master In Slave Out |
| **MOSI** | **GPIO 23** | SPI Master Out Slave In |
| **SCK** | **GPIO 18** | SPI Clock |
| **SDA (SS)**| **GPIO 5** | SPI Slave Select / Chip Select |

---

## 2. Còi Buzzer & Đèn LED báo hiệu
| Linh kiện | Chân dương (+) | Chân âm (-) | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Còi Buzzer 5V** | **GPIO 25** | GND | Kêu bíp khi quét thẻ |
| **LED Xanh lá (OK)** | **GPIO 26** (qua trở 220Ω) | GND | Báo trạng thái thành công |
| **LED Đỏ (Error)** | **GPIO 27** (qua trở 220Ω) | GND | Báo lỗi hoặc thẻ không hợp lệ |

