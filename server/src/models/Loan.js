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
  fineAmount: { type: Number, default: 0 },
  isPaid: { type: Boolean, default: false },
  renewCount: { type: Number, default: 0 }
}, { timestamps: true });

export default mongoose.model('Loan', loanSchema);

