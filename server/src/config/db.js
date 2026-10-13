import mongoose from 'mongoose';
import { ENV } from './env.js';

export async function connectDB() {
  try {
    const conn = await mongoose.connect(ENV.MONGODB_URI);
    console.log(`🍃 [MongoDB] Kết nối thành công tới Database: ${conn.connection.name}`);
  } catch (err) {
    console.error(`❌ [MongoDB] Lỗi kết nối CSDL:`, err.message);
    console.warn(`⚠️ Gợi ý: Hãy đảm bảo MongoDB đang chạy hoặc kiểm tra MONGODB_URI trong file .env`);
  }
}

