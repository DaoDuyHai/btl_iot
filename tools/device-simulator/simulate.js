const mqtt = require('mqtt');
const readline = require('readline');
const http = require('http');
const fs = require('fs');
const path = require('path');

const BROKER_URL = process.env.MQTT_BROKER_URL || 'mqtt://localhost:1883';
const DEVICE_ID = 'kiosk_01';
const WEB_PORT = process.env.PORT || 8888;

// ANSI Colors for Terminal
const C = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  bgGreen: '\x1b[42m\x1b[30m',
  bgRed: '\x1b[41m\x1b[37m'
};

console.clear();
console.log(`${C.green}================================================================================${C.reset}`);
console.log(`${C.bright}${C.green}📟 HỆ THỐNG GIẢ LẬP PHẦN CỨNG IOT KIOSK PTIT (VIRTUAL HARDWARE CONSOLE)${C.reset}`);
console.log(`${C.cyan}• Thiết bị ảo:${C.reset} ESP32 NodeMCU-32S (Device ID: ${C.bright}${DEVICE_ID}${C.reset})`);
console.log(`${C.cyan}• MQTT Broker:${C.reset} ${BROKER_URL}`);
console.log(`${C.bright}${C.yellow}🌐 GIAO DIỆN WEB SIMULATOR:${C.reset} ${C.bright}${C.white}http://localhost:${WEB_PORT}${C.reset}`);
console.log(`${C.green}================================================================================${C.reset}\n`);

// Danh sách client kết nối SSE (Web GUI)
let sseClients = [];

function broadcastSSE(type, data) {
  const payload = `data: ${JSON.stringify({ type, data })}\n\n`;
  sseClients.forEach(client => {
    try {
      client.write(payload);
    } catch (e) {}
  });
}

// 1. KẾT NỐI MQTT BROKER
const mqttClient = mqtt.connect(BROKER_URL, {
  clientId: `esp32_kiosk_${Math.random().toString(16).slice(2, 8)}`,
  clean: true,
  reconnectPeriod: 3000,
  will: {
    topic: `kiosk/${DEVICE_ID}/status`,
    payload: JSON.stringify({ status: 'offline' }),
    qos: 1,
    retain: true
  }
});

let heartbeatInterval = null;

mqttClient.on('connect', () => {
  console.log(`${C.bright}${C.green}✅ [MQTT] Đã kết nối Mosquitto Broker thành công!${C.reset}`);
  sendHeartbeat();

  if (heartbeatInterval) clearInterval(heartbeatInterval);
  heartbeatInterval = setInterval(sendHeartbeat, 30000);

  mqttClient.subscribe(`kiosk/${DEVICE_ID}/command`, (err) => {
    if (!err) {
      console.log(`${C.cyan}📡 [MQTT SUB] Đã đăng ký lắng nghe lệnh tại: kiosk/${DEVICE_ID}/command${C.reset}`);
      printMenu();
    }
  });
});

mqttClient.on('message', (topic, message) => {
  try {
    const data = JSON.parse(message.toString());
    handleServerCommand(data);
    // Bắn dữ liệu lên Web GUI qua SSE
    broadcastSSE('COMMAND', data);
  } catch (err) {
    console.error('Lỗi phân tích gói tin server:', err);
  }
});

mqttClient.on('error', (err) => {
  console.log(`${C.red}❌ [MQTT ERROR] Lỗi kết nối: ${err.message}${C.reset}`);
});

function handleServerCommand(data) {
  console.log(`\n${C.yellow}─────────────────────────────────────────────────────────────────${C.reset}`);
  console.log(`📥 ${C.bright}[LỆNH NHẬN TỪ SERVER]${C.reset} Action: "${data.action}", Status: "${data.status}"`);

  if (data.action === 'feedback') {
    if (data.status === 'success') {
      console.log(`${C.bgGreen} 🟢 [LED XANH: ON] ${C.reset} ${C.green}→ Thao tác hợp lệ / Giao dịch thành công! (Bíp 1 tiếng)${C.reset}`);
    } else {
      console.log(`${C.bgRed} 🔴 [LED ĐỎ: NHÁP NHÁY 3 LẦN] ${C.reset} ${C.red}→ Thẻ không hợp lệ / Từ chối! (Bíp-bíp-bíp)${C.reset}`);
    }
  } else if (data.action === 'reboot') {
    console.log(`${C.magenta}🔄 [HARDWARE RESTART] ESP32 Khởi động lại...${C.reset}`);
    sendHeartbeat();
  }
  console.log(`${C.yellow}─────────────────────────────────────────────────────────────────${C.reset}\n`);
  promptAction();
}

function sendHeartbeat() {
  const payload = {
    status: 'online',
    rssi: -54,
    uptime: Math.floor(process.uptime()),
    timestamp: Math.floor(Date.now() / 1000)
  };
  mqttClient.publish(`kiosk/${DEVICE_ID}/status`, JSON.stringify(payload), { qos: 1 });
  broadcastSSE('HEARTBEAT', payload);
}

function publishRfidScan(uid, description = '') {
  const payload = {
    uid: uid.toUpperCase(),
    type: 'rfid',
    timestamp: Math.floor(Date.now() / 1000)
  };

  mqttClient.publish(`kiosk/${DEVICE_ID}/scan`, JSON.stringify(payload), { qos: 1 });

  console.log(`\n${C.bright}${C.magenta}💳 [RFID SCAN] Đã quẹt thẻ UID: ${uid} (${description})${C.reset}`);
  broadcastSSE('SCAN', { uid, description });
  promptAction();
}

// 2. KHỞI CHẠY HTTP SERVER PHỤC VỤ GIAO DIỆN WEB (GUI)
const htmlPath = path.join(__dirname, 'public', 'index.html');

const server = http.createServer((req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  // Route 1: Giao diện Web
  if (req.method === 'GET' && (req.url === '/' || req.url === '/index.html')) {
    fs.readFile(htmlPath, 'utf8', (err, content) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        return res.end('Lỗi nạp file HTML giao diện: ' + err.message);
      }
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(content);
    });
    return;
  }

  // Route 2: SSE Realtime Stream
  if (req.method === 'GET' && req.url === '/api/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });
    res.write('data: {"type":"CONNECTED"}\n\n');
    sseClients.push(res);

    req.on('close', () => {
      sseClients = sseClients.filter(c => c !== res);
    });
    return;
  }

  // Route 3: API Quẹt Thẻ từ Web GUI
  if (req.method === 'POST' && req.url === '/api/scan') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { uid, label } = JSON.parse(body);
        if (uid) {
          publishRfidScan(uid, label || 'Web GUI Trigger');
          res.writeHead(200, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ success: true, uid }));
        }
      } catch (e) {}
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, message: 'Invalid payload' }));
    });
    return;
  }

  // Route 4: API Gửi nhịp tim
  if (req.method === 'POST' && req.url === '/api/ping') {
    sendHeartbeat();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ success: true }));
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(WEB_PORT, () => {
  console.log(`${C.bright}${C.green}🚀 [WEB GUI SERVER] Đã sẵn sàng tại: ${C.white}http://localhost:${WEB_PORT}${C.reset}`);
  console.log(`${C.dim}👉 Bạn có thể mở link trên bằng trình duyệt để bấm chuột quẹt thẻ trực quan thay vì gõ phím!${C.reset}\n`);
});

// 3. VẪN HỖ TRỢ BÀN PHÍM TERMINAL (CLI FALLBACK)
function printMenu() {
  console.log(`${C.cyan}--------------------------------------------------------------------------------${C.reset}`);
  console.log(`${C.bright}💡 Bạn có thể quẹt thẻ bằng 1 trong 2 cách:${C.reset}`);
  console.log(`   1. ${C.bright}${C.green}Mở Giao Diện Web:${C.reset} ${C.white}http://localhost:${WEB_PORT}${C.reset} (Có giao diện nút bấm chuột, đèn LED, còi bíp)`);
  console.log(`   2. ${C.bright}${C.yellow}Bấm phím ngay tại Console này:${C.reset}`);
  console.log(`      [1] Quẹt Thẻ SV Nguyễn Văn A (E2801192)      [2] Quẹt Sách Quá Hạn 3 Ngày (A1B2C3D4)`);
  console.log(`      [3] Quẹt Sách Đang Mượn (D4C3B2A1)           [4] Quẹt Sách Kho Mượn 1 (B3C4D5E6)`);
  console.log(`      [5] Quẹt Sách Kho Mượn 2 (C5D6E7F8)          [6] Quẹt Sách Kho Mượn 3 (E9F0A1B2)`);
  console.log(`      [7] Quẹt Thẻ SV 2: Trần Thị Mai (A8B9C0D1)   [8] Quẹt Thẻ Lạ Không Hợp Lệ (99999999)`);
  console.log(`      [c] Nhập UID thủ công                        [h] Ping Nhịp Tim Online`);
  console.log(`${C.cyan}--------------------------------------------------------------------------------${C.reset}\n`);
  promptAction();
}

function promptAction() {
  process.stdout.write(`${C.dim}IoT-Hardware > Bấm phím (1-8, c, h, m, q) hoặc dùng Web UI: ${C.reset}`);
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

let isEnteringCustomUid = false;

rl.on('line', (line) => {
  const input = line.trim();

  if (isEnteringCustomUid) {
    if (input) {
      publishRfidScan(input, `Thẻ nhập tay từ bàn phím (${input})`);
    }
    isEnteringCustomUid = false;
    promptAction();
    return;
  }

  switch (input.toLowerCase()) {
    case '1':
      publishRfidScan('E2801192', 'Thẻ Bạn Đọc: Nguyễn Văn A (B21DCCN001)');
      break;
    case '2':
      publishRfidScan('A1B2C3D4', 'Sách: Lập trình C++ Nâng Cao (Quá hạn 3 ngày)');
      break;
    case '3':
      publishRfidScan('D4C3B2A1', 'Sách: Cấu Trúc Dữ Liệu & Giải Thuật (Đúng hạn)');
      break;
    case '4':
      publishRfidScan('B3C4D5E6', 'Sách: IoT & Hệ Thống Kiosk Tự Phục Vụ (Sẵn có)');
      break;
    case '5':
      publishRfidScan('C5D6E7F8', 'Sách: Giáo Trình Mạng Máy Tính & Viễn Thông (Sẵn có)');
      break;
    case '6':
      publishRfidScan('E9F0A1B2', 'Sách: Trí Tuệ Nhân Tạo & Học Máy Ứng Dụng (Sẵn có)');
      break;
    case '7':
      publishRfidScan('A8B9C0D1', 'Thẻ Sinh Viên 2: Trần Thị Mai (B21DCVT002)');
      break;
    case '8':
      publishRfidScan('99999999', 'Thẻ lạ / Chưa đăng ký trong hệ thống');
      break;
    case 'c':
      isEnteringCustomUid = true;
      process.stdout.write(`\nNhập mã UID RFID bạn muốn quét rồi nhấn ENTER: `);
      return;
    case 'h':
      sendHeartbeat();
      console.log(`\n💓 Đã gửi Heartbeat Online tới Broker.`);
      promptAction();
      break;
    case 'm':
    case '?':
      printMenu();
      break;
    case 'q':
      console.log(`\n👋 Đang ngắt kết nối và đóng giả lập IoT...`);
      mqttClient.publish(`kiosk/${DEVICE_ID}/status`, JSON.stringify({ status: 'offline' }), () => {
        mqttClient.end();
        process.exit(0);
      });
      break;
    default:
      promptAction();
      break;
  }
});
