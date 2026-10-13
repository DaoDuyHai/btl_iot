#pragma once
#include <Arduino.h>

typedef void (*CommandCallback)(const String& action, const String& status);

void initMQTT(const char* server, int port, const char* deviceId, CommandCallback onCommand);
void loopMQTT();
bool publishCardScan(const String& deviceId, const String& uid);
bool publishHeartbeat(const String& deviceId, int rssi, unsigned long uptimeSec);

