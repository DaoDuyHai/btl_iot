import mongoose from 'mongoose';

const readerSchema = new mongoose.Schema({
  studentId: { type: String, required: true, unique: true },
  name: { type: String, required: true },
  email: { type: String, required: true },
  phone: { type: String, default: '0988123456' },
  department: { type: String, default: 'Khoa Công Nghệ Thông Tin 1 - PTIT' },
  rfidCard: { type: String, required: true, unique: true },
  active: { type: Boolean, default: true }
}, { timestamps: true });

export default mongoose.model('Reader', readerSchema);

