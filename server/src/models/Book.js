import mongoose from 'mongoose';

const bookSchema = new mongoose.Schema({
  isbn: { type: String, required: true },
  title: { type: String, required: true },
  author: { type: String, required: true },
  category: { type: String, default: 'Chung' },
  subcategory: { type: String, default: '' },
  description: { type: String, default: '' },
  shelf: { type: String, default: 'A' },
  floor: { type: Number, default: 1 },
  position: { type: String, default: 'A1-01' },
  publisher: { type: String, default: '' },
  publicationYear: { type: Number, default: 2024 },
  totalCopies: { type: Number, default: 1 },
  availableCopies: { type: Number, default: 1 },
  rfidTag: { type: String, required: true, unique: true },
  bookId: { type: String, index: true },
  copyCode: { type: String, default: '' },
  status: { 
    type: String, 
    enum: [
      'available',           // Sẵn sàng cho mượn
      'borrowed',            // Đang được mượn
      'pending_inspection',   // Đã trả tại Kiosk, chờ thủ thư kiểm tra vật lý
      'maintenance',          // Đang sửa chữa hoặc chờ xử lý
      'damaged',              // Hư hỏng nặng, không được mượn
      'lost',                 // Đã ghi nhận mất sách
      'inactive'              // Ngừng lưu hành
    ], 
    default: 'available' 
  },
  physicalCondition: {
    type: String,
    enum: ['normal', 'minor_damage', 'needs_repair', 'severely_damaged', 'lost'],
    default: 'normal'
  },
  inspectionNote: { type: String, default: '' },
  lastInspectedBy: { type: String, default: '' },
  lastInspectedAt: { type: Date, default: null },
  isDeleted: { type: Boolean, default: false }
}, { timestamps: true });

export default mongoose.model('Book', bookSchema);
