import { describe, it, expect, vi, beforeEach } from 'vitest';
import { searchBooks, recommendBooks, getAiStats, chatWithAgent } from '../../src/controllers/aiController.js';
import Book from '../../src/models/Book.js';
import Reader from '../../src/models/Reader.js';

vi.mock('../../src/models/Book.js');
vi.mock('../../src/models/Reader.js');

describe('Unit Test: AI Gateway Controller (Search & Recommendation)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('searchBooks()', () => {
    it('phải trả về 400 nếu query rỗng', async () => {
      const req = { query: { q: '   ' } };
      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn()
      };
      const next = vi.fn();

      await searchBooks(req, res, next);
      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: false,
        message: expect.stringContaining('không được để trống')
      }));
    });

    it('phải tự động fallback sang Catalog Precision an toàn khi AI Service offline', async () => {
      const req = { query: { q: 'Lập trình ESP32' } };
      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn()
      };
      const next = vi.fn();

      await searchBooks(req, res, next);

      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        source: 'catalog_precision_search'
      }));
    });
  });

  describe('recommendBooks()', () => {
    it('phải lấy department từ Reader nếu có studentId và fallback an toàn', async () => {
      const req = { query: { studentId: 'B21DCCN001' } };
      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn()
      };
      const next = vi.fn();

      Reader.findOne.mockResolvedValue({
        studentId: 'B21DCCN001',
        department: 'Khoa Công Nghệ Thông Tin 1 - PTIT'
      });

      Book.find.mockReturnValue({
        limit: vi.fn().mockResolvedValue([
          {
            bookId: 'B0001',
            title: 'Khoa học máy tính',
            status: 'available'
          }
        ])
      });

      await recommendBooks(req, res, next);

      expect(Reader.findOne).toHaveBeenCalledWith({ studentId: 'B21DCCN001' });
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        department: 'Khoa Công Nghệ Thông Tin 1 - PTIT'
      }));
    });
  });

  describe('getAiStats()', () => {
    it('phải trả về thống kê sách từ MongoDB nếu AI Service chưa khởi động', async () => {
      const req = {};
      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn()
      };

      Book.countDocuments.mockResolvedValue(3000);

      await getAiStats(req, res, vi.fn());

      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        isAiOnline: false,
        total_records: 3000
      }));
    });
  });

  describe('chatWithAgent()', () => {
    it('phải trả về 400 nếu tin nhắn rỗng', async () => {
      const req = { body: { message: '   ' } };
      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn()
      };
      await chatWithAgent(req, res, vi.fn());
      expect(res.status).toHaveBeenCalledWith(400);
    });

    it('phải tự động suy luận bằng Local Semantic Reasoner và trả về sách phù hợp', async () => {
      const req = {
        body: {
          message: 'Dạo này em rất stress và mất ngủ vì thi cử'
        }
      };
      const res = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn()
      };

      await chatWithAgent(req, res, vi.fn());

      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        source: 'local_smart_agent',
        reply: expect.stringContaining('thấu hiểu cảm xúc'),
        books: expect.arrayContaining([
          expect.objectContaining({
            category: expect.stringContaining('Phát triển bản thân')
          })
        ])
      }));
    });
  });
});
