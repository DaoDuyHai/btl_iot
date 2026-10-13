#include <WiFi.h>
#include "wifi_manager.h"

static const char* _ssid = "";
static const char* _pass = "";

void initWiFi(const char* ssid, const char* password) {
    _ssid = ssid;
    _pass = password;

    Serial.printf("\n[WiFi] Đang kết nối mạng: %s\n", _ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(_ssid, _pass);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n✅ [WiFi] Đã kết nối! IP: %s | RSSI: %d dBm\n", 
            WiFi.localIP().toString().c_str(), WiFi.RSSI());
    } else {
        Serial.println("\n⚠️ [WiFi] Chưa thể kết nối tới WiFi, sẽ tự động thử lại trong vòng lặp.");
    }
}

void checkWiFiConnection() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("🔄 [WiFi] Mất sóng WiFi, đang kết nối lại...");
        WiFi.reconnect();
    }
}

bool isWiFiConnected() {
    return WiFi.status() == WL_CONNECTED;
}

int getWiFiRSSI() {
    return WiFi.RSSI();
}

