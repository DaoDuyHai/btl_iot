import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import mongoose from 'mongoose';
import dotenv from 'dotenv';
import Book from '../models/Book.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/library_kiosk';

function parseCSV(text) {
  const lines = [];
  let row = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      row.push(current);
      current = '';
    } else if ((char === '\r' || char === '\n') && !inQuotes) {
      if (char === '\r' && next === '\n') i++;
      row.push(current);
      if (row.some(c => c.trim().length > 0)) {
        lines.push(row);
      }
      row = [];
      current = '';
    } else {
      current += char;
    }
  }

  if (current || row.length > 0) {
    row.push(current);
    if (row.some(c => c.trim().length > 0)) {
      lines.push(row);
    }
  }

  return lines;
}

// Bảng ánh xạ RFID Demo cho các phím tắt cứng trên Simulator IoT (Phím 2, 3, 4, 8)
const DEMO_RFID_MAP = {
  B0001: 'A1B2C3D4', // Phím [2] Virtual Simulator
  B0002: 'B2C3D4E5', // Phím [3] Virtual Simulator
  B0003: 'C3D4E5F6', // Phím [4] Virtual Simulator
  B0004: 'D4E5F6A7'  // Phím [8] Virtual Simulator
};

export async function seedAiBooks() {
  console.log('🔄 [Seed AI Books] Bắt đầu đồng bộ 3.000 cuốn sách từ AI sang MongoDB...');

  const csvPath = path.resolve(__dirname, '../../../ai-service/dataset/cleaned_books_dataset.csv');
  if (!fs.existsSync(csvPath)) {
    throw new Error(`Không tìm thấy file dataset chuẩn tại: ${csvPath}`);
  }

  const rawCSV = fs.readFileSync(csvPath, 'utf8');
  const rows = parseCSV(rawCSV);
  if (rows.length < 2) {
    throw new Error('File dataset không có dữ liệu hợp lệ.');
  }

  const header = rows[0].map(h => h.trim());
  const idxMap = {};
  header.forEach((h, idx) => {
    idxMap[h] = idx;
  });

  const getVal = (row, colName, fallback = '') => {
    const idx = idxMap[colName];
    if (idx === undefined || idx >= row.length) return fallback;
    return row[idx]?.trim() || fallback;
  };

  const booksToUpsert = [];
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    const bookId = getVal(r, 'Book_ID', `B${String(i).padStart(4, '0')}`);
    const title = getVal(r, 'Title', 'Tài liệu Thư viện PTIT');
    const author = getVal(r, 'Author', 'Nhiều tác giả');
    const category = getVal(r, 'Category', 'Chung');
    const subcategory = getVal(r, 'Subcategory', '');
    const description = getVal(r, 'Description', '');
    const publisher = getVal(r, 'Publisher', 'NXB Thông tin và Truyền thông');
    const publicationYear = parseInt(getVal(r, 'Publication_Year', '2024'), 10) || 2024;
    const shelf = getVal(r, 'Shelf', 'A');
    const floor = parseInt(getVal(r, 'Floor', '1'), 10) || 1;
    const position = getVal(r, 'Position', `${shelf}1-01`);
    const totalCopies = parseInt(getVal(r, 'Total_Copies', '5'), 10) || 5;
    const availableCopies = parseInt(getVal(r, 'Available_Copies', '5'), 10) || 5;

    // Ưu tiên RFID demo cho 4 cuốn đầu, các cuốn còn lại gán RFID_Bxxxx
    const rfidTag = DEMO_RFID_MAP[bookId] || `RFID_${bookId}`;
    const status = availableCopies > 0 ? 'available' : 'borrowed';

    booksToUpsert.push({
      bookId,
      title,
      author,
      category,
      subcategory,
      description,
      publisher,
      publicationYear,
      shelf,
      floor,
      position,
      totalCopies,
      availableCopies,
      rfidTag,
      copyCode: `CP-${bookId}`,
      isbn: `978-604-${bookId}`,
      status,
      physicalCondition: 'normal',
      isDeleted: false
    });
  }

  console.log(`📦 Đã xử lý ${booksToUpsert.length} đầu sách. Đang nạp vào MongoDB...`);

  // BulkWrite chia nhỏ theo chunk 500 records để đạt tốc độ cao nhất
  const CHUNK_SIZE = 500;
  let totalProcessed = 0;

  for (let i = 0; i < booksToUpsert.length; i += CHUNK_SIZE) {
    const chunk = booksToUpsert.slice(i, i + CHUNK_SIZE);
    const operations = chunk.map(book => ({
      updateOne: {
        filter: { bookId: book.bookId },
        update: { $set: book },
        upsert: true
      }
    }));

    await Book.bulkWrite(operations, { ordered: false });
    totalProcessed += chunk.length;
    console.log(`  ⚡ Tiến độ: ${totalProcessed}/${booksToUpsert.length} sách...`);
  }

  console.log(`✅ [Seed AI Books] Hoàn tất nạp thành công ${totalProcessed} sách vào MongoDB!`);
  return totalProcessed;
}

// Cho phép chạy độc lập từ CLI: node src/scripts/seedAiBooks.js
if (process.argv[1] && process.argv[1].endsWith('seedAiBooks.js')) {
  (async () => {
    try {
      console.log(`🔌 Kết nối MongoDB: ${MONGODB_URI}...`);
      await mongoose.connect(MONGODB_URI);
      console.log('✅ Đã kết nối MongoDB!');
      await seedAiBooks();
      await mongoose.disconnect();
      console.log('👋 Đã ngắt kết nối an toàn.');
      process.exit(0);
    } catch (err) {
      console.error('❌ Lỗi nạp sách:', err.message);
      process.exit(1);
    }
  })();
}
