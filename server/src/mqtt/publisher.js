import { getMQTTClient } from './client.js';

export function sendFeedback(deviceId, status = 'success') {
  const client = getMQTTClient();
  if (!client || !client.connected) return false;

  const topic = `kiosk/${deviceId}/command`;
  const payload = JSON.stringify({ action: 'feedback', status });
  client.publish(topic, payload);
  return true;
}

export function sendReboot(deviceId) {
  const client = getMQTTClient();
  if (!client || !client.connected) return false;

  const topic = `kiosk/${deviceId}/command`;
  const payload = JSON.stringify({ action: 'reboot' });
  client.publish(topic, payload);
  return true;
}

