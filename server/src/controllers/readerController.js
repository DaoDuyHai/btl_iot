import Reader from '../models/Reader.js';
import Loan from '../models/Loan.js';

export async function getAllReaders(req, res, next) {
  try {
    const readers = await Reader.find().sort({ createdAt: -1 });
    res.json({ success: true, data: readers });
  } catch (err) {
    next(err);
  }
}

export async function getReaderByRfid(req, res, next) {
  try {
    const { rfid } = req.params;
    const reader = await Reader.findOne({ rfidCard: rfid });
    if (!reader) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy độc giả' });
    }

    const activeLoans = await Loan.find({ 
      readerId: reader._id, 
      status: { $in: ['borrowing', 'overdue'] },
      isPaid: false
    }).populate('bookId');

    res.json({ success: true, data: { reader, activeLoans } });
  } catch (err) {
    next(err);
  }
}

export async function createReader(req, res, next) {
  try {
    const { studentId, name, email, rfidCard } = req.body;
    const existing = await Reader.findOne({ $or: [{ studentId }, { rfidCard }] });
    if (existing) {
      return res.status(400).json({ success: false, message: 'MSSV hoặc Mã thẻ RFID này đã tồn tại' });
    }

    const reader = await Reader.create({ studentId, name, email, rfidCard });
    res.status(201).json({ success: true, data: reader });
  } catch (err) {
    next(err);
  }
}

