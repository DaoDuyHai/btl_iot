# 📚 HỆ THỐNG SMART LIBRARY KIOSK - TRẠM MƯỢN TRẢ SÁCH TỰ PHỤC VỤ IOT & TRỢ LÝ THỦ THƯ AI (NOVA)

[![CI Pipeline](https://github.com/DaoDuyHai/btl_iot/actions/workflows/ci.yml/badge.svg)](https://github.com/DaoDuyHai/btl_iot/actions/workflows/ci.yml)
[![Architecture](https://img.shields.io/badge/Architecture-IoT_Level_3-blue.svg)](<>)
[![Hardware](https://img.shields.io/badge/Hardware-ESP32_+_RC522-red.svg)](<>)
[![Backend](https://img.shields.io/badge/Backend-Node.js_20_+_Express-green.svg)](<>)
[![Frontend](https://img.shields.io/badge/Frontend-React_18_+_Vite-61dafb.svg)](<>)
[![AI Service](https://img.shields.io/badge/AI_Engine-FastAPI_+_Hybrid_E5_+_BM25-yellow.svg)](<>)
[![Test Suite](https://img.shields.io/badge/Vitest-55_Passed_100%25-brightgreen.svg)](<>)
[![Code Quality](https://img.shields.io/badge/Code_Quality-ESLint_0_Errors-blueviolet.svg)](<>)

> **Đề tài tốt nghiệp / Đồ án IoT:** Nghiên cứu, thiết kế và chế tạo Trạm Kiosk Mượn/Trả Sách Tự Phục Vụ Thông Minh ứng dụng công nghệ **IoT (ESP32, RFID RC522, MQTT, WebSocket)** kết hợp **Trợ Lý Thủ Thư AI Rảnh Tay "Nova" (Hands-Free Voice Wake Word, Hybrid Multilingual-E5 + BM25Okapi, Sơ đồ chỉ đường vị trí kệ sách)**.

---

## 🖥️ CÁC ĐỊA CHỈ TRUY CẬP HỆ THỐNG (LOCALHOST)

- 🖥️ **Màn hình Kiosk Tự Phục Vụ:** [http://localhost:5173/kiosk](http://localhost:5173/kiosk)
- 🛡️ **Cổng Quản Trị Thủ Thư (Admin Portal):** [http://localhost:5173/admin](http://localhost:5173/admin)
- ⚙️ **Hạ tầng Backend API (Express + Socket.IO):** [http://localhost:5000/api/health](http://localhost:5000/api/health)
- 🤖 **Tài liệu API Trợ lý AI Nova (FastAPI Swagger Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🏛️ 1. SƠ ĐỒ KIẾN TRÚC TỔNG THỂ HỆ THỐNG (SYSTEM ARCHITECTURE - IOT LEVEL 3)

Hệ thống được thiết kế theo tiêu chuẩn quốc tế **IoT Level 3** (_Bahga & Madisetti_): Nút biên phần cứng (ESP32) chỉ đảm nhiệm việc thu thập mã thẻ RFID và phản hồi còi/LED; toàn bộ dữ liệu, phân tích nghiệp vụ, dịch vụ trí tuệ nhân tạo và giao diện hiển thị được xử lý tập trung trên nền tảng máy chủ.

```mermaid
flowchart TD
    %% Tầng 1: Phần cứng
    subgraph S1 ["1. TẦNG THIẾT BỊ PHẦN CỨNG (IoT Edge Layer)"]
        direction TB
        ESP32["Vi điều khiển ESP32 DevKit V1<br/>(WiFi 2.4GHz • C++ Firmware PlatformIO)"]
        RC522["Đầu đọc RFID RC522<br/>(13.56MHz Mifare • Giao tiếp SPI)"]
        Buzzer["Còi Buzzer 5V<br/>(Âm thanh phản hồi Bíp)"]
        LED["Cặp LED Kép Trạng Thái<br/>(Xanh: Thành công / Đỏ: Lỗi)"]
        Cards["Thẻ Bạn Đọc & Nhãn RFID Dán Sách<br/>(Mifare 1K / NTAG213)"]

        Cards -.->|"Quẹt thẻ chạm (Touch)"| RC522
        RC522 <==>|"Chuẩn SPI (MISO, MOSI, SCK, CS)"| ESP32
        ESP32 ==>|"GPIO 25 (PWM Active)"| Buzzer
        ESP32 ==>|"GPIO 26 / 27"| LED
    end

    %% Tầng 2: Giao thức truyền thông
    subgraph S2 ["2. TẦNG TRUYỀN THÔNG & MẠNG (Transport & Broker Layer)"]
        direction TB
        Mosquitto["Eclipse Mosquitto MQTT Broker (Port 1883)<br/>• Topic: kiosk/{id}/scan<br/>• Topic: kiosk/{id}/status (LWT/Heartbeat)<br/>• Topic: kiosk/{id}/command"]
    end

    %% Tầng 3: Máy chủ Backend & Cơ sở dữ liệu
    subgraph S3 ["3. TẦNG MÁY CHỦ TRUNG TÂM (Backend & Data Layer)"]
        direction TB
        NodeServer["Node.js Express Application Server (Port 5000)<br/>• MQTT Client Handler & Publisher<br/>• Socket.IO Realtime Gateway<br/>• RESTful Business API Engine"]
        CatalogEngine["In-Memory Semantic Precision Engine<br/>(3.000 đầu sách thực tế • BM25Okapi • 0.01ms Fallback)"]
        MongoDB[("Cơ sở dữ liệu MongoDB (Port 27017)<br/>• Readers • Books • Loans • DeviceLogs • AuditLogs")]
        EmailService["Dịch vụ Email Tự Động (Nodemailer)<br/>(Gửi biên lai mượn/trả tức thì tới Gmail sinh viên)"]

        NodeServer <-->|"Mongoose ODM"| MongoDB
        NodeServer <--> CatalogEngine
        NodeServer ==>|"SMTP TLS"| EmailService
    end

    %% Tầng 4: Trợ lý Thủ thư AI
    subgraph S4 ["4. TẦNG TRỢ LÝ THỦ THƯ AI NOVA (AI Intelligence Layer)"]
        direction TB
        FastAPI["AI Service Python FastAPI (Port 8000)<br/>• Semantic Engine (Multilingual-E5-Small)<br/>• Lexical Engine (BM25Okapi Ranking)<br/>• Query Understanding & Context Router"]
        ShelfLocator["Module Định Vị Kệ Sách Thực Tế<br/>• Bản đồ Tầng 1, 2, 3 • Kệ A, B, C, D"]

        FastAPI <--> ShelfLocator
    end

    %% Tầng 5: Giao diện người dùng
    subgraph S5 ["5. TẦNG ỨNG DỤNG & GIAO DIỆN (Frontend Presentation Layer)"]
        direction TB
        KioskUI["Màn hình Kiosk Tự Phục Vụ (/kiosk)<br/>• Xác thực thẻ sinh viên<br/>• Mượn sách theo đợt (Batch Borrow)<br/>• Trả sách & Nộp phạt VietQR động<br/>• Trò chuyện giọng nói rảnh tay: 'Nova'"]
        AdminUI["Cổng Quản Trị Thủ Thư (/admin)<br/>• Giám sát Kiosk Realtime (LWT, RSSI, Uptime)<br/>• Quản lý Sách, Bạn đọc, Kiểm toán sách mất/hỏng<br/>• Miễn phạt, Xuất báo cáo thống kê"]
    end

    %% Liên kết giữa các tầng
    ESP32 <===>|"Giao thức MQTT (WiFi 2.4GHz)"| Mosquitto
    Mosquitto <===>|"MQTT Subscriber & Publisher"| NodeServer
    NodeServer <===>|"WebSocket (Socket.IO Realtime 0ms)"| KioskUI
    NodeServer <===>|"WebSocket & HTTP REST API"| AdminUI
    NodeServer <===>|"HTTP Proxy / Fallback Timeout 3.5s"| FastAPI

    %% Phối màu trực quan
    classDef edgeStyle fill:#eff6ff,stroke:#1d4ed8,stroke-width:2px,color:#1e3a8a;
    classDef brokerStyle fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e;
    classDef serverStyle fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#14532d;
    classDef aiStyle fill:#fdf4ff,stroke:#a21caf,stroke-width:2px,color:#701a75;
    classDef uiStyle fill:#fff1f2,stroke:#be123c,stroke-width:2px,color:#881337;

    class S1,ESP32,RC522,Buzzer,LED,Cards edgeStyle;
    class S2,Mosquitto brokerStyle;
    class S3,NodeServer,CatalogEngine,MongoDB,EmailService serverStyle;
    class S4,FastAPI,ShelfLocator aiStyle;
    class S5,KioskUI,AdminUI uiStyle;
```

---

## ⚡ 2. SƠ ĐỒ PHẦN CỨNG & ĐẤU NỐI CHÂN MẠCH (HARDWARE & PINOUT WIRING)

Hệ thống sử dụng vi điều khiển **ESP32 NodeMCU DevKit V1 (30 chân)** kết nối module đầu đọc **RFID RC522 (13.56 MHz)** thông qua giao tiếp chuẩn **SPI (Serial Peripheral Interface)** với tốc độ lấy mẫu cao và độ ổn định tuyệt đối:

```mermaid
flowchart LR
    subgraph ESP ["VI ĐIỀU KHIỂN TRUNG TÂM ESP32 DEVKIT V1"]
        direction TB
        P3V3["3V3 (Nguồn 3.3V)"]
        GND["GND (Nối đất)"]
        D5["GPIO 5 (SS / SDA)"]
        D18["GPIO 18 (SCK - Clock)"]
        D23["GPIO 23 (MOSI)"]
        D19["GPIO 19 (MISO)"]
        D22["GPIO 22 (RST - Reset)"]
        D25["GPIO 25 (Buzzer PWM)"]
        D26["GPIO 26 (LED Xanh - OK)"]
        D27["GPIO 27 (LED Đỏ - Lỗi)"]
    end

    subgraph RFID ["MODULE RFID RC522 (SPI)"]
        direction TB
        R_3V3["3.3V (Tuyệt đối không cấp 5V)"]
        R_GND["GND"]
        R_SDA["SDA / SS"]
        R_SCK["SCK"]
        R_MOSI["MOSI"]
        R_MISO["MISO"]
        R_RST["RST"]
    end

    subgraph OUTPUTS ["THIẾT BỊ PHẢN HỒI THỜI GIAN THỰC"]
        direction TB
        BZ["Còi Chủ Động Active Buzzer 5V"]
        LED_G["Đèn LED Xanh Lá + Trở 220Ω (OK)"]
        LED_R["Đèn LED Đỏ + Trở 220Ω (Error)"]
    end

    %% Kết nối SPI RFID
    P3V3 <--->|"Dây Đỏ"| R_3V3
    GND <--->|"Dây Đen"| R_GND
    D5 <--->|"Dây Cam (Chip Select)"| R_SDA
    D18 <--->|"Dây Vàng (SPI Clock)"| R_SCK
    D23 <--->|"Dây Lục (Master Out)"| R_MOSI
    D19 <--->|"Dây Lam (Master In)"| R_MISO
    D22 <--->|"Dây Tím (Reset)"| R_RST

    %% Kết nối phản hồi
    D25 ==>|"Tín hiệu kích còi"| BZ
    D26 ==>|"Báo hợp lệ"| LED_G
    D27 ==>|"Báo lỗi / Cảnh báo"| LED_R

    classDef espBox fill:#f8fafc,stroke:#334155,stroke-width:2px,color:#0f172a;
    classDef rfidBox fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e40af;
    classDef outBox fill:#fef2f2,stroke:#dc2626,stroke-width:2px,color:#991b1b;

    class ESP,P3V3,GND,D5,D18,D23,D19,D22,D25,D26,D27 espBox;
    class RFID,R_3V3,R_GND,R_SDA,R_SCK,R_MOSI,R_MISO,R_RST rfidBox;
    class OUTPUTS,BZ,LED_G,LED_R outBox;
```

### 📋 Bảng Dự Toán Kinh Phí Linh Kiện Phần Cứng Thực Tế (BOM):

|  STT   | Tên Linh Kiện               | Thông Số / Giao Tiếp                | Số Lượng | Đơn Giá Ước Tính | Vai Trò Trong Đề Tài                           |
| :----: | :-------------------------- | :---------------------------------- | :------: | :--------------: | :--------------------------------------------- |
| **1**  | **ESP32 NodeMCU DevKit V1** | 30 chân, 2.4GHz Wi-Fi + BLE         |    1     |   ~65.000 VNĐ    | Nút biên vi điều khiển trung tâm IoT           |
| **2**  | **Module RFID RC522**       | 13.56 MHz, chuẩn giao tiếp SPI      |    1     |   ~28.000 VNĐ    | Đọc mã định danh UID thẻ sinh viên và thẻ sách |
| **3**  | **Thẻ & Nhãn Dán RFID**     | Mifare 1K (Thẻ trắng / Sticker dán) |    5     |   ~15.000 VNĐ    | Gán mã định danh cho bạn đọc & bìa sách        |
| **4**  | **Còi Active Buzzer 5V**    | Tần số âm thanh 1.8kHz              |    1     |    ~3.000 VNĐ    | Bíp xác nhận thao tác tức thì cho bạn đọc      |
| **5**  | **LED Kép + Trở 220Ω**      | LED 5mm Xanh lá & Đỏ                |   2 bộ   |    ~2.000 VNĐ    | Báo thị trạng thái hợp lệ hoặc từ chối         |
| **6**  | **Breadboard & Dây Jumper** | Dây cắm đực - cái chống nhiễu       |   1 bộ   |   ~25.000 VNĐ    | Đấu nối linh kiện an toàn, thẩm mỹ             |
| **--** | **TỔNG KINH PHÍ PHẦN CỨNG** |                                     |          | **~138.000 VNĐ** | **Chi phí siêu tiết kiệm, tính khả thi cao**   |

---

## 🎯 3. SƠ ĐỒ USE CASE HỆ THỐNG (USE CASE DIAGRAM)

```mermaid
flowchart TD
    %% Actors
    Reader(("👤 BẠN ĐỌC<br/>(Sinh Viên PTIT)"))
    Admin(("👨‍💼 THỦ THƯ<br/>(Quản Trị Viên)"))
    Hardware(("⚡ PHẦN CỨNG<br/>(ESP32 & RFID)"))

    %% Subgraph Kiosk
    subgraph UC_Kiosk ["HỆ THỐNG KIOSK TỰ PHỤC VỤ (CLIENT KIOSK)"]
        UC1(["Quẹt thẻ xác thực danh tính"])
        UC2(["Mượn sách theo đợt (Batch Borrow)"])
        UC3(["Trả sách tự phục vụ"])
        UC4(["Gia hạn thời gian mượn"])
        UC5(["Xem nợ phạt & Thanh toán VietQR"])
        UC6(["Trò chuyện giọng nói với Thủ thư AI 'Nova'"])
        UC7(["Xem sơ đồ chỉ đường Kệ Sách (Tầng 1, 2, 3)"])
        UC8(["Nhận biên lai điện tử qua Email"])
    end

    %% Subgraph Admin
    subgraph UC_Admin ["HỆ THỐNG QUẢN TRỊ THỦ THƯ (ADMIN DASHBOARD)"]
        UC9(["Giám sát Kiosk Realtime (Online/Offline/RSSI)"])
        UC10(["Điều khiển phần cứng từ xa (Test còi / Reboot)"])
        UC11(["Quản lý danh mục 3.000 sách (CRUD)"])
        UC12(["Quản lý hồ sơ bạn đọc & Khóa/Mở thẻ"])
        UC13(["Kiểm toán sách hư hại / Báo mất sách"])
        UC14(["Miễn / Giảm tiền phạt quá hạn"])
        UC15(["Báo cáo thống kê & Biểu đồ mượn trả"])
    end

    %% Subgraph IoT
    subgraph UC_IoT ["TÁC VỤ PHẦN CỨNG BIÊN (EMBEDDED)"]
        UC16(["Quét thẻ RFID & Khử rung Cooldown"])
        UC17(["Phát âm thanh còi & Đèn LED báo hiệu"])
        UC18(["Gửi nhịp tim định kỳ (Heartbeat 30s)"])
    end

    %% Connections Reader
    Reader --> UC1
    Reader --> UC2
    Reader --> UC3
    Reader --> UC4
    Reader --> UC5
    Reader --> UC6
    Reader --> UC7
    Reader -.->|"Nhận email tự động"| UC8

    %% Connections Admin
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
    Admin --> UC14
    Admin --> UC15

    %% Connections Hardware
    Hardware --> UC16
    Hardware --> UC17
    Hardware --> UC18

    %% Inter-relationships
    UC16 ==>|"Bắn MQTT Topic scan"| UC1
    UC16 ==>|"Bắn MQTT Topic scan"| UC2
    UC16 ==>|"Bắn MQTT Topic scan"| UC3
    UC2 -.->|"Tự động gửi"| UC8
    UC3 -.->|"Tự động gửi"| UC8
    UC18 ==>|"LWT / Status"| UC9

    classDef actorStyle fill:#f8fafc,stroke:#0f172a,stroke-width:2px,color:#0f172a;
    classDef kioskUC fill:#f0fdf4,stroke:#16a34a,stroke-width:1.5px,color:#14532d;
    classDef adminUC fill:#eff6ff,stroke:#2563eb,stroke-width:1.5px,color:#1e3a8a;
    classDef iotUC fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#92400e;

    class Reader,Admin,Hardware actorStyle;
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7,UC8 kioskUC;
    class UC9,UC10,UC11,UC12,UC13,UC14,UC15 adminUC;
    class UC16,UC17,UC18 iotUC;
```

---

## 🔄 4. SƠ ĐỒ LUỒNG HOẠT ĐỘNG NGHIỆP VỤ (BUSINESS PROCESS FLOWCHARTS)

### A. Luồng Mượn Sách Theo Đợt (Batch Borrowing Flow):

```mermaid
flowchart TD
    Start(["Bắt đầu giao dịch"]) --> Step1["Sinh viên chọn 'MƯỢN SÁCH' trên màn hình Kiosk"]
    Step1 --> Step2["Yêu cầu quẹt thẻ sinh viên lên đầu đọc RFID"]
    Step2 --> CheckCard{"Thẻ sinh viên<br/>hợp lệ?"}

    CheckCard -- "Không / Thẻ lạ" --> Err1["Kêu 'Bíp Bíp', nháy LED đỏ<br/>Hiện thông báo thẻ không hợp lệ"] --> Step2
    CheckCard -- "Thẻ bị Khóa" --> Err2["Báo lỗi: Thẻ độc giả đang bị khóa<br/>Vui lòng liên hệ thủ thư"] --> End(["Kết thúc"])

    CheckCard -- "Hợp lệ" --> CheckDebt{"Đang nợ phạt<br/>hoặc sách quá hạn?"}
    CheckDebt -- "Có sách quá hạn" --> Err3["Cảnh báo: Bạn đang có sách quá hạn<br/>Phải trả sách trước khi mượn mới"] --> End

    CheckDebt -- "Không nợ" --> AuthOK["Xác thực thành công!<br/>Mở phiên làm việc của sinh viên"]
    AuthOK --> ScanBook["Sinh viên đặt lần lượt các cuốn sách lên khay RFID"]

    ScanBook --> CheckDup{"Sách đã có<br/>trong giỏ?"}
    CheckDup -- "Đã có" --> WarnDup["Bỏ qua quét trùng lặp"] --> ScanBook

    CheckDup -- "Mới" --> CheckAvail{"Sách có sẵn<br/>trong kho (available)?"}
    CheckAvail -- "Không khả dụng" --> ErrBook["Báo lỗi: Sách đang được mượn<br/>hoặc chưa trả kho"] --> ScanBook

    CheckAvail -- "Khả dụng" --> AddCart["Kêu 'Bíp', nháy LED xanh<br/>Thêm sách vào Giỏ Mượn Kiosk"]
    AddCart --> CheckMax{"Số lượng sách<br/>mượn > 5 cuốn?"}
    CheckMax -- "Vượt quá" --> ErrMax["Thông báo đã đạt hạn mức 5 cuốn"] --> ShowCart
    CheckMax -- "Hợp lệ" --> ShowCart["Hiển thị danh sách giỏ sách trên màn hình"]

    ShowCart --> UserConfirm{"Bấm nút<br/>'XÁC NHẬN MƯỢN'?"}
    UserConfirm -- "Quét tiếp" --> ScanBook
    UserConfirm -- "Đồng ý" --> Commit["1. Trừ số lượng sách khả dụng trong CSDL<br/>2. Tạo bản ghi Mượn sách (Loans) với hạn 14 ngày<br/>3. Kêu chuông thành công<br/>4. Tự động gửi Email Biên Lai điện tử<br/>5. Hiển thị Popup Biên Lai thành công"]
    Commit --> End
```

---

### B. Luồng Trả Sách & Nộp Phạt Quá Hạn VietQR (Return & Fine Flow):

```mermaid
flowchart TD
    Start(["Bắt đầu trả sách"]) --> S1["Sinh viên chọn 'TRẢ SÁCH' trên Kiosk"]
    S1 --> S2["Đặt cuốn sách cần trả lên khay quét RFID"]
    S2 --> S3["ESP32 đọc mã RFID sách gửi lên Server qua MQTT"]
    S3 --> S4["Server truy vấn thông tin mượn hiện tại của cuốn sách"]

    S4 --> CheckLoan{"Sách có đang<br/>được mượn không?"}
    CheckLoan -- "Không" --> ErrNotBorrowed["Báo lỗi: Sách đang có sẵn trong kho,<br/>không có giao dịch mượn cần trả!"] --> End(["Kết thúc"])

    CheckLoan -- "Đang mượn" --> CalcDate{"Kiểm tra hạn trả<br/>(Current Date vs Due Date)?"}
    CalcDate -- "Đúng hạn / Trước hạn" --> FineZero["Tiền phạt = 0 VNĐ<br/>Cập nhật trạng thái: Đã trả (Returned)"]

    CalcDate -- "Quá hạn" --> CalcFine["Tính tiền phạt trễ hạn:<br/>Số ngày trễ x 1.000 VNĐ/ngày"]
    CalcFine --> ShowQR["Tạo mã chuẩn VietQR động (Ngân hàng, Số tiền, Nội dung)<br/>Hiển thị Modal QR trên màn hình Kiosk"]
    ShowQR --> PayCheck{"Sinh viên quét QR<br/>nộp phạt qua App Ngân hàng?"}
    PayCheck -- "Xác nhận nộp phạt" --> FineZero

    FineZero --> UpdateDB["1. Cập nhật sách: status = 'available'<br/>2. Đóng bản ghi Loan: returnedAt = Now<br/>3. Kêu còi 'Bíp', nháy LED xanh<br/>4. Gửi Email thông báo trả sách thành công<br/>5. Cập nhật tức thì lên Dashboard Thủ thư"] --> End
```

---

### C. Luồng Trò Chuyện Tìm Sách Rảnh Tay với Thủ Thư AI "Nova" (Hands-Free AI Search):

```mermaid
flowchart TD
    Start(["Màn hình Trợ lý AI (/kiosk/search)"]) --> Standby["Hệ thống ở chế độ Chờ (Standby: 'SẴN SÀNG: NOVA')<br/>Microphone lắng nghe thụ động từ khóa đánh thức"]

    Standby --> Hear{"Người dùng nói:<br/>'Nova' hoặc 'Nova ơi'?"}
    Hear -- "Tạp âm / Tiếng điện thoại" --> Ignore["Bộ lọc âm vị tiếng Việt: Bỏ qua hoàn toàn!"] --> Standby

    Hear -- "Khớp từ khóa 'Nova'" --> WakeUp["1. Phát chuông đánh thức 'Bính-Boong' 🔔<br/>2. Xả sạch bộ đệm âm thanh cũ (Flush Buffer)<br/>3. Hiện lời chào trợ lý trong chat box<br/>4. Chuyển trạng thái sang: 'NOVA ĐANG LẮNG NGHE' 🎙️"]

    WakeUp --> SpeakQuery["Người dùng nói câu hỏi tự nhiên:<br/>'Tìm cho mình sách lập trình C++ và cấu trúc dữ liệu'"]
    SpeakQuery --> RealtimeText["Hiển thị văn bản nhận diện trực tiếp trên ô nhập liệu"]

    RealtimeText --> SilenceDetect{"Dứt câu yên lặng<br/>đủ 1.6 giây?"}
    SilenceDetect -- "Đang nói tiếp" --> RealtimeText
    SilenceDetect -- "Đủ 1.6s" --> Submit["Tự động đóng chế độ nói (Mic tắt)<br/>Gửi câu hỏi tới AI Engine"]

    Submit --> Reasoner["AI Engine phân tích (FastAPI + In-Memory Fallback):<br/>• Semantic Search Multilingual-E5 (Độ tương đồng ngữ nghĩa)<br/>• Lexical BM25Okapi (Khớp từ khóa chính xác)<br/>• Reciprocal Rank Fusion (RRF) xếp hạng 3.000 sách<br/>• Truy xuất vị trí kệ thực tế: Kệ A-D, Tầng 1-3"]

    Reasoner --> Render["Hiển thị kết quả trong khung chat:<br/>• Lời tư vấn chu đáo từ Thủ thư AI<br/>• Thẻ sách: Tựa đề, Tác giả, Số lượng sẵn có<br/>• Nút bấm: 'Xem sơ đồ kệ X'"]

    Render --> MapClick{"Người dùng bấm<br/>'Xem sơ đồ kệ'?"}
    MapClick -- "Có" --> ShowModal["Mở Modal Sơ Đồ Chỉ Đường Kệ Sách Thực Tế<br/>Vẽ lộ trình Kiosk ➔ Kệ sách chính xác theo Tầng & Ô"]
    MapClick -- "Không" --> StandbyNext["Trở về chế độ chờ 'Nova' cho đợt trò chuyện tiếp theo"]
    ShowModal --> StandbyNext
```

---

## ⏱️ 5. SƠ ĐỒ TUẦN TỰ THỜI GIAN THỰC (REAL-TIME IOT SEQUENCE DIAGRAM)

```mermaid
sequenceDiagram
    autonumber
    actor Reader as 👤 Sinh Viên
    participant ESP32 as ⚡ ESP32 & RC522
    participant MQTT as 📡 Mosquitto Broker
    participant Server as ⚙️ Node.js Backend
    participant Mongo as 🗄️ MongoDB Database
    participant KioskUI as 🖥️ Kiosk React UI
    participant AdminUI as 👨‍💼 Admin Dashboard

    Note over Reader,AdminUI: GIAI ĐOẠN 1: QUẸT THẺ SINH VIÊN XÁC THỰC DANH TÍNH
    Reader->>ESP32: Chạm thẻ sinh viên lên đầu đọc RFID RC522
    ESP32->>ESP32: Đọc mã UID (VD: "A1704E6D") & Kiểm tra Cooldown 1.000ms
    ESP32->>MQTT: Publish Topic: kiosk/kiosk_01/scan {"uid": "A1704E6D", "type": "rfid"}
    MQTT->>Server: Chuyển tiếp Payload tới MQTT Handler
    Server->>Mongo: Truy vấn Reader.findOne({ rfidTag: "A1704E6D" }) & Active Loans
    Mongo-->>Server: Trả về thông tin Bạn đọc & Danh sách sách đang mượn

    alt Thẻ Bạn Đọc Hợp Lệ
        Server->>MQTT: Publish Topic: kiosk/kiosk_01/command {"action": "feedback", "status": "success"}
        MQTT->>ESP32: Nhận lệnh phản hồi phần cứng
        ESP32->>ESP32: Kêu 1 tiếng "Bíp" (1.8kHz) & Nháy LED Xanh (120ms)
        Server->>KioskUI: Socket.IO Emit: "kiosk:event" {type: "READER_AUTHENTICATED", data: reader}
        KioskUI-->>Reader: Màn hình chào mừng sinh viên & Mở giao diện Giỏ Mượn
    else Thẻ Lạ Chưa Đăng Ký
        Server->>MQTT: Publish Topic: kiosk/kiosk_01/command {"action": "feedback", "status": "error"}
        ESP32->>ESP32: Kêu 2 tiếng "Bíp Bíp" & Nháy LED Đỏ
        Server->>KioskUI: Socket.IO Emit: "kiosk:event" {type: "UNKNOWN_CARD"}
        KioskUI-->>Reader: Hiện thông báo thẻ không hợp lệ trên màn hình
    end

    Note over Reader,AdminUI: GIAI ĐOẠN 2: QUÉT SÁCH VÀO GIỎ & ĐỒNG BỘ REALTIME
    Reader->>ESP32: Chạm cuốn sách lên khay quét RFID
    ESP32->>MQTT: Publish Topic: kiosk/kiosk_01/scan {"uid": "1DE63B59", "type": "rfid"}
    MQTT->>Server: Chuyển tiếp Payload thẻ sách
    Server->>Mongo: Kiểm tra trạng thái sách: Book.findOne({ rfidTag: "1DE63B59" })
    Mongo-->>Server: Sách khả dụng (available = 3, status = "available")
    Server->>MQTT: Publish Topic: kiosk/kiosk_01/command {"action": "feedback", "status": "success"}
    ESP32->>ESP32: Kêu 1 tiếng "Bíp" & Nháy LED Xanh
    Server->>KioskUI: Socket.IO Emit: "kiosk:event" {type: "BOOK_SCANNED", book: bookData}
    KioskUI-->>Reader: Thêm sách vào danh sách Giỏ Mượn trên màn hình

    Note over Reader,AdminUI: GIAI ĐOẠN 3: XÁC NHẬN MƯỢN & GỬI EMAIL THỜI GIAN THỰC
    Reader->>KioskUI: Bấm nút "XÁC NHẬN MƯỢN TÀI LIỆU"
    KioskUI->>Server: HTTP POST /api/loans/borrow {readerId, bookIds: ["..."]}
    Server->>Mongo: Cập nhật Transaction: Tạo Loan, trừ Book.availableCopies
    Mongo-->>Server: Ghi dữ liệu thành công
    Server->>Server: Gửi Email Biên Lai mượn sách qua Gmail SMTP
    Server->>AdminUI: Socket.IO Emit: "loan:new" {reader, books, dueDate}
    AdminUI-->>AdminUI: Cập nhật biểu đồ thống kê & Bảng kiểm toán thời gian thực
    Server-->>KioskUI: HTTP 200 OK {success: true, receipt: {...}}
    KioskUI-->>Reader: Hiển thị Popup Biên Lai & Kêu chuông hoàn tất!
```

---

## 📂 6. CẤU TRÚC THƯ MỤC DỰ ÁN (PROJECT STRUCTURE)

```text
library-kiosk/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI Workflow (Test, Build, Lint tự động)
├── .husky/                        # Git Pre-commit Hooks bảo vệ chất lượng code
├── eslint.config.js               # Cấu hình kiểm tra cú pháp ESLint 9 Flat Config
├── .prettierrc                    # Quy chuẩn định dạng code toàn bộ dự án
├── docker-compose.yml             # Khởi chạy hạ tầng containerized: Mosquitto Broker + MongoDB
├── package.json                   # Quản lý scripts, dependencies và workspace
├── start.bat                      # Script 1-Click khởi chạy toàn bộ 3 dịch vụ tự động
├── README.md                      # Tài liệu thuyết trình và kiến trúc hệ thống
│
├── ai-service/                    # Dịch vụ Trợ lý AI Tìm kiếm Sách Nova (Python FastAPI)
│   ├── main.py                    # Điểm chạy API server (FastAPI, CORS, Endpoints)
│   ├── run.bat                    # Script khởi chạy FastAPI chuẩn ASCII (Port 8000)
│   ├── run.ps1                    # Script PowerShell khởi chạy FastAPI
│   ├── requirements.txt           # Thư viện Python (uvicorn, fastapi, torch, sentence-transformers)
│   ├── dataset/
│   │   └── books_dataset.csv      # Bộ dữ liệu 3.000 cuốn sách thư viện thực tế
│   ├── embeddings/
│   │   ├── book_ids.json          # Chỉ mục ánh xạ ID sách
│   │   └── metadata.json          # Metadata tác giả, thể loại, vị trí kệ
│   └── src/
│       ├── hybrid_search_v2.py    # Thuật toán tìm kiếm Hybrid (E5 Embeddings + BM25Okapi + RRF)
│       ├── query_understanding.py # Xử lý ngôn ngữ tự nhiên, bóc tách thực thể câu hỏi
│       └── response_generator.py  # Sinh câu trả lời tư vấn phong cách Thủ thư chuyên nghiệp
│
├── server/                        # Backend Server (Node.js Express + Socket.IO + MQTT)
│   ├── vitest.config.js           # Cấu hình kiểm thử tự động Vitest
│   ├── package.json
│   ├── .env.example               # Mẫu cấu hình môi trường chuẩn
│   ├── tests/                     # Bộ kiểm thử tự động (55/55 Tests Passed 100%)
│   │   └── unit/                  # Kiểm thử logic mượn trả, tính phạt VietQR, MQTT, AI fallback
│   └── src/
│       ├── index.js               # Khởi chạy HTTP Server + Socket.IO + MQTT Gateway (Port 5000)
│       ├── config/                # Schema xác thực biến môi trường Zod, Mongoose DB
│       ├── models/                # Schemas: Reader, Book, Loan, DeviceLog, AuditLog
│       ├── routes/                # REST API Routers: readers, books, loans, devices, ai
│       ├── services/              # Nghiệp vụ: loanService, catalogService, emailService
│       ├── controllers/           # Điều khiển: bookController, readerController, aiController
│       ├── mqtt/
│       │   ├── client.js          # Kết nối Mosquitto MQTT Broker
│       │   ├── handlers/          # Xử lý sự kiện quét thẻ (cardHandler), nhịp tim (statusHandler)
│       │   └── publisher.js       # Phát lệnh điều khiển còi/LED xuống ESP32
│       └── sockets/               # Phát sự kiện Realtime tới React Client
│
├── client/                        # Frontend Web Application (React 18 + Vite)
│   ├── package.json
│   ├── vite.config.js             # Cấu hình Vite bundler tốc độ cao
│   └── src/
│       ├── App.jsx                # Bộ định tuyến SPA (/kiosk và /admin)
│       ├── socket/                # Kết nối Client Socket.IO tới Backend
│       ├── api/                   # Axios API Service kết nối REST endpoints
│       ├── utils/
│       │   └── audio.js           # Singleton Web Audio API (Chuông Wake, Beep thành công, Cắt tiếng)
│       ├── components/            # ShelfLocatorModal (Sơ đồ kệ), ReceiptModal, VietQrModal
│       └── pages/
│           ├── kiosk/             # KioskPage, KioskHome, BorrowSection, ReturnSection, AiSearchSection
│           └── admin/             # AdminPage (Dashboard giám sát IoT, Quản lý sách, Thẻ, Nhật ký)
│
└── firmware/                      # Mã nguồn nhúng ESP32 (C++ / PlatformIO)
    ├── platformio.ini             # Cấu hình board esp32doit-devkit-v1, thư viện MFRC522, PubSubClient
    ├── include/
    │   ├── config.example.h       # Mẫu cấu hình WiFi SSID/Password, MQTT Broker IP
    │   └── pins.h                 # Định nghĩa chân SPI RC522 (GPIO 5, 18, 19, 23, 22), Buzzer (25), LED (26, 27)
    └── src/
        ├── main.cpp               # Máy trạng thái hữu hạn (FSM) và vòng lặp loop()
        ├── wifi_manager.cpp       # Quản lý kết nối & Tự động tái kết nối WiFi
        ├── mqtt_client.cpp        # Kết nối MQTT, gửi Heartbeat (30s), Last Will (LWT)
        ├── rfid_reader.cpp        # Đọc mã thẻ Mifare/NFC và chống dội quét trùng lặp
        └── indicators.cpp         # Điều khiển còi Buzzer tần số cao và LED kép
```

---

## 📡 7. ĐẶC TẢ GIAO THỨC TRUYỀN THÔNG MQTT (MQTT CONTRACT)

Hệ thống tuân thủ hợp đồng giao tiếp MQTT phân cấp theo chuẩn thiết bị:

| Chiều Truyền       | Topic MQTT                        | Payload JSON Mẫu                                    | Diễn Giải Nghiệp Vụ                                    |
| :----------------- | :-------------------------------- | :-------------------------------------------------- | :----------------------------------------------------- |
| **ESP32 ➔ Server** | `kiosk/{deviceId}/scan`           | `{"uid": "A1704E6D", "type": "rfid"}`               | Gửi mã UID thẻ vừa quẹt từ đầu đọc RC522               |
| **ESP32 ➔ Server** | `kiosk/{deviceId}/status`         | `{"status": "online", "rssi": -58, "uptime": 3600}` | Báo cáo nhịp tim định kỳ (Heartbeat 30 giây/lần)       |
| **ESP32 ➔ Server** | `kiosk/{deviceId}/status` _(LWT)_ | `{"status": "offline"}`                             | Tự động bắn thông báo khi Kiosk mất điện/WiFi đột ngột |
| **Server ➔ ESP32** | `kiosk/{deviceId}/command`        | `{"action": "feedback", "status": "success"}`       | Ra lệnh kêu 1 tiếng "Bíp" và nháy LED xanh (Hợp lệ)    |
| **Server ➔ ESP32** | `kiosk/{deviceId}/command`        | `{"action": "feedback", "status": "error"}`         | Ra lệnh kêu 2 tiếng "Bíp Bíp" và nháy LED đỏ (Từ chối) |
| **Server ➔ ESP32** | `kiosk/{deviceId}/command`        | `{"action": "reboot"}`                              | Khởi động lại vi điều khiển ESP32 từ xa qua Web Admin  |

---

## 🚀 8. HƯỚNG DẪN CÀI ĐẶT & CHẠY THỬ NHANH (QUICK START)

### Yêu Cầu Tiên Quyết:

- **Node.js:** Phiên bản 18 hoặc 20 trở lên.
- **Python:** 3.10+ (để chạy dịch vụ AI FastAPI).
- **Docker & Docker Compose** (khuyên dùng để chạy nhanh Mosquitto MQTT & MongoDB trong 1 lệnh) hoặc cài trực tiếp MongoDB và Mosquitto trên máy tính.

---

---

### Cách 1: Khởi Chạy Từng Dịch Vụ Bằng Lệnh Thủ Công

1. **Cài đặt thư viện toàn bộ dự án:**

   ```bash
   npm run setup
   ```

2. **Khởi chạy AI Service (FastAPI):**
   ```bash
   npm run ai:dev
   ```
3. **Khởi chạy Backend Server (Node.js):**
   ```bash
   npm run server:dev
   ```
4. **Khởi chạy Frontend React (Kiosk & Admin):**
   ```bash
   npm run client:dev
   ```

---

## 🧪 9. KIỂM THỬ CHẤT LƯỢNG PHẦN MỀM (AUTOMATED TESTING & CI/CD)

Hệ thống được trang bị bộ kiểm thử tự động toàn diện đảm bảo vận hành ổn định trước hội đồng:

- **Chạy toàn bộ 55 Unit Tests:**
  ```bash
  npm test
  ```
  _(Kiểm tra toàn bộ logic mượn sách, trả sách, tính tiền phạt trễ hạn VietQR, xác thực thẻ, gửi email và cơ chế tự động phục hồi Fallback của AI Service)._
- **Kiểm tra chuẩn mã nguồn (ESLint):**
  ```bash
  npm run lint
  ```
  _(Đạt kết quả hoàn hảo: 0 errors, 0 warnings)._
- **Kiểm tra đóng gói Frontend (Production Build):**
  ```bash
  npm --prefix client run build
  ```
  _(Vite tối ưu hóa và đóng gói thành công 100% trong ~4 giây)._

---

## 🎓 10. KẾT QUẢ ĐẠT ĐƯỢC & TÍNH ỨNG DỤNG THỰC TẾ

1. **Hiệu năng vượt trội:** Thời gian phản hồi từ lúc quẹt thẻ vật lý đến khi giao diện Kiosk cập nhật chỉ **dưới 80ms** nhờ sự kết hợp tối ưu giữa giao thức MQTT và WebSocket (Socket.IO).
2. **Độ ổn định cao:** Cơ chế tự động bù trừ ngoại tuyến (_Failover Fallback_) cho phép trạm Kiosk vẫn tìm kiếm và gợi ý sách chính xác kể cả khi mạng Internet bị ngắt hoặc dịch vụ Python ngoại tuyến.
3. **Trải nghiệm người dùng thông minh:** Khả năng tương tác bằng giọng nói rảnh tay (_Hands-free Voice Wake Word "Nova"_) độc đáo, nhận diện chuẩn xác tiếng Việt và tự động loại bỏ tạp âm lớp học/hội trường.
4. **Chi phí chế tạo siêu tiết kiệm:** Với tổng kinh phí phần cứng chỉ khoảng **~138.000 VNĐ**, đề tài hoàn toàn khả thi để nhân rộng lắp đặt hàng loạt tại các thư viện trường học trên cả nước.

---

**Đồ án hoàn thành bởi Sinh viên Học viện Công nghệ Bưu chính Viễn thông (PTIT) • Phiên bản: `final_v1`**
