import Reader from '../../models/Reader.js';
import Book from '../../models/Book.js';
import Loan from '../../models/Loan.js';
import DeviceLog from '../../models/DeviceLog.js';
import { emitToAll } from '../../sockets/index.js';
import { sendFeedback } from '../publisher.js';

export async function handleCardScan(deviceId, payload) {
  const { uid } = payload;
  if (!uid) return;

  console.log(`🔍 [Card Handler] Đang phân tích thẻ UID: ${uid} từ ${deviceId}`);

  try {
    // 1. Kiểm tra xem có phải Thẻ Độc Giả không
    const reader = await Reader.findOne({ rfidCard: uid });
    if (reader) {
      // Tìm các sách đang mượn của độc giả này
      const activeLoans = await Loan.find({ 
        readerId: reader._id, 
        status: { $in: ['borrowing', 'overdue'] } 
      }).populate('bookId');

      emitToAll('kiosk:event', {
        type: 'READER_AUTHENTICATED',
        data: {
          reader,
          activeLoans
        }
      });

      sendFeedback(deviceId, 'success');
      await logEvent(deviceId, 'scan', { uid, role: 'reader', name: reader.name });
      return;
    }

    // 2. Kiểm tra xem có phải Thẻ Sách không
    const book = await Book.findOne({ rfidTag: uid });
    if (book) {
      // Tìm xem sách có phiếu mượn nào đang hoạt động không
      const activeLoan = await Loan.findOne({ 
        bookId: book._id, 
        status: { $in: ['borrowing', 'overdue'] } 
      }).populate('readerId');

      emitToAll('kiosk:event', {
        type: 'BOOK_SCANNED',
        data: { 
          book,
          isAvailable: book.status === 'available' && !activeLoan,
          activeLoan: activeLoan ? {
            _id: activeLoan._id,
            status: activeLoan.status,
            dueDate: activeLoan.dueDate,
            readerName: activeLoan.readerId?.name,
            readerStudentId: activeLoan.readerId?.studentId
          } : null
        }
      });

      sendFeedback(deviceId, 'success');
      await logEvent(deviceId, 'scan', { uid, role: 'book', title: book.title, status: book.status });
      return;
    }

    // 3. Thẻ lạ chưa đăng ký vào hệ thống
    console.warn(`⚠️ [Card Handler] Thẻ UID lạ chưa đăng ký: ${uid}`);
    emitToAll('kiosk:event', {
      type: 'UNKNOWN_CARD',
      data: { uid }
    });

    sendFeedback(deviceId, 'error');
    await logEvent(deviceId, 'scan', { uid, role: 'unknown' });

  } catch (err) {
    console.error(`❌ [Card Handler] Lỗi xử lý thẻ:`, err);
    sendFeedback(deviceId, 'error');
  }
}

async function logEvent(deviceId, event, payload) {
  try {
    await DeviceLog.create({ deviceId, event, payload });
  } catch (err) {
    // Không chặn luồng nếu log lỗi
  }
}

