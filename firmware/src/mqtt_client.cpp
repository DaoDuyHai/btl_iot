#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "mqtt_client.h"

static WiFiClient espClient;
static PubSubClient client(espClient);
static String _deviceId = "";
static CommandCallback _cmdCallback = nullptr;

static void internalCallback(char* topic, byte* message, unsigned int length) {
    String msg = "";
    for (unsigned int i = 0; i < length; i++) msg += (char)message[i];

    Serial.printf("📥 [MQTT In] [%s]: %s\n", topic, msg.c_str());

    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, msg);
    if (!error && _cmdCallback) {
        String action = doc["action"] | "";
        String status = doc["status"] | "";
        _cmdCallback(action, status);
    }
}

void initMQTT(const char* server, int port, const char* deviceId, CommandCallback onCommand) {
    _deviceId = deviceId;
    _cmdCallback = onCommand;

    client.setServer(server, port);
    client.setCallback(internalCallback);
    Serial.printf("✅ [MQTT] Cấu hình Broker: %s:%d (Device: %s)\n", server, port, deviceId);
}

static void reconnect() {
    static unsigned long lastAttempt = 0;
    if (millis() - lastAttempt < 3000) return; // Thử lại sau mỗi 3 giây
    lastAttempt = millis();

    Serial.print("🔄 [MQTT] Đang kết nối tới Broker...");

    // Cấu hình MQTT Last Will and Testament (LWT)
    String willTopic = "kiosk/" + _deviceId + "/status";
    String willPayload = "{\"status\":\"offline\"}";

    if (client.connect(_deviceId.c_str(), willTopic.c_str(), 1, false, willPayload.c_str())) {
        Serial.println(" Thành công!");

        // Gửi báo cáo Online
        client.publish(willTopic.c_str(), "{\"status\":\"online\"}");

        // Lắng nghe topic nhận lệnh từ Server
        String cmdTopic = "kiosk/" + _deviceId + "/command";
        client.subscribe(cmdTopic.c_str());
        Serial.printf("📡 [MQTT] Đã lắng nghe lệnh tại: %s\n", cmdTopic.c_str());
    } else {
        Serial.printf(" Thất bại, mã lỗi rc=%d\n", client.state());
    }
}

void loopMQTT() {
    if (!client.connected()) {
        reconnect();
    } else {
        client.loop();
    }
}

bool publishCardScan(const String& deviceId, const String& uid) {
    if (!client.connected()) return false;

    StaticJsonDocument<200> doc;
    doc["uid"] = uid;
    doc["type"] = "rfid";
    doc["timestamp"] = millis() / 1000;

    char buffer[200];
    serializeJson(doc, buffer);

    String topic = "kiosk/" + deviceId + "/scan";
    return client.publish(topic.c_str(), buffer);
}

bool publishHeartbeat(const String& deviceId, int rssi, unsigned long uptimeSec) {
    if (!client.connected()) return false;

    StaticJsonDocument<200> doc;
    doc["status"] = "online";
    doc["rssi"] = rssi;
    doc["uptime"] = uptimeSec;

    char buffer[200];
    serializeJson(doc, buffer);

    String topic = "kiosk/" + deviceId + "/status";
    return client.publish(topic.c_str(), buffer);
}

