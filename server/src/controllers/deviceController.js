import DeviceLog from '../models/DeviceLog.js';
import { sendFeedback, sendReboot } from '../mqtt/publisher.js';

export async function getLogs(req, res, next) {
  try {
    const limit = parseInt(req.query.limit, 10) || 30;
    const logs = await DeviceLog.find().sort({ createdAt: -1 }).limit(limit);
    res.json({ success: true, data: logs });
  } catch (err) {
    next(err);
  }
}

export async function sendCommand(req, res, next) {
  try {
    const { deviceId } = req.params;
    const { action, status } = req.body;

    if (action === 'feedback') {
      sendFeedback(deviceId, status || 'success');
      return res.json({ success: true, message: `Đã gửi lệnh feedback (${status}) tới ${deviceId}` });
    }

    if (action === 'reboot') {
      sendReboot(deviceId);
      return res.json({ success: true, message: `Đã gửi lệnh reboot tới ${deviceId}` });
    }

    res.status(400).json({ success: false, message: 'Action không hợp lệ' });
  } catch (err) {
    next(err);
  }
}

