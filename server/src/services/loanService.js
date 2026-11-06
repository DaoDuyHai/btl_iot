import Loan from '../models/Loan.js';
import Book from '../models/Book.js';
import Reader from '../models/Reader.js';
import AuditLog from '../models/AuditLog.js';
import { ENV } from '../config/env.js';
import { sendReceiptEmail } from './emailService.js';

export async function borrowBatch({ readerId, bookIds, loanDays = 14 }) {
  if (!readerId || !bookIds || !Array.isArray(bookIds) || bookIds.length === 0) {
    throw new Error('Dữ liệu mượn sách không hợp lệ (readerId và bookIds là bắt buộc)');
  }

  // Chặn phần tử trùng lặp trong mảng bookIds gửi lên
  const uniqueBookIds = [...new Set(bookIds)];
  if (uniqueBookIds.length !== bookIds.length) {
    throw new Error('Danh sách tài liệu mượn có phần tử bị trùng lặp');
  }

  // 1. Kiểm tra bạn đọc tồn tại và đang hoạt động
  const reader = await Reader.findById(readerId);
  if (!reader || reader.active === false) {
    throw new Error('Độc giả không tồn tại hoặc tài khoản đã bị khóa');
  }

  // 2. Chặn mượn nếu bạn đọc đang có khoản nợ phạt chưa thanh toán (Mục 3 STT 3 & Mục 6.3)
  const unpaidFineCount = await Loan.countDocuments({
    readerId: reader._id,
    $or: [
      { fineStatus: 'unpaid' },
      { isPaid: false, fineAmount: { $gt: 0 } }
    ]
  });
  if (unpaidFineCount > 0) {
    throw new Error('Độc giả đang có khoản phạt chưa thanh toán! Thư viện tạm khóa quyền mượn sách mới cho đến khi hoàn tất nộp phạt.');
  }

  // 3. Chặn mượn nếu bạn đọc đang có sách quá hạn chưa hoàn trả
  const overdueCount = await Loan.countDocuments({
    readerId: reader._id,
    status: 'overdue'
  });
  if (overdueCount > 0) {
    throw new Error(`Độc giả đang có ${overdueCount} tài liệu quá hạn chưa hoàn trả! Vui lòng hoàn trả tài liệu cũ trước khi mượn mới.`);
  }

  // 4. Kiểm tra giới hạn mượn tối đa 5 cuốn (Hạn mức thư viện)
  const activeCount = await Loan.countDocuments({
    readerId: reader._id,
    status: 'borrowing'
  });
  if (activeCount + bookIds.length > 5) {
    throw new Error(`Vượt quá hạn mức mượn tài liệu (Hiện đang mượn ${activeCount} cuốn, yêu cầu thêm ${bookIds.length} cuốn, tối đa cho phép 5 cuốn).`);
  }

  // 5. Kiểm tra danh sách sách trong DB: Phải tồn tại và ở trạng thái 'available'
  const books = await Book.find({
    _id: { $in: bookIds },
    status: 'available',
    isDeleted: { $ne: true }
  });

  if (books.length !== bookIds.length) {
    const foundIds = books.map(b => b._id.toString());
    const missingId = bookIds.find(id => !foundIds.includes(id.toString()));
    const unavailableBook = await Book.findById(missingId);
    const title = unavailableBook ? unavailableBook.title : missingId;
    throw new Error(`Cuốn sách "${title}" hiện không khả dụng (đang được mượn, chờ kiểm tra hoặc bảo trì).`);
  }

  // 6. Thực hiện giao dịch mượn
  const now = new Date();
  const dueDate = new Date(now.getTime() + loanDays * 24 * 60 * 60 * 1000);
  const createdLoans = [];

  for (const book of books) {
    const loan = await Loan.create({
      readerId: reader._id,
      bookId: book._id,
      borrowDate: now,
      dueDate,
      status: 'borrowing',
      renewCount: 0,
      fineStatus: 'none',
      isPaid: false
    });

    book.status = 'borrowed';
    await book.save();

    createdLoans.push(loan);
  }

  // Tự động gửi email biên lai mượn tài liệu
  sendReceiptEmail({
    reader,
    items: books.map(b => ({ title: b.title, author: b.author, dueDate })),
    actionType: 'BORROW'
  }).catch(() => {});

  return {
    reader,
    dueDate,
    count: createdLoans.length,
    loans: createdLoans
  };
}

/**
 * Xem trước thông tin tài liệu cần trả khi quét tại Kiosk.
 * TUYỆT ĐỐI KHÔNG CẬP NHẬT DATABASE Ở BƯỚC NÀY! (Sửa lỗi STT 1 Mục 2.1)
 */
export async function getReturnPreview(bookRfid) {
  const book = await Book.findOne({ rfidTag: bookRfid, isDeleted: { $ne: true } });
  if (!book) {
    throw new Error(`Không tìm thấy cuốn sách với mã RFID: ${bookRfid}`);
  }

  const loan = await Loan.findOne({ 
    bookId: book._id, 
    status: { $in: ['borrowing', 'overdue'] } 
  }).populate('readerId');

  if (!loan) {
    return {
      book,
      alreadyReturned: true,
      message: 'Sách này hiện đã có sẵn trong thư viện, không có phiếu mượn cần hoàn trả.'
    };
  }

  const now = new Date();
  let fineAmount = 0;
  let isOverdue = false;
  let overdueDays = 0;

  if (now > loan.dueDate) {
    isOverdue = true;
    const diffTime = now.getTime() - new Date(loan.dueDate).getTime();
    overdueDays = Math.max(1, Math.round(diffTime / (1000 * 60 * 60 * 24)));
    fineAmount = overdueDays * ENV.FINE_PER_DAY_VND;
  }

  let vietQrUrl = null;
  if (fineAmount > 0 && loan.readerId?.studentId) {
    vietQrUrl = `https://img.vietqr.io/image/${ENV.BANK_BIN}-${ENV.BANK_ACCOUNT}-compact2.png?amount=${fineAmount}&addInfo=PHAT%20${loan.readerId.studentId}&accountName=THU%20VIEN`;
  }

  return {
    book,
    loan,
    reader: loan.readerId,
    isOverdue,
    overdueDays,
    fineAmount,
    vietQrUrl,
    alreadyReturned: false
  };
}

/**
 * Hoàn thành trả sách theo lô (Chỉ thực thi khi người dùng bấm Hoàn thành trả sách).
 * Chuyển sách sang 'pending_inspection' để thủ thư kiểm tra vật lý (Sửa lỗi STT 2 & 6).
 */
export async function returnBatch({ bookRfids, readerId = null, returnMethod = 'kiosk_rfid' }) {
  if (!Array.isArray(bookRfids) || bookRfids.length === 0) {
    throw new Error('Danh sách mã RFID tài liệu trả không hợp lệ');
  }

  const now = new Date();
  const processedItems = [];
  let totalFine = 0;
  let primaryReader = readerId ? await Reader.findById(readerId) : null;

  for (const rfid of bookRfids) {
    const book = await Book.findOne({ rfidTag: rfid, isDeleted: { $ne: true } });
    if (!book) continue;

    const loan = await Loan.findOne({
      bookId: book._id,
      status: { $in: ['borrowing', 'overdue'] }
    }).populate('readerId');

    if (!loan) continue;

    if (!primaryReader && loan.readerId) {
      primaryReader = loan.readerId;
    }

    // Tính tiền phạt quá hạn và chốt dừng thời gian tính quá hạn tại đúng thời điểm trả
    let isOverdue = false;
    let overdueFine = 0;
    if (now > loan.dueDate) {
      isOverdue = true;
      const diffTime = now.getTime() - new Date(loan.dueDate).getTime();
      const diffDays = Math.max(1, Math.round(diffTime / (1000 * 60 * 60 * 24)));
      overdueFine = diffDays * ENV.FINE_PER_DAY_VND;
    }

    loan.returnDate = now;
    loan.overdueFine = overdueFine;
    loan.fineAmount = overdueFine;
    loan.status = 'returned'; // Kết thúc lượt mượn, dừng tính ngày quá hạn
    loan.returnMethod = returnMethod;
    loan.inspectionStatus = 'pending'; // Chờ thủ thư kiểm tra vật lý

    if (overdueFine > 0) {
      loan.fineStatus = 'unpaid';
      loan.isPaid = false;
      totalFine += overdueFine;
    } else {
      loan.fineStatus = 'none';
      loan.isPaid = true;
    }

    await loan.save();

    // Sách chuyển sang trạng thái chờ thủ thư kiểm tra
    book.status = 'pending_inspection';
    await book.save();

    processedItems.push({
      book,
      loan,
      reader: loan.readerId,
      isOverdue,
      overdueFine
    });
  }

  if (processedItems.length === 0) {
    throw new Error('Không tìm thấy phiếu mượn hợp lệ nào cần hoàn trả trong danh sách đã chọn');
  }

  // Tạo mã VietQR nếu có tổng tiền phạt
  let vietQrUrl = null;
  if (totalFine > 0 && primaryReader?.studentId) {
    vietQrUrl = `https://img.vietqr.io/image/${ENV.BANK_BIN}-${ENV.BANK_ACCOUNT}-compact2.png?amount=${totalFine}&addInfo=PHAT%20${primaryReader.studentId}&accountName=THU%20VIEN`;
  }

  // Gửi biên lai trả tài liệu qua email
  if (primaryReader) {
    sendReceiptEmail({
      reader: primaryReader,
      items: processedItems.map(item => ({
        title: item.book.title,
        author: item.book.author,
        isOverdue: item.isOverdue,
        fineAmount: item.overdueFine
      })),
      actionType: 'RETURN'
    }).catch(() => {});
  }

  return {
    success: true,
    count: processedItems.length,
    items: processedItems,
    totalFine,
    vietQrUrl,
    message: 'Đã tiếp nhận sách – chờ thủ thư kiểm tra tình trạng vật lý'
  };
}

/**
 * Trả sách đơn lẻ (Tương thích ngược và hỗ trợ kiểm thử)
 */
export async function returnBookByRfid(bookRfid) {
  const preview = await getReturnPreview(bookRfid);
  if (preview.alreadyReturned) {
    return preview;
  }

  const batchResult = await returnBatch({ bookRfids: [bookRfid] });
  const item = batchResult.items[0];

  return {
    book: item.book,
    reader: item.reader,
    isOverdue: item.isOverdue,
    fineAmount: item.overdueFine,
    isPaid: item.loan.isPaid,
    vietQrUrl: batchResult.vietQrUrl,
    loan: item.loan
  };
}

/**
 * Thủ thư kiểm tra sách sau khi trả (Mục 5)
 */
export async function inspectBook({
  loanId,
  result,
  damageType = 'none',
  damageDescription = '',
  damageFine = 0,
  actor = 'Thủ thư',
  inspectionNotes = ''
}) {
  const loan = await Loan.findById(loanId).populate('bookId').populate('readerId');
  if (!loan) {
    throw new Error('Không tìm thấy phiếu mượn tương ứng để kiểm tra');
  }

  const book = await Book.findById(loan.bookId._id || loan.bookId);
  if (!book) {
    throw new Error('Không tìm thấy tài liệu tương ứng');
  }

  const now = new Date();
  damageFine = Number(damageFine) || 0;

  // Cập nhật trạng thái sách theo kết quả kiểm tra (Mục 5 Bảng kết quả)
  switch (result) {
    case 'normal':
      book.status = 'available';
      book.physicalCondition = 'normal';
      break;
    case 'minor_damage':
      book.status = 'available';
      book.physicalCondition = 'minor_damage';
      break;
    case 'needs_repair':
      book.status = 'maintenance';
      book.physicalCondition = 'needs_repair';
      break;
    case 'damaged':
      book.status = 'damaged';
      book.physicalCondition = 'severely_damaged';
      break;
    case 'lost':
      book.status = 'lost';
      book.physicalCondition = 'lost';
      break;
    default:
      book.status = 'available';
      book.physicalCondition = 'normal';
  }

  book.lastInspectedBy = actor;
  book.lastInspectedAt = now;
  book.inspectionNote = inspectionNotes || damageDescription;
  await book.save();

  // Cập nhật phiếu mượn
  loan.inspectionStatus = 'inspected';
  loan.inspectedBy = actor;
  loan.inspectedAt = now;
  loan.inspectionNotes = inspectionNotes;

  if (damageFine > 0) {
    loan.damageFine = damageFine;
    loan.damageType = damageType;
    loan.damageDescription = damageDescription;
    loan.fineAmount = (loan.overdueFine || 0) + damageFine;
    loan.fineStatus = 'unpaid';
    loan.isPaid = false;
  }

  await loan.save();

  // Ghi nhật ký Audit Log
  await AuditLog.create({
    actor,
    action: 'INSPECT_BOOK',
    targetType: 'Loan',
    targetId: loan._id,
    details: {
      result,
      damageFine,
      damageType,
      damageDescription,
      bookTitle: book.title,
      readerStudentId: loan.readerId?.studentId
    }
  });

  return {
    success: true,
    loan,
    book,
    message: `Đã hoàn tất kiểm tra tài liệu "${book.title}". Trạng thái mới: ${book.status}`
  };
}

/**
 * Trả sách thủ công khi nhãn RFID bị hỏng/mất (Mục 8)
 */
export async function manualReturn({ loanId, actor = 'Thủ thư', reason = 'Nhãn RFID hỏng/mất' }) {
  const loan = await Loan.findById(loanId).populate('bookId').populate('readerId');
  if (!loan) {
    throw new Error('Không tìm thấy phiếu mượn tương ứng để trả thủ công');
  }

  const book = await Book.findById(loan.bookId._id || loan.bookId);
  const now = new Date();

  let overdueFine = 0;
  if (now > loan.dueDate) {
    const diffTime = now.getTime() - new Date(loan.dueDate).getTime();
    const diffDays = Math.max(1, Math.round(diffTime / (1000 * 60 * 60 * 24)));
    overdueFine = diffDays * ENV.FINE_PER_DAY_VND;
  }

  loan.returnDate = now;
  loan.overdueFine = overdueFine;
  loan.fineAmount = overdueFine;
  loan.status = 'returned';
  loan.returnMethod = 'manual_librarian';
  loan.inspectionStatus = 'pending';

  if (overdueFine > 0) {
    loan.fineStatus = 'unpaid';
    loan.isPaid = false;
  } else {
    loan.fineStatus = 'none';
    loan.isPaid = true;
  }

  await loan.save();

  if (book) {
    book.status = 'pending_inspection';
    await book.save();
  }

  await AuditLog.create({
    actor,
    action: 'MANUAL_RETURN',
    targetType: 'Loan',
    targetId: loan._id,
    details: {
      reason,
      bookTitle: book?.title,
      readerStudentId: loan.readerId?.studentId,
      overdueFine
    }
  });

  return {
    success: true,
    loan,
    book,
    message: `Đã xác nhận trả thủ công cho cuốn sách "${book?.title}". Trạng thái: Chờ kiểm tra.`
  };
}

/**
 * Thanh toán tiền phạt (Nộp phạt)
 */
export async function payFine(loanId, actor = 'Hệ thống') {
  const loan = await Loan.findById(loanId).populate('bookId').populate('readerId');
  if (!loan) {
    throw new Error('Không tìm thấy phiếu mượn tương ứng');
  }

  loan.isPaid = true;
  loan.fineStatus = 'paid';
  await loan.save();

  await AuditLog.create({
    actor,
    action: 'PAY_FINE',
    targetType: 'Loan',
    targetId: loan._id,
    details: {
      fineAmount: loan.fineAmount,
      readerStudentId: loan.readerId?.studentId
    }
  });

  return {
    success: true,
    message: `Đã xác nhận nộp phạt ${loan.fineAmount?.toLocaleString('vi-VN')} VNĐ thành công`,
    loan
  };
}

/**
 * Miễn tiền phạt (Mục 6.2)
 */
export async function waiveFine(loanId, reason = 'Miễn phạt theo quy chế', actor = 'Thủ thư') {
  const loan = await Loan.findById(loanId).populate('bookId').populate('readerId');
  if (!loan) {
    throw new Error('Không tìm thấy phiếu mượn tương ứng');
  }

  loan.fineStatus = 'waived';
  loan.isPaid = true;
  await loan.save();

  await AuditLog.create({
    actor,
    action: 'WAIVE_FINE',
    targetType: 'Loan',
    targetId: loan._id,
    details: {
      waivedAmount: loan.fineAmount,
      reason,
      readerStudentId: loan.readerId?.studentId
    }
  });

  return {
    success: true,
    message: `Đã miễn khoản phạt ${loan.fineAmount?.toLocaleString('vi-VN')} VNĐ cho bạn đọc`,
    loan
  };
}

/**
 * Khiếu nại khoản phạt (Mục 6.2)
 */
export async function disputeFine(loanId, reason = 'Độc giả khiếu nại', actor = 'Độc giả') {
  const loan = await Loan.findById(loanId).populate('bookId').populate('readerId');
  if (!loan) {
    throw new Error('Không tìm thấy phiếu mượn tương ứng');
  }

  loan.fineStatus = 'disputed';
  await loan.save();

  await AuditLog.create({
    actor,
    action: 'DISPUTE_FINE',
    targetType: 'Loan',
    targetId: loan._id,
    details: {
      reason,
      readerStudentId: loan.readerId?.studentId
    }
  });

  return {
    success: true,
    message: 'Đã chuyển trạng thái khoản phạt sang khiếu nại (disputed) để chờ xem xét',
    loan
  };
}

/**
 * Lấy danh sách các tài liệu đang chờ kiểm tra vật lý sau khi trả
 */
export async function getPendingInspectionBooks() {
  return Loan.find({
    status: 'returned',
    inspectionStatus: 'pending'
  })
    .sort({ returnDate: -1 })
    .populate('bookId')
    .populate('readerId');
}

export async function sendReturnBatchReceipt({ readerId, items = [] }) {
  let reader = null;
  if (readerId) {
    reader = await Reader.findById(readerId);
  }
  if (!reader && items[0]?.readerId) {
    reader = await Reader.findById(items[0].readerId);
  }
  if (!reader) {
    throw new Error('Không tìm thấy thông tin bạn đọc để gửi email biên lai');
  }

  await sendReceiptEmail({
    reader,
    items,
    actionType: 'RETURN'
  });

  return {
    success: true,
    message: `Đã gửi 01 email biên lai trả ${items.length} tài liệu tới ${reader.email}`
  };
}

export async function renewLoans({ loanIds, extraDays = 14 }) {
  if (!Array.isArray(loanIds) || loanIds.length === 0) {
    throw new Error('Danh sách phiếu mượn cần gia hạn không hợp lệ');
  }

  const loans = await Loan.find({ _id: { $in: loanIds }, status: 'borrowing' }).populate('bookId').populate('readerId');
  if (loans.length === 0) {
    throw new Error('Không tìm thấy tài liệu đang mượn hợp lệ để gia hạn');
  }

  const now = new Date();

  // Chặn tuyệt đối gia hạn sách ĐÃ QUÁ HẠN
  const overdueLoan = loans.find(l => now > new Date(l.dueDate));
  if (overdueLoan) {
    const bookTitle = overdueLoan.bookId?.title || 'Tài liệu';
    throw new Error(`Cuốn sách "${bookTitle}" đã quá hạn trả! Quy định thư viện PTIT không cho phép gia hạn sách trễ hạn. Vui lòng mang sách trả lại và nộp phạt.`);
  }

  // Chặn gia hạn quá 2 lần (Chính sách thư viện đại học)
  const maxRenewLoan = loans.find(l => (l.renewCount || 0) >= 2);
  if (maxRenewLoan) {
    const bookTitle = maxRenewLoan.bookId?.title || 'Tài liệu';
    throw new Error(`Cuốn sách "${bookTitle}" đã đạt hạn mức gia hạn tối đa (2 lần). Vui lòng hoàn trả tài liệu.`);
  }

  const updatedLoans = [];
  for (const loan of loans) {
    const currentDue = new Date(loan.dueDate);
    currentDue.setDate(currentDue.getDate() + extraDays);
    loan.dueDate = currentDue;
    loan.renewCount = (loan.renewCount || 0) + 1;
    await loan.save();
    updatedLoans.push(loan);
  }

  // Tự động gửi email biên lai gia hạn tài liệu
  if (loans[0]?.readerId) {
    sendReceiptEmail({
      reader: loans[0].readerId,
      items: updatedLoans.map(l => ({ title: l.bookId?.title, author: l.bookId?.author, dueDate: l.dueDate })),
      actionType: 'RENEW'
    }).catch(() => {});
  }

  return {
    count: updatedLoans.length,
    loans: updatedLoans
  };
}

export async function getLoanHistory(limit = 50) {
  return Loan.find()
    .sort({ createdAt: -1 })
    .limit(limit)
    .populate('readerId')
    .populate('bookId');
}
