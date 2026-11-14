import { describe, it, expect, vi, beforeEach } from 'vitest';
import mongoose from 'mongoose';
import { getAllBooks } from '../../src/controllers/bookController.js';
import Book from '../../src/models/Book.js';

describe('Unit Test: Book Controller (Keyset Cursor Pagination)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('phải phân trang thành công với limit và trả về hasMore, nextCursor', async () => {
    const fakeBooks = Array.from({ length: 16 }, (_, i) => ({
      _id: new mongoose.Types.ObjectId(),
      title: `Sách số ${i + 1}`,
      author: 'Tác giả A',
      category: 'Công nghệ thông tin',
      rfidTag: `RFID_${i + 1}`,
      isDeleted: false
    }));

    // Mock Book.find chain: .sort().limit()
    const sortMock = vi.fn().mockReturnThis();
    const limitMock = vi.fn().mockResolvedValue(fakeBooks);
    vi.spyOn(Book, 'find').mockReturnValue({
      sort: sortMock,
      limit: limitMock
    });

    const req = {
      query: { limit: '15' }
    };
    const res = {
      json: vi.fn()
    };
    const next = vi.fn();

    await getAllBooks(req, res, next);

    expect(Book.find).toHaveBeenCalled();
    expect(res.json).toHaveBeenCalled();
    const responseData = res.json.mock.calls[0][0];

    expect(responseData.success).toBe(true);
    expect(responseData.data).toHaveLength(15);
    expect(responseData.pagination.hasMore).toBe(true);
    expect(responseData.pagination.nextCursor).toBe(String(fakeBooks[14]._id));
  });

  it('phải áp dụng filter _id < cursor khi truyền cursor hợp lệ', async () => {
    const targetCursor = new mongoose.Types.ObjectId();
    const fakeBooks = [
      { _id: new mongoose.Types.ObjectId(), title: 'Trang 2 Sách 1', isDeleted: false }
    ];

    const sortMock = vi.fn().mockReturnThis();
    const limitMock = vi.fn().mockResolvedValue(fakeBooks);
    const findSpy = vi.spyOn(Book, 'find').mockReturnValue({
      sort: sortMock,
      limit: limitMock
    });

    const req = {
      query: { limit: '15', cursor: targetCursor.toString() }
    };
    const res = {
      json: vi.fn()
    };
    const next = vi.fn();

    await getAllBooks(req, res, next);

    expect(findSpy).toHaveBeenCalled();
    const appliedFilter = findSpy.mock.calls[0][0];
    expect(appliedFilter._id).toEqual({ $lt: targetCursor });
    expect(res.json).toHaveBeenCalled();
  });

  it('phải chuẩn hóa category tìm kiếm hỗ trợ cả gạch ngang en-dash và hyphen', async () => {
    const fakeBooks = [
      { _id: new mongoose.Types.ObjectId(), title: 'Kinh tế vĩ mô', category: 'Kinh tế – Kinh doanh', isDeleted: false }
    ];

    const sortMock = vi.fn().mockReturnThis();
    const limitMock = vi.fn().mockResolvedValue(fakeBooks);
    const findSpy = vi.spyOn(Book, 'find').mockReturnValue({
      sort: sortMock,
      limit: limitMock
    });

    const req = {
      query: { category: 'Kinh tế - Kinh doanh' }
    };
    const res = {
      json: vi.fn()
    };
    const next = vi.fn();

    await getAllBooks(req, res, next);

    expect(findSpy).toHaveBeenCalled();
    const appliedFilter = findSpy.mock.calls[0][0];
    expect(appliedFilter.category.$regex).toBeInstanceOf(RegExp);
  });
});
