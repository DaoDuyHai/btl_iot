import mongoose from 'mongoose';

const loanSchema = new mongoose.Schema({
  readerId: { type: mongoose.Schema.Types.ObjectId, ref: 'Reader', required: true },
  bookId: { type: mongoose.Schema.Types.ObjectId, ref: 'Book', required: true },
  borrowDate: { type: Date, default: Date.now },
  dueDate: { type: Date, required: true },
  returnDate: { type: Date, default: null },
  status: { 
    type: String, 
    enum: ['borrowing', 'returned', 'overdue'], 
    default: 'borrowing' 
  },
  
  // Tiền phạt & phân loại
  fineAmount: { type: Number, default: 0 },       // Tổng tiền phạt = overdueFine + damageFine
  overdueFine: { type: Number, default: 0 },      // Tiền phạt quá hạn
  damageFine: { type: Number, default: 0 },       // Tiền phạt hư hỏng / bồi thường mất sách
  damageType: { 
    type: String, 
    enum: ['none', 'torn_cover', 'missing_pages', 'writing', 'water_damage', 'lost', 'other'],
    default: 'none'
  },
  damageDescription: { type: String, default: '' },
  fineStatus: {
    type: String,
    enum: ['none', 'pending', 'unpaid', 'paid', 'waived', 'disputed', 'cancelled'],
    default: 'none'
  },
  isPaid: { type: Boolean, default: false },

  // Kiểm tra vật lý sau khi trả
  inspectionStatus: {
    type: String,
    enum: ['none', 'pending', 'inspected'],
    default: 'none'
  },
  inspectedBy: { type: String, default: '' },
  inspectedAt: { type: Date, default: null },
  inspectionNotes: { type: String, default: '' },

  renewCount: { type: Number, default: 0 },
  returnMethod: { 
    type: String, 
    enum: ['kiosk_rfid', 'manual_librarian'], 
    default: 'kiosk_rfid' 
  }
}, { timestamps: true });

export default mongoose.model('Loan', loanSchema);
