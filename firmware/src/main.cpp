#include <Arduino.h>

#include "pins.h"
#include "indicators.h"
#include "wifi_manager.h"
#include "rfid_reader.h"
#include "mqtt_client.h"

// Tự động nạp cấu hình WiFi và Broker nếu có file config.h
#if __has_include("config.h")
    #include "config.h"
#else
    #define WIFI_SSID       "WIFI_TEST"
    #define WIFI_PASSWORD   "12345678"
    #define MQTT_SERVER     "192.168.1.100"
    #define MQTT_PORT       1883
    #define DEVICE_ID       "kiosk_01"
#endif

static unsigned long lastHeartbeatTime = 0;

// Xử lý lệnh nhận từ MQTT Broker (do Server gửi xuống)
void handleServerCommand(const String& action, const String& status) {
    if (action == "feedback") {
        if (status == "success") {
            feedbackSuccess();
        } else {
            feedbackError();
        }
    } else if (action == "reboot") {
        Serial.println("🔄 [System] Nhận lệnh khởi động lại từ xa...");
        feedbackError();
        delay(500);
        ESP.restart();
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n==============================================");
    Serial.println("🚀 SMART LIBRARY KIOSK FIRMWARE - ESP32 V1.0");
    Serial.println("==============================================");

    // 1. Khởi tạo ngoại vi (Buzzer & LED)
    initIndicators();
    feedbackSuccess(); // Kêu bíp chào mừng khi khởi động

    // 2. Khởi tạo Module RFID RC522 (Chuẩn SPI)
    initRFID();

    // 3. Khởi tạo kết nối mạng WiFi
    initWiFi(WIFI_SSID, WIFI_PASSWORD);

    // 4. Khởi tạo MQTT Client & đăng ký hàm xử lý lệnh
    initMQTT(MQTT_SERVER, MQTT_PORT, DEVICE_ID, handleServerCommand);
}

void loop() {
    // 1. Duy trì kết nối WiFi và MQTT
    checkWiFiConnection();
    loopMQTT();

    // 2. Định kỳ gửi nhịp tim Heartbeat mỗi 30 giây (kèm sóng WiFi RSSI và Uptime)
    if (millis() - lastHeartbeatTime > 30000) {
        lastHeartbeatTime = millis();
        unsigned long uptimeSec = millis() / 1000;
        publishHeartbeat(DEVICE_ID, getWiFiRSSI(), uptimeSec);
        Serial.printf("💓 [Heartbeat] Đã gửi nhịp tim Kiosk: Uptime %lus, RSSI %d dBm\n", 
            uptimeSec, getWiFiRSSI());
    }

    // 3. Quét thẻ RFID (Thẻ sinh viên hoặc Thẻ sách)
    String scannedUID = "";
    if (readRFID(scannedUID)) {
        Serial.printf("💳 [RFID] Phát hiện thẻ UID: %s\n", scannedUID.c_str());
        
        // Gửi ngay lên Broker qua topic kiosk/{deviceId}/scan
        if (publishCardScan(DEVICE_ID, scannedUID)) {
            Serial.println("📤 [MQTT] Đã gửi thẻ thành công lên Server.");
            feedbackSuccess(); // Beep xác nhận đã gửi
        } else {
            Serial.println("❌ [MQTT] Gửi thẻ thất bại (Mất kết nối MQTT).");
            feedbackError();
        }
    }
}
