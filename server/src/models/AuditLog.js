import mongoose from 'mongoose';

const auditLogSchema = new mongoose.Schema({
  actor: { type: String, default: 'Thủ thư' },
  action: { 
    type: String, 
    required: true,
    enum: [
      'INSPECT_BOOK', 
      'MANUAL_RETURN', 
      'WAIVE_FINE', 
      'PAY_FINE',
      'DISPUTE_FINE',
      'UPDATE_BOOK', 
      'UPDATE_READER', 
      'BLOCK_READER',
      'UNBLOCK_READER'
    ]
  },
  targetType: { 
    type: String, 
    required: true, 
    enum: ['Book', 'Loan', 'Reader'] 
  },
  targetId: { type: mongoose.Schema.Types.ObjectId, required: true },
  details: { type: mongoose.Schema.Types.Mixed, default: {} },
  timestamp: { type: Date, default: Date.now }
}, { timestamps: true });

export default mongoose.model('AuditLog', auditLogSchema);
