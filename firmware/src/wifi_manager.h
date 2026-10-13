#pragma once
#include <Arduino.h>

void initWiFi(const char* ssid, const char* password);
void checkWiFiConnection();
bool isWiFiConnected();
int getWiFiRSSI();

