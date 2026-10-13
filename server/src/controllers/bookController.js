import Book from '../models/Book.js';

export async function getAllBooks(req, res, next) {
  try {
    const books = await Book.find().sort({ createdAt: -1 });
    res.json({ success: true, data: books });
  } catch (err) {
    next(err);
  }
}

export async function getBookByRfid(req, res, next) {
  try {
    const { rfid } = req.params;
    const book = await Book.findOne({ rfidTag: rfid });
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
    const { isbn, title, author, category, rfidTag } = req.body;
    const existing = await Book.findOne({ rfidTag });
    if (existing) {
      return res.status(400).json({ success: false, message: 'Mã RFID này đã được gán cho cuốn sách khác' });
    }

    const book = await Book.create({ isbn, title, author, category, rfidTag });
    res.status(201).json({ success: true, data: book });
  } catch (err) {
    next(err);
  }
}

export async function deleteBook(req, res, next) {
  try {
    const { id } = req.params;
    await Book.findByIdAndDelete(id);
    res.json({ success: true, message: 'Đã xóa sách thành công' });
  } catch (err) {
    next(err);
  }
}

