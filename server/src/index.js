import http from 'http';
import app from './app.js';
import { ENV } from './config/env.js';
import { connectDB } from './config/db.js';
import { initSocketIO } from './sockets/index.js';
import { initMQTT } from './mqtt/client.js';

async function bootstrap() {
  console.log('-------------------------------------------------------');
  console.log('🚀 KHỞI ĐỘNG HỆ THỐNG SMART LIBRARY KIOSK BACKEND');
  console.log('-------------------------------------------------------');

  // 1. Kết nối CSDL MongoDB
  await connectDB();

  // 2. Tạo HTTP Server
  const server = http.createServer(app);

  // 3. Khởi tạo Socket.IO Realtime
  initSocketIO(server);

  // 4. Khởi tạo kết nối MQTT Broker
  initMQTT();

  // 5. Lắng nghe HTTP Port
  server.listen(ENV.PORT, () => {
    console.log(`🌐 [HTTP Server] Đang lắng nghe tại: http://localhost:${ENV.PORT}`);
    console.log(`📡 [Kiosk Device ID]: ${ENV.KIOSK_DEVICE_ID}`);
    console.log('-------------------------------------------------------');
  });
}

bootstrap();
