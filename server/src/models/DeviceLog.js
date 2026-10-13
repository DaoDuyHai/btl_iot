import mongoose from 'mongoose';

const deviceLogSchema = new mongoose.Schema({
  deviceId: { type: String, required: true },
  event: { 
    type: String, 
    enum: ['scan', 'heartbeat', 'offline', 'command', 'error'], 
    required: true 
  },
  payload: { type: mongoose.Schema.Types.Mixed },
  rssi: { type: Number },
  uptime: { type: Number },
  timestamp: { type: Date, default: Date.now }
}, { timestamps: true });

export default mongoose.model('DeviceLog', deviceLogSchema);

