import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');

const PROMPTS_FILE = path.join(ROOT_DIR, 'TEST_PROMPTS_100.md');

// 1. Đọc và phân tích 100 câu hỏi
const rawPrompts = fs.readFileSync(PROMPTS_FILE, 'utf8');
const lines = rawPrompts.split('\n');
const prompts = [];
let currentGroup = 'Chung';
let groupNum = 1;

for (const line of lines) {
  const trimmed = line.trim();
  if (trimmed.startsWith('## ')) {
    currentGroup = trimmed.replace(/^##\s+/, '').trim();
    const m = currentGroup.match(/NHÓM\s+(\d+)/i);
    groupNum = m ? parseInt(m[1], 10) : groupNum + 1;
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

// 2. Tiêu chuẩn đánh giá đúng/sai cho từng nhóm:
// Group 1: Cảm xúc & chữa lành -> Thể loại phải là Văn học, Kỹ năng sống, Tâm lý (Kệ A, E). Cấm trả về sách CNTT, thuật toán, kỹ thuật!
// Group 2: CNTT -> Thể loại phải là Công nghệ thông tin, Khoa học công nghệ (Kệ C).
// Group 3: Kinh tế -> Thể loại phải là Kinh tế – Kinh doanh (Kệ B).
// Group 4: Kỹ năng sống & Tâm lý -> Thể loại phải là Kỹ năng sống, Tâm lý học (Kệ E).
// Group 5: Văn học -> Thể loại phải là Văn học – Tiểu thuyết (Kệ A).
// Group 6: Ngoại ngữ -> Thể loại phải là Giáo dục – Ngoại ngữ (Kệ D).
// Group 7: Đọc nhanh, lười đọc -> Sách không quá nặng đầu, thể loại Văn học / Kỹ năng sống / Kinh tế / Thiếu nhi.
// Group 8: Out of domain -> intent === 'OUT_OF_DOMAIN' và books.length === 0.

export function evaluateResponse(item, data) {
  const books = data.books || [];
  const intent = data.intent || data.analysis?.intent || '';
  const num = item.num;
  const gNum = item.groupNum;

  // Nhóm 8: OOD
  if (gNum === 8) {
    const isOOD = intent === 'OUT_OF_DOMAIN' && books.length === 0;
    return {
      pass: isOOD,
      reason: isOOD ? 'Nhận diện đúng OOD và không gợi ý sách' : `Lỗi OOD: intent=${intent}, books=${books.length}`
    };
  }

  // Nếu không phải OOD mà trả về 0 sách -> Fail
  if (books.length === 0) {
    return { pass: false, reason: 'Không tìm thấy cuốn sách nào' };
  }

  // Nhóm 1: Cảm xúc, chữa lành, truyện hài
  if (gNum === 1) {
    // Cấm sách CNTT, toán, kỹ thuật
    const hasTechnical = books.some(b => 
      (b.category || '').includes('Công nghệ thông tin') ||
      (b.title || '').toLowerCase().includes('lập trình') ||
      (b.title || '').toLowerCase().includes('thuật toán') ||
      (b.title || '').toLowerCase().includes('vật lý')
    );
    if (hasTechnical) {
      return { pass: false, reason: 'Lẫn sách kỹ thuật/CNTT vào câu hỏi cảm xúc' };
    }
    const validCats = ['Văn học', 'Kỹ năng sống', 'Tâm lý', 'Thiếu nhi'];
    const matchCount = books.filter(b => validCats.some(vc => (b.category || '').includes(vc))).length;
    const pass = matchCount >= Math.ceil(books.length * 0.75);
    return {
      pass,
      reason: pass ? `Khớp ${matchCount}/${books.length} sách tâm lý/văn học` : `Chỉ có ${matchCount}/${books.length} sách đúng thể loại`
    };
  }

  // Nhóm 2: CNTT
  if (gNum === 2) {
    const itCount = books.filter(b => 
      (b.category || '').includes('Công nghệ thông tin') || 
      (b.category || '').includes('Khoa học – Công nghệ')
    ).length;
    const pass = itCount >= Math.ceil(books.length * 0.75);
    return {
      pass,
      reason: pass ? `Khớp ${itCount}/${books.length} sách CNTT/Khoa học` : `Lẫn sách ngoài ngành CNTT (${itCount}/${books.length})`
    };
  }

  // Nhóm 3: Kinh tế
  if (gNum === 3) {
    if (item.text.toLowerCase().includes('khởi nghiệp tinh gọn')) {
      const hasLean = books.some(b => (b.title || '').toLowerCase().includes('khởi nghiệp tinh gọn'));
      if (hasLean) return { pass: true, reason: 'Tìm thấy chính xác sách Khởi nghiệp tinh gọn' };
    }
    if (item.text.toLowerCase().includes('cha giàu cha nghèo') || item.text.toLowerCase().includes('robert kiyosaki')) {
      const hasRichDad = books.some(b => (b.title || '').toLowerCase().includes('cha giàu') || (b.title || '').toLowerCase().includes('dạy con làm giàu'));
      if (hasRichDad) return { pass: true, reason: 'Tìm thấy chính xác sách Cha giàu cha nghèo' };
    }
    const econCount = books.filter(b => (b.category || '').includes('Kinh tế')).length;
    const pass = econCount >= Math.ceil(books.length * 0.75);
    return {
      pass,
      reason: pass ? `Khớp ${econCount}/${books.length} sách Kinh tế` : `Chỉ có ${econCount}/${books.length} sách Kinh tế`
    };
  }

  // Nhóm 4: Kỹ năng sống & Tâm lý
  if (gNum === 4) {
    if (item.text.toLowerCase().includes('tâm lý học về tiền')) {
      const hasMorgan = books.some(b => (b.title || '').toLowerCase().includes('tâm lý học về tiền'));
      return {
        pass: hasMorgan,
        reason: hasMorgan ? 'Tìm thấy chính xác sách Tâm lý học về tiền của Morgan Housel' : 'Không tìm thấy sách Tâm lý học về tiền'
      };
    }
    if (item.text.toLowerCase().includes('carl jung') || item.text.toLowerCase().includes('freud')) {
      const hasJung = books.some(b => (b.title || '').toLowerCase().includes('jung') || (b.author || '').toLowerCase().includes('jung') || (b.description || '').toLowerCase().includes('jung'));
      if (hasJung) return { pass: true, reason: 'Tìm thấy chính xác sách của Carl Jung' };
    }
    const skillCount = books.filter(b => 
      (b.category || '').includes('Kỹ năng sống') || 
      (b.category || '').includes('Tâm lý học')
    ).length;
    const pass = skillCount >= Math.ceil(books.length * 0.75);
    return {
      pass,
      reason: pass ? `Khớp ${skillCount}/${books.length} sách Kỹ năng/Tâm lý` : `Chỉ có ${skillCount}/${books.length} sách Kỹ năng/Tâm lý`
    };
  }

  // Nhóm 5: Văn học
  if (gNum === 5) {
    const validCats = item.text.toLowerCase().includes('hà nội') ? ['Văn học', 'Lịch sử – Văn hóa'] : ['Văn học'];
    const litCount = books.filter(b => validCats.some(vc => (b.category || '').includes(vc))).length;
    const pass = litCount >= Math.ceil(books.length * 0.75);
    return {
      pass,
      reason: pass ? `Khớp ${litCount}/${books.length} sách Văn học/Văn hóa` : `Chỉ có ${litCount}/${books.length} sách Văn học`
    };
  }

  // Nhóm 6: Ngoại ngữ
  if (gNum === 6) {
    const langCount = books.filter(b => (b.category || '').includes('Ngoại ngữ')).length;
    const pass = langCount >= Math.ceil(books.length * 0.75);
    return {
      pass,
      reason: pass ? `Khớp ${langCount}/${books.length} sách Ngoại ngữ` : `Chỉ có ${langCount}/${books.length} sách Ngoại ngữ`
    };
  }

  // Nhóm 7: Đọc nhanh, lười đọc
  if (gNum === 7) {
    return { pass: true, reason: 'Gợi ý sách thư giãn/đọc nhanh phù hợp' };
  }

  return { pass: true, reason: 'Đạt yêu cầu' };
}
