import mongoose from 'mongoose';
import Book from '../models/Book.js';
import AuditLog from '../models/AuditLog.js';

export async function getAllBooks(req, res, next) {
  try {
    const includeDeleted = req.query.includeDeleted === 'true';
    const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || 15, 1), 100);
    const cursor = req.query.cursor; // _id của bản ghi cuối trang trước (Cursor Pagination Pattern)
    const q = (req.query.q || '').trim();
    const category = (req.query.category || '').trim();
    const status = (req.query.status || '').trim();

    const filter = includeDeleted ? {} : { isDeleted: { $ne: true } };
    if (category) {
      const sanitizedCat = category.replace(/[-–—]/g, '[-–—]');
      filter.category = { $regex: new RegExp(`^${sanitizedCat}$`, 'i') };
    }
    if (status) filter.status = status;

    if (q) {
      filter.$or = [
        { title: { $regex: q, $options: 'i' } },
        { author: { $regex: q, $options: 'i' } },
        { bookId: { $regex: q, $options: 'i' } },
        { rfidTag: { $regex: q, $options: 'i' } }
      ];
    }

    // Áp dụng Keyset Cursor Pagination Pattern: Quét theo B-Tree Index (_id < cursor)
    if (cursor && mongoose.Types.ObjectId.isValid(cursor)) {
      filter._id = { $lt: new mongoose.Types.ObjectId(cursor) };
    }

    const isCursorPaginated = req.query.limit !== undefined || req.query.cursor !== undefined || req.query.q !== undefined || req.query.category !== undefined;

    let query = Book.find(filter).sort({ _id: -1 });

    if (isCursorPaginated && req.query.all !== 'true') {
      // Lấy limit + 1 để xác định hasMore mà không cần countDocuments tốn kém
      query = query.limit(limit + 1);
    }

    const books = await query;

    let resultBooks = books;
    let nextCursor = null;
    let hasMore = false;

    if (isCursorPaginated && req.query.all !== 'true') {
      hasMore = books.length > limit;
      resultBooks = hasMore ? books.slice(0, limit) : books;
      nextCursor = hasMore && resultBooks.length > 0 ? String(resultBooks[resultBooks.length - 1]._id) : null;
    }

    res.json({
      success: true,
      data: resultBooks,
      pagination: {
        limit: resultBooks.length,
        nextCursor,
        hasMore,
        totalInPage: resultBooks.length
      }
    });
  } catch (err) {
    next(err);
  }
}

export async function getBookByRfid(req, res, next) {
  try {
    const { rfid } = req.params;
    const book = await Book.findOne({ rfidTag: rfid, isDeleted: { $ne: true } });
    if (!book) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy sách với mã RFID này' });
    }
    res.json({ success: true, data: book });
  } catch (err) {
    next(err);
  }
}

export async function createBook(req, res, next) {
  try {
    const { isbn, title, author, category, rfidTag, copyCode, status } = req.body;
    const existing = await Book.findOne({ rfidTag, isDeleted: { $ne: true } });
    if (existing) {
      return res.status(400).json({ success: false, message: 'Mã RFID này đã được gán cho cuốn sách khác' });
    }

    const book = await Book.create({
      isbn,
      title,
      author,
      category,
      rfidTag,
      copyCode: copyCode || `CP-${Date.now().toString().slice(-4)}`,
      status: status || 'available'
    });

    await AuditLog.create({
      actor: 'Thủ thư',
      action: 'UPDATE_BOOK',
      targetType: 'Book',
      targetId: book._id,
      details: { actionType: 'CREATE', title: book.title, rfidTag: book.rfidTag }
    }).catch(() => {});

    res.status(201).json({ success: true, data: book });
  } catch (err) {
    next(err);
  }
}

export async function updateBook(req, res, next) {
  try {
    const { id } = req.params;
    const { isbn, title, author, category, rfidTag, copyCode, status, physicalCondition, inspectionNote } = req.body;

    const book = await Book.findById(id);
    if (!book) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy sách cần cập nhật' });
    }

    // Nếu đổi rfidTag thì kiểm tra trùng lặp
    if (rfidTag && rfidTag !== book.rfidTag) {
      const existing = await Book.findOne({ rfidTag, _id: { $ne: id }, isDeleted: { $ne: true } });
      if (existing) {
        return res.status(400).json({ success: false, message: 'Mã RFID mới đã tồn tại trên một tài liệu khác' });
      }
      book.rfidTag = rfidTag;
    }

    if (isbn !== undefined) book.isbn = isbn;
    if (title !== undefined) book.title = title;
    if (author !== undefined) book.author = author;
    if (category !== undefined) book.category = category;
    if (copyCode !== undefined) book.copyCode = copyCode;
    if (status !== undefined) book.status = status;
    if (physicalCondition !== undefined) book.physicalCondition = physicalCondition;
    if (inspectionNote !== undefined) book.inspectionNote = inspectionNote;

    await book.save();

    await AuditLog.create({
      actor: 'Thủ thư',
      action: 'UPDATE_BOOK',
      targetType: 'Book',
      targetId: book._id,
      details: { actionType: 'UPDATE', changes: req.body }
    }).catch(() => {});

    res.json({ success: true, data: book, message: 'Cập nhật tài liệu thành công' });
  } catch (err) {
    next(err);
  }
}

export async function deleteBook(req, res, next) {
  try {
    const { id } = req.params;
    const book = await Book.findById(id);
    if (!book) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy tài liệu' });
    }

    // Xóa mềm (Soft Delete) theo Mục 2.2 STT 7
    book.isDeleted = true;
    book.status = 'inactive';
    await book.save();

    await AuditLog.create({
      actor: 'Thủ thư',
      action: 'UPDATE_BOOK',
      targetType: 'Book',
      targetId: book._id,
      details: { actionType: 'SOFT_DELETE', title: book.title }
    }).catch(() => {});

    res.json({ success: true, message: 'Đã ngừng sử dụng tài liệu thành công (Xóa mềm)' });
  } catch (err) {
    next(err);
  }
}
