import Loan from '../models/Loan.js';
import Book from '../models/Book.js';
import Reader from '../models/Reader.js';
import { ENV } from '../config/env.js';
import { sendReceiptEmail } from './emailService.js';

export async function borrowBatch({ readerId, bookIds, loanDays = 14 }) {
  const reader = await Reader.findById(readerId);
  if (!reader || !reader.active) {
    throw new Error('Độc giả không tồn tại hoặc tài khoản đã bị khóa');
  }

  if (!Array.isArray(bookIds) || bookIds.length === 0) {
    throw new Error('Danh sách sách mượn không hợp lệ');
  }

  // 1. Kiểm tra danh sách trùng lặp
  const uniqueBookIds = [...new Set(bookIds.map(String))];
  if (uniqueBookIds.length !== bookIds.length) {
    throw new Error('Danh sách tài liệu mượn có phần tử bị trùng lặp');
  }

  // 2. Chặn mượn nếu bạn đọc đang có sách QUÁ HẠN chưa trả
  const now = new Date();
  const overdueLoansCount = await Loan.countDocuments({
    readerId: reader._id,
    status: { $in: ['borrowing', 'overdue'] },
    dueDate: { $lt: now }
  });
  if (overdueLoansCount > 0) {
    throw new Error(`Tài khoản đang có ${overdueLoansCount} tài liệu quá hạn chưa hoàn trả! Bạn đọc vui lòng hoàn tất trả sách và nộp phạt trước khi mượn tài liệu mới.`);
  }

  // 3. Kiểm tra hạn mức mượn tối đa (Tối đa 5 cuốn/bạn đọc)
  const currentBorrowedCount = await Loan.countDocuments({
    readerId: reader._id,
    status: { $in: ['borrowing', 'overdue'] }
  });
  if (currentBorrowedCount + uniqueBookIds.length > 5) {
    throw new Error(`Vượt quá hạn mức mượn tài liệu! Mỗi bạn đọc chỉ được mượn tối đa 5 cuốn (Hiện đang mượn: ${currentBorrowedCount} cuốn, muốn mượn thêm: ${uniqueBookIds.length} cuốn).`);
  }

  // 4. Kiểm tra tính khả dụng của từng cuốn (Chặn tuyệt đối nếu sách đang mượn hoặc không available)
  const books = await Book.find({ _id: { $in: uniqueBookIds } });
  if (books.length !== uniqueBookIds.length) {
    throw new Error('Một số sách không tồn tại trong hệ thống');
  }

  const unavailable = books.find(b => b.status !== 'available');
  if (unavailable) {
    throw new Error(`Cuốn sách "${unavailable.title}" hiện không khả dụng (Trạng thái: ${unavailable.status === 'borrowed' ? 'Đang được mượn / chưa trả' : unavailable.status}). Không thể tạo lệnh mượn!`);
  }

  // 5. Kiểm tra chéo xem có phiếu mượn nào còn active liên kết với các cuốn sách này không
  const activeExistingLoans = await Loan.find({
    bookId: { $in: uniqueBookIds },
    status: { $in: ['borrowing', 'overdue'] }
  }).populate('bookId');
  if (activeExistingLoans.length > 0) {
    const conflictedBook = activeExistingLoans[0].bookId?.title || 'Tài liệu';
    throw new Error(`Cuốn sách "${conflictedBook}" đang có phiếu mượn hoạt động chưa hoàn trả! Không thể mượn lại.`);
  }

  const dueDate = new Date();
  dueDate.setDate(now.getDate() + loanDays);

  const createdLoans = [];

  for (const book of books) {
    const loan = await Loan.create({
      readerId: reader._id,
      bookId: book._id,
      borrowDate: now,
      dueDate,
      status: 'borrowing',
      renewCount: 0
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

export async function returnBookByRfid(bookRfid) {
  const book = await Book.findOne({ rfidTag: bookRfid });
  if (!book) {
    throw new Error(`Không tìm thấy cuốn sách với mã RFID: ${bookRfid}`);
  }

  const loan = await Loan.findOne({ 
    bookId: book._id, 
    status: { $in: ['borrowing', 'overdue'] } 
  }).populate('readerId');

  if (!loan) {
    // Sách đã có sẵn trong thư viện
    return {
      book,
      alreadyReturned: true,
      message: 'Sách này hiện đã có sẵn trong thư viện, không có phiếu mượn cần hoàn trả.'
    };
  }

  const now = new Date();
  let fineAmount = 0;
  let isOverdue = false;

  if (now > loan.dueDate) {
    isOverdue = true;
    const diffTime = Math.abs(now - loan.dueDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    fineAmount = diffDays * ENV.FINE_PER_DAY_VND;
  }

  loan.returnDate = now;
  loan.fineAmount = fineAmount;

  if (isOverdue) {
    // Sách quá hạn: giữ trạng thái overdue, chưa thanh toán phạt (isPaid = false)
    loan.status = 'overdue';
    loan.isPaid = false;
  } else {
    // Sách đúng hạn: hoàn tất ngay
    loan.status = 'returned';
    loan.isPaid = true;
  }
  await loan.save();

  book.status = 'available';
  await book.save();

  // Tạo URL VietQR nếu có tiền phạt
  let vietQrUrl = null;
  if (fineAmount > 0) {
    vietQrUrl = `https://img.vietqr.io/image/${ENV.BANK_BIN}-${ENV.BANK_ACCOUNT}-compact2.png?amount=${fineAmount}&addInfo=PHAT%20${loan.readerId.studentId}&accountName=THU%20VIEN`;
  }

  return {
    book,
    reader: loan.readerId,
    isOverdue,
    fineAmount,
    isPaid: loan.isPaid,
    vietQrUrl,
    loan
  };
}

export async function payFine(loanId) {
  const loan = await Loan.findById(loanId).populate('bookId').populate('readerId');
  if (!loan) {
    throw new Error('Không tìm thấy phiếu mượn tương ứng');
  }

  loan.isPaid = true;
  loan.status = 'returned';
  await loan.save();

  return {
    success: true,
    message: `Đã xác nhận nộp phạt ${loan.fineAmount?.toLocaleString('vi-VN')} VNĐ thành công`,
    loan
  };
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

