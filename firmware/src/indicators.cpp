#include <Arduino.h>
#include "indicators.h"

void initIndicators() {
    pinMode(PIN_BUZZER, OUTPUT);
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_RED, LOW);
}

void feedbackSuccess() {
    digitalWrite(PIN_LED_GREEN, HIGH);
    digitalWrite(PIN_BUZZER, HIGH);
    delay(100);
    digitalWrite(PIN_BUZZER, LOW);
    delay(400);
    digitalWrite(PIN_LED_GREEN, LOW);
}

void feedbackError() {
    for (int i = 0; i < 2; i++) {
        digitalWrite(PIN_LED_RED, HIGH);
        digitalWrite(PIN_BUZZER, HIGH);
        delay(100);
        digitalWrite(PIN_BUZZER, LOW);
        digitalWrite(PIN_LED_RED, LOW);
        delay(100);
    }
}

