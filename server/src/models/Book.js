import mongoose from 'mongoose';

const bookSchema = new mongoose.Schema({
  isbn: { type: String, required: true },
  title: { type: String, required: true },
  author: { type: String, required: true },
  category: { type: String, default: 'Chung' },
  rfidTag: { type: String, required: true, unique: true },
  status: { 
    type: String, 
    enum: ['available', 'borrowed', 'maintenance'], 
    default: 'available' 
  }
}, { timestamps: true });

export default mongoose.model('Book', bookSchema);

