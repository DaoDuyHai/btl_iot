import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as loanService from '../../src/services/loanService.js';
import Reader from '../../src/models/Reader.js';
import Book from '../../src/models/Book.js';
import Loan from '../../src/models/Loan.js';

vi.mock('../../src/models/Reader.js');
vi.mock('../../src/models/Book.js');
vi.mock('../../src/models/Loan.js');
vi.mock('../../src/services/emailService.js', () => ({
  sendReceiptEmail: vi.fn().mockResolvedValue({ messageId: 'mock-mail-id' })
}));

describe('Unit Test: Mock Tầng Service Nghiệp Vụ Mượn/Trả (Không cần Database)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('borrowBatch() - Mượn sách theo lô', () => {
    it('phải chặn mượn nếu bạn đọc bị khóa tài khoản', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: false });

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1'] })
      ).rejects.toThrow('Độc giả không tồn tại hoặc tài khoản đã bị khóa');
    });

    it('phải chặn mượn nếu danh sách sách có phần tử trùng lặp', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: true });

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1', 'b1'] })
      ).rejects.toThrow('Danh sách tài liệu mượn có phần tử bị trùng lặp');
    });

    it('phải chặn mượn nếu bạn đọc đang có sách quá hạn chưa thanh toán', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: true });
      Loan.countDocuments.mockResolvedValueOnce(2); // Có 2 cuốn quá hạn

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1'] })
      ).rejects.toThrow(/quá hạn chưa hoàn trả/);
    });

    it('phải chặn mượn nếu vượt quá hạn mức tối đa 5 cuốn', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: true });
      Loan.countDocuments.mockResolvedValueOnce(0); // Không có sách quá hạn
      Loan.countDocuments.mockResolvedValueOnce(4); // Hiện đang mượn 4 cuốn

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1', 'b2'] }) // 4 + 2 = 6 > 5
      ).rejects.toThrow(/Vượt quá hạn mức mượn tài liệu/);
    });

    it('phải chặn mượn nếu cuốn sách đang ở trạng thái không khả dụng (borrowed)', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: true });
      Loan.countDocuments.mockResolvedValueOnce(0);
      Loan.countDocuments.mockResolvedValueOnce(1);
      Book.find.mockResolvedValue([
        { _id: 'b1', title: 'Lập trình IoT', status: 'borrowed' }
      ]);

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1'] })
      ).rejects.toThrow(/hiện không khả dụng/);
    });
  });

  describe('returnBookByRfid() - Trả sách và tính phạt VietQR', () => {
    it('phải trả về thông báo đã có sẵn trong kho nếu sách không có phiếu mượn active', async () => {
      Book.findOne.mockResolvedValue({ _id: 'b1', title: 'Mạng máy tính' });
      Loan.findOne.mockReturnValue({
        populate: vi.fn().mockResolvedValue(null)
      });

      const res = await loanService.returnBookByRfid('TAG_AVAILABLE');
      expect(res.alreadyReturned).toBe(true);
      expect(res.message).toContain('đã có sẵn trong thư viện');
    });

    it('phải tính đúng tiền phạt 15.000 VNĐ cho sách quá hạn 3 ngày và sinh mã VietQR', async () => {
      const mockBook = { _id: 'b1', title: 'Giáo trình IoT', status: 'borrowed', save: vi.fn() };
      const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000);
      const mockLoan = {
        _id: 'l1',
        dueDate: threeDaysAgo,
        readerId: { studentId: 'B21DCCN001', name: 'Trần Văn B' },
        save: vi.fn()
      };

      Book.findOne.mockResolvedValue(mockBook);
      Loan.findOne.mockReturnValue({
        populate: vi.fn().mockResolvedValue(mockLoan)
      });

      const res = await loanService.returnBookByRfid('TAG_OVERDUE');

      expect(res.isOverdue).toBe(true);
      expect(res.fineAmount).toBe(15000); // 3 ngày * 5000đ
      expect(res.isPaid).toBe(false);
      expect(res.vietQrUrl).toContain('amount=15000');
      expect(res.vietQrUrl).toContain('PHAT%20B21DCCN001');
    });

    it('phải hoàn tất trả sách ngay (fineAmount = 0, isPaid = true) khi sách còn hạn mượn', async () => {
      const mockBook = { _id: 'b1', title: 'Hệ thống nhúng', status: 'borrowed', save: vi.fn() };
      const fiveDaysLater = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000);
      const mockLoan = {
        _id: 'l2',
        dueDate: fiveDaysLater,
        readerId: { studentId: 'B21DCCN002', name: 'Lê Thị C' },
        save: vi.fn()
      };

      Book.findOne.mockResolvedValue(mockBook);
      Loan.findOne.mockReturnValue({
        populate: vi.fn().mockResolvedValue(mockLoan)
      });

      const res = await loanService.returnBookByRfid('TAG_ON_TIME');

      expect(res.isOverdue).toBe(false);
      expect(res.fineAmount).toBe(0);
      expect(res.isPaid).toBe(true);
      expect(res.vietQrUrl).toBeNull();
    });
  });

  describe('payFine() - Nộp phạt trực tuyến', () => {
    it('phải mở khóa phiếu mượn và đánh dấu đã nộp phạt thành công', async () => {
      const mockLoan = {
        _id: 'l1',
        fineAmount: 15000,
        isPaid: false,
        status: 'overdue',
        save: vi.fn()
      };

      Loan.findById.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue(mockLoan)
        })
      });

      const res = await loanService.payFine('l1');
      expect(res.success).toBe(true);
      expect(mockLoan.isPaid).toBe(true);
      expect(mockLoan.status).toBe('returned');
      expect(mockLoan.save).toHaveBeenCalled();
    });
  });
});

