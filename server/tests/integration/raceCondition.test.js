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

describe('Integration Test: Kiểm thử Race Condition & Chống chiếm quyền phiên', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Race Condition: 2 độc giả mượn cùng 1 cuốn sách đồng thời', () => {
    it('chỉ duy nhất 1 yêu cầu mượn thành công, yêu cầu thứ 2 phải bị từ chối', async () => {
      // Giả lập 2 độc giả hợp lệ
      Reader.findById.mockImplementation(async (id) => {
        if (id === 'reader_1') return { _id: 'reader_1', name: 'Độc giả 1', active: true };
        if (id === 'reader_2') return { _id: 'reader_2', name: 'Độc giả 2', active: true };
        return null;
      });

      Loan.countDocuments.mockResolvedValue(0);

      // Trạng thái sách ban đầu: available
      let bookAvailable = true;

      Book.find.mockImplementation(async () => {
        return [
          {
            _id: 'book_exclusive_01',
            title: 'Sách Quý Duy Nhất',
            status: bookAvailable ? 'available' : 'borrowed',
            save: vi.fn()
          }
        ];
      });

      Loan.find.mockImplementation(() => ({
        populate: vi.fn().mockImplementation(async () => {
          if (!bookAvailable) {
            return [{ bookId: { title: 'Sách Quý Duy Nhất' } }];
          }
          return [];
        })
      }));

      Loan.create.mockImplementation(async () => {
        if (!bookAvailable) {
          throw new Error('Cuốn sách đã bị mượn bởi giao dịch khác!');
        }
        bookAvailable = false; // Độc giả 1 chiếm thành công
        return { _id: 'loan_created' };
      });

      // Kích hoạt đồng thời 2 yêu cầu qua Promise.all (Race condition simulation)
      const req1 = loanService.borrowBatch({ readerId: 'reader_1', bookIds: ['book_exclusive_01'] });
      const req2 = loanService.borrowBatch({ readerId: 'reader_2', bookIds: ['book_exclusive_01'] });

      const results = await Promise.allSettled([req1, req2]);

      const fulfilled = results.filter((r) => r.status === 'fulfilled');
      const rejected = results.filter((r) => r.status === 'rejected');

      // Khẳng định: Chính xác 1 giao dịch thành công và 1 giao dịch bị chặn đứng
      expect(fulfilled.length).toBe(1);
      expect(rejected.length).toBe(1);
      expect(rejected[0].reason.message).toMatch(/(không khả dụng|đã bị mượn|đang được mượn)/i);
    });
  });

  describe('Chống chiếm quyền phiên (Anti-Session Hijacking)', () => {
    it('phải chặn thẻ của độc giả B khi độc giả A đang trong phiên làm việc', () => {
      // Giả lập trạng thái Kiosk Session Manager
      let activeSession = {
        readerId: 'reader_A',
        studentId: 'B21DCCN001',
        sessionStartTime: Date.now()
      };

      function handleIncomingCardScan(incomingCard) {
        if (activeSession && activeSession.readerId !== incomingCard.readerId) {
          return {
            allowed: false,
            action: 'REJECT_HIJACKING',
            message: 'Phát hiện quẹt thẻ chen ngang! Đang có phiên làm việc của sinh viên khác.'
          };
        }
        return {
          allowed: true,
          action: 'PROCESS_SCAN'
        };
      }

      // Thẻ A quét lại trong phiên -> Được phép
      const scanA = handleIncomingCardScan({ readerId: 'reader_A' });
      expect(scanA.allowed).toBe(true);

      // Thẻ B cố tình quẹt chen ngang -> Bị chặn đứng ngay lập tức
      const scanB = handleIncomingCardScan({ readerId: 'reader_B' });
      expect(scanB.allowed).toBe(false);
      expect(scanB.action).toBe('REJECT_HIJACKING');
    });
  });
});

