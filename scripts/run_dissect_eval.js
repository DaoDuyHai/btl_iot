import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { evaluateResponse } from './dissect_conversations.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');

const PROMPTS_FILE = path.join(ROOT_DIR, 'TEST_PROMPTS_100.md');
const raw = fs.readFileSync(PROMPTS_FILE, 'utf8');
const lines = raw.split('\n');
const prompts = [];
let currentGroup = 'Chung';
let groupNum = 1;

for (const line of lines) {
  const trimmed = line.trim();
  if (trimmed.startsWith('## ')) {
    currentGroup = trimmed.replace(/^##\s+/, '').trim();
    const match = currentGroup.match(/NHÓM\s+(\d+)/i);
    groupNum = match ? parseInt(match[1], 10) : groupNum + 1;
  } else {
    const match = trimmed.match(/^(\d+)\.\s+(.+)$/);
    if (match) {
      prompts.push({
        num: parseInt(match[1], 10),
        group: currentGroup,
        groupNum,
        text: match[2].trim()
      });
    }
  }
}

async function run() {
  console.log('='.repeat(80));
  console.log('  🔍 BẮT ĐẦU BÓC TÁCH & ĐÁNH GIÁ ĐỘ CHÍNH XÁC CỦA AI TRÊN 100 CÂU HỎI');
  console.log('='.repeat(80));

  const failures = [];
  let passed = 0;
  const groupStats = {};

  for (let g = 1; g <= 8; g++) {
    groupStats[g] = { total: 0, passed: 0 };
  }

  for (let i = 0; i < prompts.length; i++) {
    const p = prompts[i];
    groupStats[p.groupNum].total++;

    try {
      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: p.text, top_k: 4 })
      });
      const data = await res.json();
      const evalRes = evaluateResponse(p, data);

      if (evalRes.pass) {
        passed++;
        groupStats[p.groupNum].passed++;
      } else {
        failures.push({
          num: p.num,
          group: p.groupNum,
          text: p.text,
          intent: data.intent || data.analysis?.intent,
          books: (data.books || []).map(b => `${b.title} [${b.category}]`),
          reason: evalRes.reason
        });
      }
    } catch (e) {
      failures.push({ num: p.num, group: p.groupNum, text: p.text, reason: 'Lỗi mạng: ' + e.message });
    }

    await new Promise(r => setTimeout(r, 40));
  }

  const score = Math.round((passed / prompts.length) * 100);

  console.log('\n' + '='.repeat(80));
  console.log(`📊 KẾT QUẢ ĐÁNH GIÁ ĐỘ CHÍNH XÁC (ACCURACY SCORE): ${passed}/100 (${score}%)`);
  console.log('='.repeat(80));

  const groupNames = {
    1: 'Nhóm 1: Cảm xúc, tâm trạng & chữa lành',
    2: 'Nhóm 2: CNTT & Kỹ thuật PTIT',
    3: 'Nhóm 3: Kinh tế, khởi nghiệp & tài chính',
    4: 'Nhóm 4: Kỹ năng sống & Tâm lý học',
    5: 'Nhóm 5: Văn học, tiểu thuyết & nghệ thuật',
    6: 'Nhóm 6: Học ngoại ngữ & Luyện thi',
    7: 'Nhóm 7: Đọc nhanh, lười đọc',
    8: 'Nhóm 8: Ngoài phạm vi (OOD)'
  };

  for (let g = 1; g <= 8; g++) {
    const st = groupStats[g];
    const pct = Math.round((st.passed / st.total) * 100);
    console.log(`   ${groupNames[g]}: ${st.passed}/${st.total} câu đạt (${pct}%)`);
  }

  console.log('\n' + '-'.repeat(80));
  console.log(`❌ DANH SÁCH ${failures.length} CÂU HỎI LỖI / CHƯA ĐẠT (CẦN TỐI ƯU & TRAIN LẠI):`);
  console.log('-'.repeat(80));

  failures.forEach(f => {
    console.log(`[Câu #${f.num}] (Nhóm ${f.group}) "${f.text}"`);
    console.log(`   ❌ Lý do không đạt: ${f.reason}`);
    console.log(`   ⚙️ Intent nhận diện: ${f.intent}`);
    console.log(`   📚 Sách trả về: ${f.books ? f.books.slice(0, 3).join(' | ') : 'None'}`);
    console.log('');
  });

  fs.writeFileSync('ai-service/dissect_report_initial.json', JSON.stringify({
    accuracy_percent: score,
    total_passed: passed,
    total_questions: prompts.length,
    group_stats: groupStats,
    failures
  }, null, 2), 'utf8');
}

run().catch(console.error);
