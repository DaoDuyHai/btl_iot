import mqtt from 'mqtt';
import { ENV } from '../config/env.js';
import { handleCardScan } from './handlers/cardScan.js';
import { handleDeviceStatus } from './handlers/deviceStatus.js';

let mqttClientInstance = null;

export function initMQTT() {
  console.log(`🔌 [MQTT] Đang kết nối Broker tại: ${ENV.MQTT_BROKER_URL}...`);

  mqttClientInstance = mqtt.connect(ENV.MQTT_BROKER_URL, {
    reconnectPeriod: 5000,
    connectTimeout: 10000
  });

  mqttClientInstance.on('connect', () => {
    console.log('✅ [MQTT] Kết nối thành công tới Mosquitto Broker!');

    // Lắng nghe tất cả các Kiosk
    mqttClientInstance.subscribe('kiosk/+/scan', (err) => {
      if (!err) console.log('📡 [MQTT] Đã lắng nghe: kiosk/+/scan');
    });

    mqttClientInstance.subscribe('kiosk/+/status', (err) => {
      if (!err) console.log('📡 [MQTT] Đã lắng nghe: kiosk/+/status');
    });
  });

  mqttClientInstance.on('message', async (topic, message) => {
    try {
      const parts = topic.split('/');
      // topic: kiosk/{deviceId}/{action}
      if (parts.length < 3) return;

      const deviceId = parts[1];
      const action = parts[2];
      const payload = JSON.parse(message.toString());

      if (action === 'scan') {
        await handleCardScan(deviceId, payload);
      } else if (action === 'status') {
        await handleDeviceStatus(deviceId, payload);
      }
    } catch (err) {
      console.error(`❌ [MQTT] Lỗi phân tích gói tin [${topic}]:`, err.message);
    }
  });

  mqttClientInstance.on('error', (err) => {
    console.error(`❌ [MQTT] Lỗi kết nối Broker:`, err.message);
  });

  return mqttClientInstance;
}

export function getMQTTClient() {
  return mqttClientInstance;
}

