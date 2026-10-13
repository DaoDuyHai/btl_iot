import dotenv from 'dotenv';
dotenv.config();

export const ENV = {
  PORT: process.env.PORT || 5000,
  MONGODB_URI: process.env.MONGODB_URI || 'mongodb://localhost:27017/library_kiosk',
  MQTT_BROKER_URL: process.env.MQTT_BROKER_URL || 'mqtt://localhost:1883',
  KIOSK_DEVICE_ID: process.env.KIOSK_DEVICE_ID || 'kiosk_01',
  CLIENT_URL: process.env.CLIENT_URL || 'http://localhost:5173',
  FINE_PER_DAY_VND: parseInt(process.env.FINE_PER_DAY_VND, 10) || 5000, // 5.000 VNĐ / ngày trễ hạn
  BANK_BIN: process.env.BANK_BIN || '970422', // MBBank
  BANK_ACCOUNT: process.env.BANK_ACCOUNT || '000124135246'
};

