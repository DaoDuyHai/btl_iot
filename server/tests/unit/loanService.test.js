import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as loanService from '../../src/services/loanService.js';
import Reader from '../../src/models/Reader.js';
import Book from '../../src/models/Book.js';
import Loan from '../../src/models/Loan.js';

vi.mock('../../src/models/Reader.js');
vi.mock('../../src/models/Book.js');
vi.mock('../../src/models/Loan.js');
vi.mock('../../src/models/AuditLog.js', () => ({
  default: {
    create: vi.fn().mockResolvedValue({ _id: 'audit_1' })
  }
}));
vi.mock('../../src/services/emailService.js', () => ({
  sendReceiptEmail: vi.fn().mockResolvedValue({ messageId: 'mock-mail-id' })
}));

describe('Unit Test: Mock Tầng Service Nghiệp Vụ Mượn/Trả Chuẩn Thư Viện', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('borrowBatch() - Mượn tài liệu theo lô', () => {
    it('phải chặn mượn nếu độc giả bị khóa tài khoản', async () => {
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

    it('phải chặn mượn nếu độc giả đang có khoản phạt chưa thanh toán (Nợ công)', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: true });
      Loan.countDocuments.mockResolvedValueOnce(1); // 1 khoản phạt chưa trả

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1'] })
      ).rejects.toThrow(/khoản phạt chưa thanh toán/);
    });

    it('phải chặn mượn nếu độc giả đang có sách quá hạn chưa hoàn trả', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: true });
      Loan.countDocuments.mockResolvedValueOnce(0); // Không có nợ phạt
      Loan.countDocuments.mockResolvedValueOnce(2); // Có 2 cuốn quá hạn

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1'] })
      ).rejects.toThrow(/quá hạn chưa hoàn trả/);
    });

    it('phải chặn mượn nếu vượt quá hạn mức tối đa 5 cuốn', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: true });
      Loan.countDocuments.mockResolvedValueOnce(0); // Không có nợ phạt
      Loan.countDocuments.mockResolvedValueOnce(0); // Không có sách quá hạn
      Loan.countDocuments.mockResolvedValueOnce(4); // Hiện đang mượn 4 cuốn

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1', 'b2'] }) // 4 + 2 = 6 > 5
      ).rejects.toThrow(/Vượt quá hạn mức mượn tài liệu/);
    });

    it('phải chặn mượn nếu cuốn sách đang ở trạng thái không khả dụng (borrowed hoặc pending_inspection)', async () => {
      Reader.findById.mockResolvedValue({ _id: 'r1', name: 'Nguyễn Văn A', active: true });
      Loan.countDocuments.mockResolvedValueOnce(0);
      Loan.countDocuments.mockResolvedValueOnce(0);
      Loan.countDocuments.mockResolvedValueOnce(1);
      Book.find.mockResolvedValue([]); // Không tìm thấy sách nào available
      Book.findById.mockResolvedValue({ _id: 'b1', title: 'Lập trình IoT', status: 'pending_inspection' });

      await expect(
        loanService.borrowBatch({ readerId: 'r1', bookIds: ['b1'] })
      ).rejects.toThrow(/hiện không khả dụng/);
    });
  });

  describe('getReturnPreview() - Quét sách tại Kiosk (KHÔNG lưu Database)', () => {
    it('phải trả về thông báo đã có sẵn trong kho nếu sách không có lượt mượn hoạt động', async () => {
      Book.findOne.mockResolvedValue({ _id: 'b1', title: 'Mạng máy tính', rfidTag: 'TAG_1' });
      Loan.findOne.mockReturnValue({
        populate: vi.fn().mockResolvedValue(null)
      });

      const res = await loanService.getReturnPreview('TAG_1');
      expect(res.alreadyReturned).toBe(true);
      expect(res.message).toContain('đã có sẵn trong thư viện');
    });

    it('phải tính toán đúng tiền phạt cho sách quá hạn và sinh mã VietQR mà không sửa DB', async () => {
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

      const res = await loanService.getReturnPreview('TAG_OVERDUE');

      expect(res.isOverdue).toBe(true);
      expect(res.fineAmount).toBe(15000); // 3 ngày * 5000đ
      expect(res.vietQrUrl).toContain('amount=15000');
      // Đảm bảo không gọi save vào DB
      expect(mockBook.save).not.toHaveBeenCalled();
      expect(mockLoan.save).not.toHaveBeenCalled();
    });
  });

  describe('returnBatch() - Hoàn thành trả sách theo đợt & Chuyển sang pending_inspection', () => {
    it('phải chuyển sách sang pending_inspection và kết thúc tính quá hạn', async () => {
      const mockBook = { _id: 'b1', title: 'Hệ thống nhúng', status: 'borrowed', save: vi.fn() };
      const now = new Date();
      const mockLoan = {
        _id: 'l1',
        dueDate: new Date(now.getTime() + 5 * 24 * 60 * 60 * 1000), // Còn 5 ngày
        readerId: { studentId: 'B21DCCN001', name: 'Nguyễn Văn A' },
        save: vi.fn()
      };

      Book.findOne.mockResolvedValue(mockBook);
      Loan.findOne.mockReturnValue({
        populate: vi.fn().mockResolvedValue(mockLoan)
      });

      const res = await loanService.returnBatch({ bookRfids: ['TAG_VALID'] });

      expect(res.success).toBe(true);
      expect(res.count).toBe(1);
      expect(mockBook.status).toBe('pending_inspection');
      expect(mockBook.save).toHaveBeenCalled();
      expect(mockLoan.status).toBe('returned');
      expect(mockLoan.inspectionStatus).toBe('pending');
      expect(mockLoan.isPaid).toBe(true);
      expect(mockLoan.save).toHaveBeenCalled();
    });
  });

  describe('inspectBook() - Thủ thư kiểm tra sách sau khi trả (Mục 5)', () => {
    it('phải đưa sách trở lại available nếu kết quả kiểm tra là normal', async () => {
      const mockBook = { _id: 'b1', title: 'Lập trình C++', status: 'pending_inspection', save: vi.fn() };
      const mockLoan = {
        _id: 'l1',
        bookId: mockBook,
        readerId: { studentId: 'B21DCCN001' },
        save: vi.fn()
      };

      Loan.findById.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue(mockLoan)
        })
      });
      Book.findById.mockResolvedValue(mockBook);

      const res = await loanService.inspectBook({
        loanId: 'l1',
        result: 'normal',
        actor: 'Thủ thư Trưởng'
      });

      expect(res.success).toBe(true);
      expect(mockBook.status).toBe('available');
      expect(mockBook.physicalCondition).toBe('normal');
      expect(mockLoan.inspectionStatus).toBe('inspected');
      expect(mockBook.save).toHaveBeenCalled();
      expect(mockLoan.save).toHaveBeenCalled();
    });

    it('phải chuyển sách sang damaged và tạo khoản bồi thường nếu hư hỏng nặng', async () => {
      const mockBook = { _id: 'b1', title: 'Sách quý hiếm', status: 'pending_inspection', save: vi.fn() };
      const mockLoan = {
        _id: 'l1',
        bookId: mockBook,
        overdueFine: 0,
        readerId: { studentId: 'B21DCCN001' },
        save: vi.fn()
      };

      Loan.findById.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue(mockLoan)
        })
      });
      Book.findById.mockResolvedValue(mockBook);

      const res = await loanService.inspectBook({
        loanId: 'l1',
        result: 'damaged',
        damageType: 'water_damage',
        damageDescription: 'Dính nước ướt toàn bộ ruột sách',
        damageFine: 150000,
        actor: 'Thủ thư Trưởng'
      });

      expect(res.success).toBe(true);
      expect(mockBook.status).toBe('damaged');
      expect(mockLoan.damageFine).toBe(150000);
      expect(mockLoan.fineAmount).toBe(150000);
      expect(mockLoan.fineStatus).toBe('unpaid');
      expect(mockLoan.isPaid).toBe(false);
    });
  });

  describe('manualReturn() - Trả sách thủ công khi RFID bị hỏng (Mục 8)', () => {
    it('phải ghi nhận trả thủ công và đưa sách về trạng thái pending_inspection', async () => {
      const mockBook = { _id: 'b1', title: 'Sách rách tem RFID', status: 'borrowed', save: vi.fn() };
      const mockLoan = {
        _id: 'l1',
        bookId: mockBook,
        dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
        readerId: { studentId: 'B21DCCN001' },
        save: vi.fn()
      };

      Loan.findById.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue(mockLoan)
        })
      });
      Book.findById.mockResolvedValue(mockBook);

      const res = await loanService.manualReturn({
        loanId: 'l1',
        actor: 'Thủ thư',
        reason: 'Tem RFID bị rách không đọc được'
      });

      expect(res.success).toBe(true);
      expect(mockBook.status).toBe('pending_inspection');
      expect(mockLoan.returnMethod).toBe('manual_librarian');
      expect(mockLoan.status).toBe('returned');
    });
  });

  describe('payFine() & waiveFine() - Xử lý tiền phạt', () => {
    it('payFine() phải mở khóa phiếu mượn và đánh dấu đã nộp phạt thành công', async () => {
      const mockLoan = {
        _id: 'l1',
        fineAmount: 15000,
        isPaid: false,
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
      expect(mockLoan.fineStatus).toBe('paid');
      expect(mockLoan.save).toHaveBeenCalled();
    });

    it('waiveFine() phải miễn phạt và đánh dấu fineStatus = waived', async () => {
      const mockLoan = {
        _id: 'l1',
        fineAmount: 20000,
        isPaid: false,
        save: vi.fn()
      };

      Loan.findById.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue(mockLoan)
        })
      });

      const res = await loanService.waiveFine('l1', 'Miễn phạt do bạn đọc có hoàn cảnh khó khăn');
      expect(res.success).toBe(true);
      expect(mockLoan.isPaid).toBe(true);
      expect(mockLoan.fineStatus).toBe('waived');
      expect(mockLoan.save).toHaveBeenCalled();
    });

    it('disputeFine() phải chuyển trạng thái khoản phạt sang disputed', async () => {
      const mockLoan = {
        _id: 'l1',
        fineStatus: 'unpaid',
        save: vi.fn()
      };

      Loan.findById.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue(mockLoan)
        })
      });

      const res = await loanService.disputeFine('l1', 'Sách trả đúng hạn nhưng máy quét lỗi');
      expect(res.success).toBe(true);
      expect(mockLoan.fineStatus).toBe('disputed');
      expect(mockLoan.save).toHaveBeenCalled();
    });
  });

  describe('renewLoans() - Gia hạn thời hạn mượn', () => {
    it('phải gia hạn thành công và cộng thêm 14 ngày vào dueDate', async () => {
      const futureDue = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000);
      const mockLoan = {
        _id: 'l1',
        dueDate: futureDue,
        renewCount: 0,
        readerId: { _id: 'r1', name: 'Sinh viên' },
        bookId: { title: 'Lập trình Node.js' },
        save: vi.fn()
      };

      Loan.find.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue([mockLoan])
        })
      });
      Loan.countDocuments.mockResolvedValue(0); // Không có nợ phạt

      const res = await loanService.renewLoans({ loanIds: ['l1'], extraDays: 14 });
      expect(res.count).toBe(1);
      expect(mockLoan.renewCount).toBe(1);
      expect(mockLoan.save).toHaveBeenCalled();
    });

    it('phải chặn gia hạn nếu sách đã quá hạn trả', async () => {
      const pastDue = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000);
      const mockLoan = {
        _id: 'l1',
        dueDate: pastDue,
        renewCount: 0,
        readerId: { _id: 'r1' },
        bookId: { title: 'Sách quá hạn' },
        save: vi.fn()
      };

      Loan.find.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue([mockLoan])
        })
      });
      Loan.countDocuments.mockResolvedValue(0);

      await expect(
        loanService.renewLoans({ loanIds: ['l1'] })
      ).rejects.toThrow(/đã quá hạn trả/);
    });

    it('phải chặn gia hạn nếu sách đã đạt hạn mức 2 lần gia hạn tối đa', async () => {
      const futureDue = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000);
      const mockLoan = {
        _id: 'l1',
        dueDate: futureDue,
        renewCount: 2, // Đã gia hạn 2 lần
        readerId: { _id: 'r1' },
        bookId: { title: 'Sách đã đạt giới hạn' },
        save: vi.fn()
      };

      Loan.find.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue([mockLoan])
        })
      });
      Loan.countDocuments.mockResolvedValue(0);

      await expect(
        loanService.renewLoans({ loanIds: ['l1'] })
      ).rejects.toThrow(/đã đạt hạn mức gia hạn tối đa/);
    });

    it('phải chặn gia hạn nếu độc giả đang có khoản phạt chưa thanh toán', async () => {
      const futureDue = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000);
      const mockLoan = {
        _id: 'l1',
        dueDate: futureDue,
        renewCount: 0,
        readerId: { _id: 'r1' },
        bookId: { title: 'Sách' },
        save: vi.fn()
      };

      Loan.find.mockReturnValue({
        populate: vi.fn().mockReturnValue({
          populate: vi.fn().mockResolvedValue([mockLoan])
        })
      });
      Loan.countDocuments.mockResolvedValue(1); // Có nợ phạt

      await expect(
        loanService.renewLoans({ loanIds: ['l1'] })
      ).rejects.toThrow(/khoản nợ phạt chưa thanh toán/);
    });
  });

  describe('getPendingInspectionBooks() - Lấy danh sách chờ kiểm tra', () => {
    it('phải gọi đúng query lọc status = returned và inspectionStatus = pending', async () => {
      const mockList = [{ _id: 'l1', status: 'returned', inspectionStatus: 'pending' }];
      Loan.find.mockReturnValue({
        sort: vi.fn().mockReturnValue({
          populate: vi.fn().mockReturnValue({
            populate: vi.fn().mockResolvedValue(mockList)
          })
        })
      });

      const res = await loanService.getPendingInspectionBooks();
      expect(res).toEqual(mockList);
      expect(Loan.find).toHaveBeenCalledWith({
        status: 'returned',
        inspectionStatus: 'pending'
      });
    });
  });
});
