import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getAllReaders, getReaderByRfid, createReader } from '../../src/controllers/readerController.js';
import Reader from '../../src/models/Reader.js';
import Loan from '../../src/models/Loan.js';

vi.mock('../../src/models/Reader.js');
vi.mock('../../src/models/Loan.js');
vi.mock('../../src/models/AuditLog.js', () => ({
  default: {
    create: vi.fn().mockReturnValue(Promise.resolve({}))
  }
}));

describe('Unit Test: Reader Controller (Quản lý Bạn đọc & Thẻ RFID)', () => {
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

  describe('getAllReaders()', () => {
    it('phải trả về toàn bộ danh sách bạn đọc sắp xếp theo thời gian tạo mới nhất', async () => {
      const mockReaders = [
        { _id: 'r1', name: 'Nguyễn Văn A', studentId: 'B21DCCN001' },
        { _id: 'r2', name: 'Trần Thị B', studentId: 'B21DCCN002' }
      ];

      Reader.find.mockReturnValue({
        sort: vi.fn().mockResolvedValue(mockReaders)
      });

      await getAllReaders(req, res, next);

      expect(res.json).toHaveBeenCalledWith({
        success: true,
        data: mockReaders
      });
    });
  });

  describe('getReaderByRfid()', () => {
    it('phải trả về mã lỗi 404 khi không tìm thấy thẻ bạn đọc trong hệ thống', async () => {
      req.params.rfid = 'UNKNOWN_RFID';
      Reader.findOne.mockResolvedValue(null);

      await getReaderByRfid(req, res, next);

      expect(res.status).toHaveBeenCalledWith(404);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: false,
        message: expect.stringContaining('Không tìm thấy độc giả')
      }));
    });

    it('phải trả về đầy đủ hồ sơ bạn đọc, sách đang mượn và tổng nợ phạt chưa thanh toán', async () => {
      req.params.rfid = 'VALID_RFID_123';
      const mockReader = {
        _id: 'r1',
        name: 'Nguyễn Văn A',
        studentId: 'B21DCCN001',
        rfidCard: 'VALID_RFID_123'
      };

      Reader.findOne.mockResolvedValue(mockReader);

      const mockActiveLoans = [
        { _id: 'l1', status: 'borrowing', bookId: { title: 'Lập trình Web' } }
      ];
      const mockUnpaidLoans = [
        { _id: 'l2', fineAmount: 15000, fineStatus: 'unpaid', bookId: { title: 'IoT cơ bản' } }
      ];

      Loan.find
        .mockReturnValueOnce({ populate: vi.fn().mockResolvedValue(mockActiveLoans) })
        .mockReturnValueOnce({ populate: vi.fn().mockResolvedValue(mockUnpaidLoans) });

      await getReaderByRfid(req, res, next);

      expect(res.json).toHaveBeenCalledWith({
        success: true,
        data: expect.objectContaining({
          reader: mockReader,
          activeLoans: mockActiveLoans,
          unpaidLoans: mockUnpaidLoans,
          totalUnpaidFine: 15000,
          hasDebt: true
        })
      });
    });
  });

  describe('createReader()', () => {
    it('phải từ chối tạo mới khi MSSV hoặc Mã RFID đã tồn tại (400 Bad Request)', async () => {
      req.body = {
        studentId: 'B21DCCN001',
        name: 'Nguyễn Văn A',
        rfidCard: 'RFID_EXISTING'
      };

      Reader.findOne.mockResolvedValue({ _id: 'existing_id' });

      await createReader(req, res, next);

      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: false,
        message: expect.stringContaining('đã tồn tại')
      }));
    });

    it('phải tạo bạn đọc thành công khi thông tin hợp lệ (201 Created)', async () => {
      req.body = {
        studentId: 'B21DCCN999',
        name: 'Phạm Văn Mới',
        email: 'moi@ptit.edu.vn',
        rfidCard: 'NEW_RFID_999'
      };

      Reader.findOne.mockResolvedValue(null);
      const createdReader = { _id: 'r_new', ...req.body };
      Reader.create.mockResolvedValue(createdReader);

      await createReader(req, res, next);

      expect(res.status).toHaveBeenCalledWith(201);
      expect(res.json).toHaveBeenCalledWith({
        success: true,
        data: createdReader
      });
    });
  });
});
