import mongoose from 'mongoose';
import dotenv from 'dotenv';
import Reader from '../models/Reader.js';
import Book from '../models/Book.js';
import Loan from '../models/Loan.js';

dotenv.config();

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/library_kiosk';

async function seedData() {
  try {
    console.log('🔄 Đang kết nối MongoDB để khởi tạo cơ sở dữ liệu mẫu...');
    await mongoose.connect(MONGODB_URI);
    console.log('✅ Đã kết nối MongoDB thành công!');

    // 1. Dọn dẹp dữ liệu cũ
    await Reader.deleteMany({});
    await Book.deleteMany({});
    await Loan.deleteMany({});
    console.log('🧹 Đã xóa sạch dữ liệu cũ trong các collection (Reader, Book, Loan).');

    // 2. Tạo danh sách Bạn đọc chuẩn Học viện Công nghệ Bưu chính Viễn thông (PTIT)
    const readers = await Reader.insertMany([
      {
        studentId: 'B21DCCN001',
        name: 'Nguyễn Văn A',
        email: 'haicoder.journey@gmail.com',
        phone: '0988123456',
        department: 'Khoa Công Nghệ Thông Tin 1 - PTIT',
        rfidCard: 'E2801192', // Phím [1] trên Virtual IoT Simulator
        active: true
      },
      {
        studentId: 'B21DCVT002',
        name: 'Trần Thị Mai',
        email: 'thuvien.ptit.test@gmail.com',
        phone: '0912345678',
        department: 'Khoa Viễn Thông 1 - PTIT',
        rfidCard: 'A8B9C0D1', // Phím [7] trên Virtual IoT Simulator
        active: true
      }
    ]);
    const readerA = readers[0];

    // 3. Tạo kho sách phong phú đáp ứng đầy đủ các kịch bản thực tế
    const books = await Book.insertMany([
      {
        isbn: '978-604-0-01',
        title: 'Lập trình C++ Nâng Cao',
        author: 'GS. Phạm Văn B',
        category: 'Công nghệ thông tin',
        rfidTag: 'A1B2C3D4', // Phím [2] trên Simulator -> Test TRẢ QUÁ HẠN & VIETQR
        status: 'borrowed'
      },
      {
        isbn: '978-604-0-02',
        title: 'Cấu Trúc Dữ Liệu & Giải Thuật',
        author: 'TS. Lê Thị C',
        category: 'Khoa học máy tính',
        rfidTag: 'D4C3B2A1', // Phím [3] trên Simulator -> Test GIA HẠN & TRẢ ĐÚNG HẠN
        status: 'borrowed'
      },
      {
        isbn: '978-604-0-03',
        title: 'Internet of Things & Hệ Thống Kiosk Tự Phục Vụ',
        author: 'ThS. Trần Văn D',
        category: 'IoT & Phần cứng',
        rfidTag: 'B3C4D5E6', // Phím [4] trên Simulator -> Test MƯỢN MỚI
        status: 'available'
      },
      {
        isbn: '978-604-0-04',
        title: 'Giáo Trình Mạng Máy Tính & Viễn Thông',
        author: 'PGS.TS Nguyễn Văn E',
        category: 'Mạng viễn thông',
        rfidTag: 'C5D6E7F8', // Phím [5] trên Simulator -> Test MƯỢN MỚI
        status: 'available'
      },
      {
        isbn: '978-604-0-05',
        title: 'Trí Tuệ Nhân Tạo & Học Máy Ứng Dụng',
        author: 'TS. Vũ Hoàng Nam',
        category: 'Trí tuệ nhân tạo',
        rfidTag: 'E9F0A1B2', // Phím [6] trên Simulator -> Test MƯỢN MỚI
        status: 'available'
      },
      {
        isbn: '978-604-0-06',
        title: 'Kỹ Thuật Vi Điều Khiển & Vi Xử Lý ESP32',
        author: 'TS. Đặng Quốc Hưng',
        category: 'Điện tử viễn thông',
        rfidTag: 'F1E2D3C4',
        status: 'available'
      }
    ]);

    // 4. Khởi tạo các kịch bản mượn trả phục vụ kiểm thử song song
    const now = new Date();

    // Kịch bản A: Phiếu mượn ĐÃ QUÁ HẠN 3 NGÀY (Để test Trả sách phát sinh tiền phạt & VietQR)
    const overdueBorrowDate = new Date();
    overdueBorrowDate.setDate(now.getDate() - 17);
    const overdueDueDate = new Date();
    overdueDueDate.setDate(now.getDate() - 3); // Quá hạn 3 ngày

    await Loan.create({
      readerId: readerA._id,
      bookId: books[0]._id, // Lập trình C++ Nâng Cao (A1B2C3D4)
      borrowDate: overdueBorrowDate,
      dueDate: overdueDueDate,
      status: 'borrowing',
      renewCount: 0
    });

    // Kịch bản B: Phiếu mượn ĐÚNG HẠN còn 10 ngày (Để test Gia hạn & TrẢ đúng hạn phí 0đ)
    const validBorrowDate = new Date();
    validBorrowDate.setDate(now.getDate() - 4);
    const validDueDate = new Date();
    validDueDate.setDate(now.getDate() + 10); // Còn 10 ngày

    await Loan.create({
      readerId: readerA._id,
      bookId: books[1]._id, // Cấu Trúc Dữ Liệu & Giải Thuật (D4C3B2A1)
      borrowDate: validBorrowDate,
      dueDate: validDueDate,
      status: 'borrowing',
      renewCount: 0
    });

    // Kịch bản C: Phiếu mượn ĐÃ TRẢ THÀNH CÔNG trong quá khứ (Lịch sử mượn trả)
    const pastBorrowDate = new Date();
    pastBorrowDate.setDate(now.getDate() - 30);
    const pastDueDate = new Date();
    pastDueDate.setDate(now.getDate() - 16);
    const pastReturnDate = new Date();
    pastReturnDate.setDate(now.getDate() - 17);

    await Loan.create({
      readerId: readerA._id,
      bookId: books[5]._id, // Kỹ Thuật ESP32
      borrowDate: pastBorrowDate,
      dueDate: pastDueDate,
      returnDate: pastReturnDate,
      status: 'returned',
      fineAmount: 0,
      isPaid: true
    });

    console.log('\n=============================================================');
    console.log('🎉 CƠ SỞ DỮ LIỆU ĐÃ ĐƯỢC THIẾT LẬP THÀNH CÔNG CHO KIOSK PTIT:');
    console.log('=============================================================');
    console.log(`👤 BẠN ĐỌC CHÍNH (Đã liên kết Gmail nhận biên lai thực tế):`);
    console.log(`   - Tên: ${readerA.name} | MSSV: ${readerA.studentId}`);
    console.log(`   - Email: ${readerA.email}`);
    console.log(`   - Thẻ RFID: ${readerA.rfidCard} (Phím [1] trên Simulator)`);
    console.log(`📚 KHO SÁCH (6 cuốn):`);
    console.log(`   - Sách quá hạn 3 ngày (Phím [2]): "${books[0].title}" (UID: ${books[0].rfidTag})`);
    console.log(`   - Sách đang mượn đúng hạn (Phím [3]): "${books[1].title}" (UID: ${books[1].rfidTag})`);
    console.log(`   - Sách sẵn sàng mượn (Phím [4], [5], [6]): Sẵn có trong kho`);
    console.log(`📋 PHIẾU MƯỢN SẴN CÓ:`);
    console.log(`   - 1 Phiếu QUÁ HẠN (Test Quẹt trả -> VietQR 15.000đ & Email)`);
    console.log(`   - 1 Phiếu ĐÚNG HẠN (Test Gia Hạn +14 ngày & Email)`);
    console.log(`   - 1 Phiếu ĐÃ HOÀN TẤT (Xem lịch sử tài khoản bạn đọc)`);
    console.log('=============================================================\n');

    process.exit(0);
  } catch (err) {
    console.error('❌ Lỗi nạp seed data:', err);
    process.exit(1);
  }
}

seedData();
