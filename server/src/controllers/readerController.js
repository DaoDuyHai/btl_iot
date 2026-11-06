import Reader from '../models/Reader.js';
import Loan from '../models/Loan.js';
import AuditLog from '../models/AuditLog.js';

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
      status: { $in: ['borrowing', 'overdue'] }
    }).populate('bookId');

    const unpaidLoans = await Loan.find({
      readerId: reader._id,
      $or: [
        { fineStatus: 'unpaid' },
        { isPaid: false, fineAmount: { $gt: 0 } }
      ]
    }).populate('bookId');

    const totalUnpaidFine = unpaidLoans.reduce((sum, l) => sum + (l.fineAmount || 0), 0);

    res.json({ 
      success: true, 
      data: { 
        reader, 
        activeLoans, 
        unpaidLoans, 
        totalUnpaidFine,
        hasDebt: totalUnpaidFine > 0
      } 
    });
  } catch (err) {
    next(err);
  }
}

export async function createReader(req, res, next) {
  try {
    const { studentId, name, email, phone, department, rfidCard } = req.body;
    const existing = await Reader.findOne({ $or: [{ studentId }, { rfidCard }] });
    if (existing) {
      return res.status(400).json({ success: false, message: 'MSSV hoặc Mã thẻ RFID này đã tồn tại' });
    }

    const reader = await Reader.create({ studentId, name, email, phone, department, rfidCard });
    
    await AuditLog.create({
      actor: 'Thủ thư',
      action: 'UPDATE_READER',
      targetType: 'Reader',
      targetId: reader._id,
      details: { actionType: 'CREATE', name: reader.name, studentId: reader.studentId }
    }).catch(() => {});

    res.status(201).json({ success: true, data: reader });
  } catch (err) {
    next(err);
  }
}

export async function updateReader(req, res, next) {
  try {
    const { id } = req.params;
    const { studentId, name, email, phone, department, rfidCard, active, blockReason } = req.body;

    const reader = await Reader.findById(id);
    if (!reader) {
      return res.status(404).json({ success: false, message: 'Không tìm thấy độc giả' });
    }

    // Nếu đổi rfidCard hoặc studentId thì kiểm tra trùng lặp
    if (rfidCard && rfidCard !== reader.rfidCard) {
      const existing = await Reader.findOne({ rfidCard, _id: { $ne: id } });
      if (existing) {
        return res.status(400).json({ success: false, message: 'Mã thẻ RFID này đã được cấp cho độc giả khác' });
      }
      reader.rfidCard = rfidCard;
    }

    if (studentId && studentId !== reader.studentId) {
      const existing = await Reader.findOne({ studentId, _id: { $ne: id } });
      if (existing) {
        return res.status(400).json({ success: false, message: 'Mã sinh viên này đã tồn tại' });
      }
      reader.studentId = studentId;
    }

    if (name !== undefined) reader.name = name;
    if (email !== undefined) reader.email = email;
    if (phone !== undefined) reader.phone = phone;
    if (department !== undefined) reader.department = department;
    if (active !== undefined) reader.active = active;
    if (blockReason !== undefined) reader.blockReason = blockReason;

    await reader.save();

    await AuditLog.create({
      actor: 'Thủ thư',
      action: active === false ? 'BLOCK_READER' : 'UPDATE_READER',
      targetType: 'Reader',
      targetId: reader._id,
      details: { actionType: 'UPDATE', changes: req.body }
    }).catch(() => {});

    res.json({ success: true, data: reader, message: 'Cập nhật thông tin độc giả thành công' });
  } catch (err) {
    next(err);
  }
}
