import DeviceLog from '../../models/DeviceLog.js';
import { emitToAll } from '../../sockets/index.js';

let lastStatus = {};

export async function handleDeviceStatus(deviceId, payload) {
  const { status, rssi, uptime } = payload;
  const isStateChanged = lastStatus[deviceId] !== status;
  lastStatus[deviceId] = status;

  // Đẩy realtime lên giao diện Admin / Kiosk
  emitToAll('device:status', {
    deviceId,
    status: status || 'offline',
    rssi: rssi || null,
    uptime: uptime || null,
    updatedAt: new Date()
  });

  if (isStateChanged || status === 'offline') {
    console.log(`📡 [Device Status] Kiosk ${deviceId} thay đổi trạng thái: ${status}`);
    try {
      await DeviceLog.create({
        deviceId,
        event: status === 'online' ? 'heartbeat' : 'offline',
        rssi,
        uptime,
        payload
      });
    } catch (err) {}
  }
}

