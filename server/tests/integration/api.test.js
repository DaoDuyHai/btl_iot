import { describe, it, expect, vi, beforeEach } from 'vitest';
import request from 'supertest';
import app from '../../src/app.js';
import Book from '../../src/models/Book.js';

vi.mock('../../src/models/Book.js');
vi.mock('../../src/models/Reader.js');
vi.mock('../../src/models/DeviceLog.js');
vi.mock('../../src/models/Loan.js');
vi.mock('../../src/models/AuditLog.js');
vi.mock('../../src/mqtt/publisher.js', () => ({
  sendFeedback: vi.fn(),
  sendReboot: vi.fn()
}));

describe('Integration Test: REST API Endpoints với Supertest', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('GET /api/health', () => {
    it('phải trả về status: ok và thông tin dịch vụ (200 OK)', async () => {
      const res = await request(app).get('/api/health');
      expect(res.status).toBe(200);
      expect(res.body.status).toBe('ok');
      expect(res.body.service).toContain('Smart Library Kiosk');
    });
  });

  describe('GET /api/books', () => {
    it('phải trả về danh sách tài liệu từ cơ sở dữ liệu (200 OK)', async () => {
      const mockBooks = [
        { _id: 'b1', title: 'Lập trình Vi điều khiển ESP32', status: 'available' },
        { _id: 'b2', title: 'Kiến trúc Mạng IoT', status: 'available' }
      ];

      Book.find.mockReturnValue({
        sort: vi.fn().mockResolvedValue(mockBooks)
      });

      const res = await request(app).get('/api/books');
      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.data).toHaveLength(2);
      expect(res.body.data[0].title).toBe('Lập trình Vi điều khiển ESP32');
    });
  });

  describe('POST /api/loans/borrow validation', () => {
    it('phải trả về mã lỗi 400 khi thiếu readerId hoặc bookIds', async () => {
      const res = await request(app)
        .post('/api/loans/borrow')
        .send({ readerId: '', bookIds: [] });

      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
      expect(res.body.message).toContain('bắt buộc');
    });
  });

  describe('POST /api/loans/return-preview validation', () => {
    it('phải trả về mã lỗi 400 khi thiếu bookRfid', async () => {
      const res = await request(app)
        .post('/api/loans/return-preview')
        .send({});

      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
      expect(res.body.message).toContain('Vui lòng cung cấp bookRfid');
    });
  });

  describe('POST /api/loans/return-batch validation', () => {
    it('phải trả về mã lỗi 400 khi thiếu mảng bookRfids', async () => {
      const res = await request(app)
        .post('/api/loans/return-batch')
        .send({ bookRfids: [] });

      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
      expect(res.body.message).toContain('Danh sách bookRfids là bắt buộc');
    });
  });

  describe('POST /api/loans/inspect validation', () => {
    it('phải trả về mã lỗi 400 khi thiếu loanId hoặc result', async () => {
      const res = await request(app)
        .post('/api/loans/inspect')
        .send({ loanId: '' });

      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
      expect(res.body.message).toContain('bắt buộc');
    });
  });

  describe('POST /api/loans/manual-return validation', () => {
    it('phải trả về mã lỗi 400 khi thiếu loanId', async () => {
      const res = await request(app)
        .post('/api/loans/manual-return')
        .send({});

      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
      expect(res.body.message).toContain('Vui lòng cung cấp loanId');
    });
  });

  describe('POST /api/devices/:deviceId/command', () => {
    it('phải gửi thành công lệnh phản hồi phần cứng (Buzzer/LED) qua MQTT', async () => {
      const res = await request(app)
        .post('/api/devices/kiosk_01/command')
        .send({ action: 'feedback', status: 'success' });

      expect(res.status).toBe(200);
      expect(res.body.success).toBe(true);
      expect(res.body.message).toContain('kiosk_01');
    });

    it('phải từ chối khi action điều khiển không hợp lệ (400 Bad Request)', async () => {
      const res = await request(app)
        .post('/api/devices/kiosk_01/command')
        .send({ action: 'invalid_action' });

      expect(res.status).toBe(400);
      expect(res.body.success).toBe(false);
      expect(res.body.message).toContain('không hợp lệ');
    });
  });
});
