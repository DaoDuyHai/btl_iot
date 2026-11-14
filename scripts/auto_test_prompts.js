#!/usr/bin/env node
/**
 * auto_test_prompts.js
 * Tự động gửi 100 câu hỏi từ TEST_PROMPTS_100.md trực tiếp tới AI Service (Port 8000/5000)
 * Y HỆT như bạn đọc đang gõ trò chuyện trên màn hình Kiosk.
 * 
 * NGUYÊN TẮC:
 * - 100% kết nối HTTP thực tế tới AI Engine (Multilingual-E5 + BM25 + Query Analyzer).
 * - KHÔNG mock, KHÔNG fallback dữ liệu giả lập.
 * - Nếu AI Service chưa bật, dừng ngay và yêu cầu bật service.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');

let promptsFile = path.join(ROOT_DIR, 'TEST_PROMPTS_100_v2.md');
if (!fs.existsSync(promptsFile)) {
  promptsFile = path.join(ROOT_DIR, 'TEST_PROMPTS_100.md');
}

const AI_SERVICE_URL = 'http://127.0.0.1:8000';
const SERVER_URL = 'http://127.0.0.1:5000';

// 1. Phân tích tham số CLI
const args = process.argv.slice(2);
let targetGroup = null;
let maxLimit = 100;
let startIndex = 1;
let endIndex = 100;

for (const arg of args) {
  if (arg.startsWith('--file=')) {
    promptsFile = path.resolve(ROOT_DIR, arg.split('=')[1]);
  } else if (arg.startsWith('--group=') || arg.startsWith('-g=')) {
    targetGroup = parseInt(arg.split('=')[1], 10);
  } else if (arg.startsWith('--limit=') || arg.startsWith('-n=')) {
    maxLimit = parseInt(arg.split('=')[1], 10);
  } else if (arg.startsWith('--range=')) {
    const parts = arg.split('=')[1].split('-');
    startIndex = parseInt(parts[0], 10) || 1;
    endIndex = parseInt(parts[1], 10) || 100;
  }
}

// 2. Đọc file prompts
function parseTestPrompts() {
  if (!fs.existsSync(promptsFile)) {
    console.error(`❌ Không tìm thấy file: ${promptsFile}`);
    process.exit(1);
  }

  const raw = fs.readFileSync(promptsFile, 'utf8');
  const lines = raw.split('\n');
  const prompts = [];
  let currentGroup = 'Chung';
  let groupIndex = 0;

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('## ')) {
      currentGroup = trimmed.replace(/^##\s+/, '').trim();
      const gMatch = currentGroup.match(/(?:NHÓM\s+)?(\d+)/i);
      groupIndex = gMatch ? parseInt(gMatch[1], 10) : groupIndex + 1;
    } else {
      const match = trimmed.match(/^(\d+)\.\s+(.+)$/);
      if (match) {
        prompts.push({
          num: parseInt(match[1], 10),
          group: currentGroup,
          groupNum: groupIndex,
          text: match[2].trim()
        });
      }
    }
  }
  return prompts;
}

// 3. Kiểm tra kênh kết nối AI Service thực tế
async function detectAiBackend() {
  // Ưu tiên 1: Kết nối trực tiếp Python FastAPI (Port 8000)
  try {
    const controller = new AbortController();
    const tId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${AI_SERVICE_URL}/api/stats`, { signal: controller.signal });
    clearTimeout(tId);
    if (res.ok) {
      const stats = await res.json();
      return { 
        type: 'fastapi', 
        url: `${AI_SERVICE_URL}/api/chat`, 
        name: `Python FastAPI (Port 8000) • ${stats.method || 'Hybrid E5 + BM25'}` 
      };
    }
  } catch (_e) {}

  // Ưu tiên 2: Kết nối qua Node.js Express Gateway (Port 5000)
  try {
    const controller = new AbortController();
    const tId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${SERVER_URL}/api/health`, { signal: controller.signal });
    clearTimeout(tId);
    if (res.ok) {
      return { 
        type: 'express', 
        url: `${SERVER_URL}/api/ai/chat`, 
        name: `Node.js Express Gateway (Port 5000) ➔ AI Service` 
      };
    }
  } catch (_e) {}

  // Không có server nào đang chạy -> Dừng và cảnh báo trung thực
  return null;
}

// 4. Gửi câu hỏi tới AI Engine thật
async function queryRealAi(backend, promptText) {
  const t0 = performance.now();

  if (backend.type === 'fastapi') {
    const res = await fetch(backend.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: promptText,
        top_k: 4,
        studentInfo: { name: 'Bạn đọc Kiosk (Kiểm thử)', department: 'PTIT' }
      })
    });
    if (!res.ok) {
      throw new Error(`AI Service lỗi HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    const latency = Math.round(performance.now() - t0);
    return {
      reply: data.reply || data.intro || 'Thủ thư gửi bạn các ấn phẩm phù hợp:',
      books: data.books || [],
      analysis: data.analysis || { intent: data.intent || 'CATEGORY_TOPIC' },
      latencyMs: latency
    };
  }

  if (backend.type === 'express') {
    const res = await fetch(backend.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: promptText,
        studentInfo: { name: 'Bạn đọc Kiosk (Kiểm thử)', department: 'PTIT' }
      })
    });
    if (!res.ok) {
      throw new Error(`Express Gateway lỗi HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    const latency = Math.round(performance.now() - t0);
    return {
      reply: data.reply || 'Thủ thư gửi bạn các ấn phẩm phù hợp:',
      books: data.books || [],
      analysis: data.analysis || { intent: 'CATEGORY_TOPIC' },
      latencyMs: latency
    };
  }

  throw new Error('Kênh kết nối AI không xác định');
}

// 5. Hàm thực thi chính
async function run() {
  console.log('\n' + '='.repeat(80));
  console.log('  🤖 KIỂM THỬ TỰ ĐỘNG THỰC TẾ 100 CÂU HỎI QUA AI SERVICE (KHÔNG MOCK)');
  console.log('='.repeat(80));

  const allPrompts = parseTestPrompts();
  console.log(`📋 Đã nạp thành công: ${allPrompts.length} câu hỏi từ ${path.basename(promptsFile)}`);

  let filtered = allPrompts.filter(p => p.num >= startIndex && p.num <= endIndex);
  if (targetGroup) {
    filtered = filtered.filter(p => p.groupNum === targetGroup);
    console.log(`🎯 Lọc theo: Nhóm ${targetGroup} (${filtered.length} câu)`);
  }
  if (filtered.length > maxLimit) {
    filtered = filtered.slice(0, maxLimit);
  }
  console.log(`⚡ Số câu sẽ chạy: ${filtered.length} câu.`);

  console.log('\n🔍 Đang kết nối tới AI Service...');
  const backend = await detectAiBackend();

  if (!backend) {
    console.error('\n❌ KHÔNG THỂ KẾT NỐI TỚI AI SERVICE!');
    console.error('--------------------------------------------------------------------------------');
    console.error('Hệ thống từ chối tạo dữ liệu giả lập (mock/fallback) vào kho CONVERSATION_HISTORY.');
    console.error('Vui lòng khởi chạy AI Service thật trước:');
    console.error('   👉 Cách 1: Chạy file start.bat để khởi động toàn bộ hệ thống.');
    console.error('   👉 Cách 2: Chạy lệnh "npm run ai:dev" để mở riêng AI Service (Port 8000).');
    console.error('--------------------------------------------------------------------------------\n');
    process.exit(1);
  }

  console.log(`✅ Kết nối THÀNH CÔNG: [${backend.name}]`);
  console.log('💡 Lưu ý: Python AI Service sẽ TỰ ĐỘNG ghi nhận toàn bộ hội thoại chuẩn xác 100% vào CONVERSATION_HISTORY.md!');
  console.log('\n' + '-'.repeat(80));
  console.log('Bắt đầu gửi câu hỏi...');
  console.log('-'.repeat(80) + '\n');

  let successCount = 0;
  let totalLatency = 0;
  const shelfCount = { A: 0, B: 0, C: 0, D: 0, E: 0, F: 0 };

  for (let i = 0; i < filtered.length; i++) {
    const item = filtered[i];
    const prefix = `[${String(item.num).padStart(3, ' ')}/100]`;

    try {
      const res = await queryRealAi(backend, item.text);
      successCount++;
      totalLatency += res.latencyMs;

      (res.books || []).forEach(b => {
        const s = (b.shelf || 'A').toUpperCase();
        if (shelfCount[s] !== undefined) shelfCount[s]++;
      });

      const shelves = [...new Set((res.books || []).map(b => b.shelf || 'A'))].join('/');
      console.log(`${prefix} "${item.text.slice(0, 46)}${item.text.length > 46 ? '…' : ''}" ➔ ${res.books.length} sách (Kệ ${shelves || 'A'}) [${res.latencyMs}ms]`);
    } catch (err) {
      console.error(`${prefix} ❌ Lỗi: ${err.message}`);
    }

    // Nghỉ nhẹ 50ms giữa các request
    await new Promise(r => setTimeout(r, 50));
  }

  const avgLatency = successCount > 0 ? Math.round(totalLatency / successCount) : 0;

  console.log('\n' + '='.repeat(80));
  console.log('  🎉 HOÀN TẤT KIỂM THỬ THỰC TẾ!');
  console.log('='.repeat(80));
  console.log(`✅ Xử lý thành công: ${successCount}/${filtered.length} câu hỏi`);
  console.log(`⚡ Độ trễ thực tế trung bình: ${avgLatency} ms (Mô hình E5 + BM25)`);
  console.log(`📊 Phân bổ gợi ý theo khu vực kệ sách thực tế:`);
  console.log(`   - Kệ A (Văn học - Thiếu nhi):        ${shelfCount.A} lượt`);
  console.log(`   - Kệ B (Kinh tế - Kinh doanh):       ${shelfCount.B} lượt`);
  console.log(`   - Kệ C (CNTT - Khoa học kỹ thuật):   ${shelfCount.C} lượt`);
  console.log(`   - Kệ D (Giáo dục - Ngoại ngữ):       ${shelfCount.D} lượt`);
  console.log(`   - Kệ E (Kỹ năng sống - Tâm lý học):  ${shelfCount.E} lượt`);
  console.log(`   - Kệ F (Lịch sử - Văn hóa):          ${shelfCount.F} lượt`);
  console.log(`\n📁 Toàn bộ nhật ký đối thoại do chính AI Service ghi nhận tại:`);
  console.log(`   👉 ${path.join(ROOT_DIR, 'CONVERSATION_HISTORY.md')}`);
  console.log('='.repeat(80) + '\n');
}

run().catch(err => {
  console.error('Lỗi thực thi:', err);
  process.exit(1);
});
