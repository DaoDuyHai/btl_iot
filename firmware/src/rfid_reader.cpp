#include <SPI.h>
#include <MFRC522.h>
#include "rfid_reader.h"
#include "pins.h"

static MFRC522 rfid(PIN_RC522_SS, PIN_RC522_RST);
static String lastScannedUID = "";
static unsigned long lastScanTime = 0;

void initRFID() {
    SPI.begin(PIN_RC522_SCK, PIN_RC522_MISO, PIN_RC522_MOSI, PIN_RC522_SS);
    rfid.PCD_Init();
    Serial.println("✅ [RFID] Module RC522 đã khởi tạo thành công qua chuẩn SPI.");
}

bool readRFID(String &outUID) {
    if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
        return false;
    }

    String uid = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) uid += "0";
        uid += String(rfid.uid.uidByte[i], HEX);
    }
    uid.toUpperCase();

    // Chống quẹt lặp rung thẻ (debounce 1.5 giây cho cùng 1 thẻ)
    if (uid == lastScannedUID && (millis() - lastScanTime < 1500)) {
        rfid.PICC_HaltA();
        rfid.PCD_StopCrypto1();
        return false;
    }

    lastScannedUID = uid;
    lastScanTime = millis();
    outUID = uid;

    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    return true;
}

