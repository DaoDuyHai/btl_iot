import Book from '../models/Book.js';
import AuditLog from '../models/AuditLog.js';

export async function getAllBooks(req, res, next) {
  try {
    const includeDeleted = req.query.includeDeleted === 'true';
    const filter = includeDeleted ? {} : { isDeleted: { $ne: true } };
    const books = await Book.find(filter).sort({ createdAt: -1 });
    res.json({ success: true, data: books });
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
