import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getLogs, sendCommand } from '../../src/controllers/deviceController.js';
import DeviceLog from '../../src/models/DeviceLog.js';
import * as publisher from '../../src/mqtt/publisher.js';

vi.mock('../../src/models/DeviceLog.js');
vi.mock('../../src/mqtt/publisher.js', () => ({
  sendFeedback: vi.fn(),
  sendReboot: vi.fn()
}));

describe('Unit Test: Device Controller (Điều khiển Phần cứng IoT & Xem Logs)', () => {
  let req, res, next;

  beforeEach(() => {
    vi.clearAllMocks();
    req = { params: {}, body: {}, query: {} };
    res = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis()
    };
    next = vi.fn();
  });

  describe('getLogs()', () => {
    it('phải trả về danh sách lịch sử log thiết bị với limit mặc định 30', async () => {
      const mockLogs = [
        { deviceId: 'kiosk_01', type: 'HEARTBEAT', payload: { status: 'online' } }
      ];

      DeviceLog.find.mockReturnValue({
        sort: vi.fn().mockReturnValue({
          limit: vi.fn().mockResolvedValue(mockLogs)
        })
      });

      await getLogs(req, res, next);

      expect(res.json).toHaveBeenCalledWith({
        success: true,
        data: mockLogs
      });
    });
  });

  describe('sendCommand()', () => {
    it('phải gửi lệnh phản hồi (feedback buzzer/led) tới thiết bị kiosk', async () => {
      req.params.deviceId = 'kiosk_01';
      req.body = { action: 'feedback', status: 'success' };

      await sendCommand(req, res, next);

      expect(publisher.sendFeedback).toHaveBeenCalledWith('kiosk_01', 'success');
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        message: expect.stringContaining('kiosk_01')
      }));
    });

    it('phải gửi lệnh khởi động lại (reboot) tới thiết bị kiosk', async () => {
      req.params.deviceId = 'kiosk_01';
      req.body = { action: 'reboot' };

      await sendCommand(req, res, next);

      expect(publisher.sendReboot).toHaveBeenCalledWith('kiosk_01');
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        message: expect.stringContaining('reboot')
      }));
    });

    it('phải từ chối khi action điều khiển không hợp lệ (400 Bad Request)', async () => {
      req.params.deviceId = 'kiosk_01';
      req.body = { action: 'shutdown_system' };

      await sendCommand(req, res, next);

      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: false,
        message: expect.stringContaining('Action không hợp lệ')
      }));
    });
  });
});
