import { getMQTTClient } from './client.js';

export function sendFeedback(deviceId, status = 'success') {
  const client = getMQTTClient();
  if (!client || !client.connected) return false;

  const payload = JSON.stringify({ action: 'feedback', status });
  client.publish(`kiosk/${deviceId}/command`, payload);

  // Đồng bộ cả kiosk-01 và kiosk_01 để đảm bảo tương thích mọi firmware và simulator
  const altId = deviceId.includes('-') ? deviceId.replace(/-/g, '_') : deviceId.replace(/_/g, '-');
  if (altId !== deviceId) {
    client.publish(`kiosk/${altId}/command`, payload);
  }
  return true;
}

export function sendReboot(deviceId) {
  const client = getMQTTClient();
  if (!client || !client.connected) return false;

  const payload = JSON.stringify({ action: 'reboot' });
  client.publish(`kiosk/${deviceId}/command`, payload);

  const altId = deviceId.includes('-') ? deviceId.replace(/-/g, '_') : deviceId.replace(/_/g, '-');
  if (altId !== deviceId) {
    client.publish(`kiosk/${altId}/command`, payload);
  }
  return true;
}

