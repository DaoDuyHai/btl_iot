import { describe, it, expect, vi, beforeEach } from 'vitest';
import { handleCardScan } from '../../src/mqtt/handlers/cardScan.js';
import { handleDeviceStatus } from '../../src/mqtt/handlers/deviceStatus.js';
import { sendFeedback } from '../../src/mqtt/publisher.js';
import Reader from '../../src/models/Reader.js';
import Book from '../../src/models/Book.js';
import Loan from '../../src/models/Loan.js';
import DeviceLog from '../../src/models/DeviceLog.js';
import * as socketModule from '../../src/sockets/index.js';

vi.mock('../../src/models/Reader.js');
vi.mock('../../src/models/Book.js');
vi.mock('../../src/models/Loan.js');
vi.mock('../../src/models/DeviceLog.js');
vi.mock('../../src/sockets/index.js', () => ({
  emitToAll: vi.fn()
}));
vi.mock('../../src/mqtt/publisher.js', () => ({
  sendFeedback: vi.fn(),
  sendReboot: vi.fn()
}));

describe('Unit Test: MQTT Message Handlers (IoT Layer)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('handleCardScan() - Xử lý quẹt thẻ RFID từ phần cứng', () => {
    it('phải xác thực thành công thẻ độc giả và phát sự kiện READER_AUTHENTICATED', async () => {
      const mockReader = { _id: 'r1', name: 'Trần Văn B', studentId: 'B21DCCN001', active: true };
      Reader.findOne.mockResolvedValue(mockReader);
      Loan.find.mockReturnValue({
        populate: vi.fn().mockResolvedValue([])
      });
      DeviceLog.create.mockResolvedValue({});

      await handleCardScan('kiosk_01', { uid: 'READER_UID_TEST_1' });

      expect(socketModule.emitToAll).toHaveBeenCalledWith('kiosk:event', expect.objectContaining({
        type: 'READER_AUTHENTICATED',
        data: expect.objectContaining({ reader: mockReader, hasDebt: false })
      }));
      expect(sendFeedback).toHaveBeenCalledWith('kiosk_01', 'success');
    });

    it('phải chặn thẻ độc giả bị khóa, phát tín hiệu lỗi phần cứng và phát sự kiện READER_LOCKED', async () => {
      const mockLockedReader = { _id: 'r2', name: 'Lê Văn C', studentId: 'B21DCCN002', active: false };
      Reader.findOne.mockResolvedValue(mockLockedReader);
      DeviceLog.create.mockResolvedValue({});

      await handleCardScan('kiosk_01', { uid: 'LOCKED_UID_TEST' });

      expect(socketModule.emitToAll).toHaveBeenCalledWith('kiosk:event', expect.objectContaining({
        type: 'READER_LOCKED'
      }));
      expect(sendFeedback).toHaveBeenCalledWith('kiosk_01', 'error');
    });

    it('phải bỏ qua quét trùng lặp UID nếu diễn ra trong khoảng cooldown 1000ms', async () => {
      const mockReader = { _id: 'r3', name: 'Độc giả 3', active: true };
      Reader.findOne.mockResolvedValue(mockReader);
      Loan.find.mockReturnValue({
        populate: vi.fn().mockResolvedValue([])
      });

      // Lần 1: Được xử lý
      await handleCardScan('kiosk_01', { uid: 'DEBOUNCE_UID_TEST' });
      expect(sendFeedback).toHaveBeenCalledTimes(1);

      // Lần 2: Ngay lập tức cùng UID -> Bị debounce bỏ qua
      await handleCardScan('kiosk_01', { uid: 'DEBOUNCE_UID_TEST' });
      expect(sendFeedback).toHaveBeenCalledTimes(1);
    });

    it('phải nhận diện đúng thẻ sách và phát sự kiện BOOK_SCANNED', async () => {
      Reader.findOne.mockResolvedValue(null); // Không phải thẻ độc giả
      const mockBook = { _id: 'b1', title: 'Lập trình nhúng ESP32', status: 'available' };
      Book.findOne.mockResolvedValue(mockBook);
      Loan.findOne.mockReturnValue({
        populate: vi.fn().mockResolvedValue(null)
      });
      DeviceLog.create.mockResolvedValue({});

      await handleCardScan('kiosk_01', { uid: 'BOOK_UID_TEST_1' });

      expect(socketModule.emitToAll).toHaveBeenCalledWith('kiosk:event', expect.objectContaining({
        type: 'BOOK_SCANNED',
        data: expect.objectContaining({ book: mockBook, isAvailable: true })
      }));
      expect(sendFeedback).toHaveBeenCalledWith('kiosk_01', 'success');
    });

    it('phải phát sự kiện UNKNOWN_CARD và báo lỗi phần cứng nếu UID chưa đăng ký', async () => {
      Reader.findOne.mockResolvedValue(null);
      Book.findOne.mockResolvedValue(null);
      DeviceLog.create.mockResolvedValue({});

      await handleCardScan('kiosk_01', { uid: 'UNKNOWN_UID_TEST' });

      expect(socketModule.emitToAll).toHaveBeenCalledWith('kiosk:event', expect.objectContaining({
        type: 'UNKNOWN_CARD',
        data: { uid: 'UNKNOWN_UID_TEST' }
      }));
      expect(sendFeedback).toHaveBeenCalledWith('kiosk_01', 'error');
    });
  });

  describe('handleDeviceStatus() - Xử lý nhịp tim Heartbeat thiết bị', () => {
    it('phải cập nhật trạng thái online và phát socket device:status', async () => {
      DeviceLog.create.mockResolvedValue({});

      await handleDeviceStatus('kiosk_01', { status: 'online', rssi: -62, uptime: 300 });

      expect(socketModule.emitToAll).toHaveBeenCalledWith('device:status', expect.objectContaining({
        deviceId: 'kiosk_01',
        status: 'online',
        rssi: -62,
        uptime: 300
      }));
    });
  });
});
