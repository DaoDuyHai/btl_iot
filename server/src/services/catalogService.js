import fs from 'fs';
import path from 'path';

function stripAccents(str) {
  if (!str) return '';
  return str.normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd').replace(/Đ/g, 'D')
    .toLowerCase();
}

function cleanText(str) {
  if (!str) return '';
  return str.toLowerCase().trim();
}

// Từ điển ngữ nghĩa chuyên sâu (Semantic Intent Knowledge Graph)
const SEMANTIC_INTENTS = [
  {
    intent: 'JAPANESE_LANG',
    triggers: ['tieng nhat', 'tiếng nhật', 'nhat ban', 'nhật bản', 'jlpt', 'nihongo', 'minna'],
    keywords: ['tiếng nhật', 'nhật', 'từ vựng tiếng nhật', 'ngữ pháp tiếng nhật', 'luyện thi tiếng nhật', 'tiếng nhật giao tiếp'],
    targetSubcats: ['Từ Vựng Tiếng Nhật', 'Luyện thi Tiếng Nhật', 'Ngữ pháp Tiếng Nhật', 'Tiếng Nhật Giao Tiếp'],
    targetCategories: ['Giáo dục – Ngoại ngữ']
  },
  {
    intent: 'ENGLISH_LANG',
    triggers: ['tieng anh', 'tiếng anh', 'ielts', 'toeic', 'toefl', 'english', 'grammar', 'vocabulary'],
    keywords: ['tiếng anh', 'ielts', 'toeic', 'toefl', 'ngữ pháp tiếng anh', 'từ vựng tiếng anh', 'tiếng anh giao tiếp'],
    targetSubcats: ['Tiếng Anh', 'Luyện thi IELTS', 'Luyện thi TOEIC', 'Ngữ pháp Tiếng Anh', 'Từ Vựng Tiếng Anh', 'Tiếng Anh giao tiếp'],
    targetCategories: ['Giáo dục – Ngoại ngữ']
  },
  {
    intent: 'CHINESE_LANG',
    triggers: ['tieng hoa', 'tiếng hoa', 'tieng trung', 'tiếng trung', 'hsk', 'han ngu', 'hán ngữ'],
    keywords: ['tiếng hoa', 'tiếng trung', 'hsk', 'hán ngữ', 'luyện thi tiếng hoa hsk'],
    targetSubcats: ['Luyện thi Tiếng Hoa HSK', 'Tiếng Hoa Giao Tiếp', 'Giáo trình Hán ngữ'],
    targetCategories: ['Giáo dục – Ngoại ngữ']
  },
  {
    intent: 'KOREAN_LANG',
    triggers: ['tieng han', 'tiếng hàn', 'topik', 'tieng trieu tien'],
    keywords: ['tiếng hàn', 'topik', 'ngữ pháp tiếng hàn', 'giao tiếp tiếng hàn'],
    targetSubcats: ['Ngữ pháp Tiếng Hàn', 'Luyện thi TOPIK', 'Giao tiếp Tiếng Hàn'],
    targetCategories: ['Giáo dục – Ngoại ngữ']
  },
  {
    intent: 'IT_PROGRAMMING',
    triggers: ['lap trinh', 'lập trình', 'python', 'java', 'c++', 'c/c++', 'code', 'thuat toan', 'thuật toán', 'phan mem', 'phần mềm', 'web', 'backend', 'frontend', 'ai', 'tri tue nhan tao', 'học máy', 'machine learning', 'khoa hoc may tinh'],
    keywords: ['lập trình', 'python', 'java', 'c/c++', 'thuật toán', 'phần mềm', 'học máy', 'ai'],
    targetSubcats: ['Lập Trình', 'Tin Học Văn Phòng', 'Khoa học máy tính'],
    targetCategories: ['Công nghệ thông tin']
  },
  {
    intent: 'IOT_EMBEDDED',
    triggers: ['iot', 'vi dieu khien', 'vi điều khiển', 'esp32', 'arduino', 'nhung', 'nhúng', 'cam bien', 'cảm biến', 'mach dien tu', 'mạch điện tử', 'dien tu', 'điện tử', 'vien thong', 'viễn thông'],
    keywords: ['iot', 'vi điều khiển', 'esp32', 'arduino', 'mạng máy tính', 'viễn thông', 'hệ thống nhúng'],
    targetSubcats: ['Điện tử viễn thông', 'IoT & Phần cứng', 'Mạng viễn thông'],
    targetCategories: ['Khoa học – Công nghệ', 'Công nghệ thông tin']
  },
  {
    intent: 'CYBER_SECURITY',
    triggers: ['an toan thong tin', 'an toàn thông tin', 'bao mat', 'bảo mật', 'an ninh mang', 'an ninh mạng', 'hack', 'mat ma', 'mật mã'],
    keywords: ['an toàn thông tin', 'bảo mật', 'an ninh mạng', 'mật mã học'],
    targetSubcats: ['An toàn thông tin', 'Mạng máy tính'],
    targetCategories: ['Công nghệ thông tin']
  },
  {
    intent: 'HEALING_PSYCHOLOGY',
    triggers: ['stress', 'mat ngu', 'mất ngủ', 'ap luc', 'áp lực', 'chua lanh', 'chữa lành', 'buon', 'buồn', 'chan', 'chán', 'chia tay', 'met moi', 'mệt mỏi', 'be tac', 'bế tắc', 'tam ly', 'tâm lý', 'ton thuong', 'tổn thương', 'vo dinh', 'vô định'],
    keywords: ['tâm lý', 'chữa lành', 'áp lực', 'cảm xúc', 'bình an', 'thấu hiểu', 'tự chữa lành', 'tư duy tích cực'],
    targetSubcats: ['Tâm lý học', 'Tư duy tích cực', 'Kỹ năng sống'],
    targetCategories: ['Tâm lý học', 'Kỹ năng sống – Phát triển bản thân']
  },
  {
    intent: 'BUSINESS_FINANCE',
    triggers: ['kinh doanh', 'lam giau', 'làm giàu', 'dau tu', 'đầu tư', 'khoi nghiep', 'khởi nghiệp', 'tai chinh', 'tài chính', 'chung khoan', 'chứng khoán', 'marketing', 'tien', 'tiền'],
    keywords: ['kinh doanh', 'làm giàu', 'đầu tư', 'tài chính', 'khởi nghiệp', 'quản trị'],
    targetSubcats: ['Đầu tư', 'Marketing', 'Quản trị kinh doanh', 'Khởi nghiệp', 'Tài chính cá nhân'],
    targetCategories: ['Kinh tế – Kinh doanh']
  },
  {
    intent: 'LITERATURE_CLASSIC',
    triggers: ['van hoc', 'văn học', 'tieu thuyet', 'tiểu thuyết', 'truyen', 'truyện', 'kinh dien', 'kinh điển', 'doat giai', 'nobel'],
    keywords: ['tiểu thuyết', 'văn học', 'tác phẩm kinh điển', 'truyện ngắn'],
    targetSubcats: ['Tác phẩm kinh điển', 'Tiểu Thuyết', 'Truyện dài'],
    targetCategories: ['Văn học – Tiểu thuyết']
  }
];

function parseCSV(content) {
  const lines = [];
  let row = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < content.length; i++) {
    const char = content[i];
    const next = content[i + 1];
    if (char === '"') {
      if (inQuotes && next === '"') { current += '"'; i++; }
      else { inQuotes = !inQuotes; }
    } else if (char === ',' && !inQuotes) {
      row.push(current);
      current = '';
    } else if ((char === '\r' || char === '\n') && !inQuotes) {
      if (char === '\r' && next === '\n') i++;
      row.push(current);
      if (row.some(c => c.trim().length > 0)) lines.push(row);
      row = [];
      current = '';
    } else {
      current += char;
    }
  }
  if (current || row.length > 0) {
    row.push(current);
    if (row.some(c => c.trim().length > 0)) lines.push(row);
  }
  return lines;
}

class CatalogService {
  constructor() {
    this.books = [];
    this.isLoaded = false;
    this.loadCatalog();
  }

  loadCatalog() {
    try {
      const candidates = [
        path.resolve('ai-service/dataset/cleaned_books_dataset.csv'),
        path.resolve('../ai-service/dataset/cleaned_books_dataset.csv'),
        path.resolve('dataset/cleaned_books_dataset.csv')
      ];

      let csvPath = '';
      for (const p of candidates) {
        if (fs.existsSync(p)) {
          csvPath = p;
          break;
        }
      }

      if (!csvPath) {
        console.warn('⚠️ [CatalogService] Không tìm thấy file cleaned_books_dataset.csv');
        return;
      }

      const content = fs.readFileSync(csvPath, 'utf-8');
      const rows = parseCSV(content);
      if (rows.length < 2) return;

      const header = rows[0].map(h => h.trim().replace(/^\uFEFF/, ''));
      this.books = rows.slice(1).map(r => {
        const obj = {};
        header.forEach((h, idx) => { obj[h] = r[idx] || ''; });

        return {
          bookId: obj.Book_ID || '',
          title: obj.Title || '',
          author: obj.Author || '',
          category: obj.Category || '',
          subcategory: obj.Subcategory || '',
          description: obj.Description || '',
          keywords: obj.Keywords || '',
          publisher: obj.Publisher || '',
          publicationYear: parseInt(obj.Publication_Year, 10) || 2023,
          shelf: (obj.Shelf || 'A').toUpperCase(),
          floor: parseInt(obj.Floor, 10) || 1,
          position: obj.Position || 'A1-01',
          totalCopies: parseInt(obj.Total_Copies, 10) || 5,
          availableCopies: parseInt(obj.Available_Copies, 10) || 3,
          rfidTag: `RFID_${obj.Book_ID}`,
          status: (parseInt(obj.Available_Copies, 10) || 0) > 0 ? 'available' : 'borrowed',
          // Trường tra cứu chuẩn hóa tốc độ cao
          _normTitle: cleanText(obj.Title),
          _unaccTitle: stripAccents(obj.Title),
          _normAuthor: cleanText(obj.Author),
          _unaccAuthor: stripAccents(obj.Author),
          _normCat: cleanText(obj.Category),
          _normSubcat: cleanText(obj.Subcategory),
          _unaccSubcat: stripAccents(obj.Subcategory),
          _normKeywords: cleanText(obj.Keywords),
          _normDesc: cleanText(obj.Description)
        };
      });

      this.isLoaded = true;
      console.log(`✅ [CatalogService] Đã nạp thành công ${this.books.length} sách thực tế vào In-Memory Semantic Index.`);
    } catch (err) {
      console.error('❌ [CatalogService] Lỗi khi nạp catalog:', err);
    }
  }

  /**
   * Thuật toán tìm kiếm chính xác đa tầng (Precision Intelligent Search)
   */
  searchPrecision(query, topK = 6) {
    if (!query || !query.trim() || this.books.length === 0) {
      return this.books.slice(0, topK);
    }

    const qClean = cleanText(query);
    const qUnacc = stripAccents(query);

    // 1. Nhận diện Semantic Intent
    const matchedIntents = [];
    for (const item of SEMANTIC_INTENTS) {
      for (const trig of item.triggers) {
        if (qClean.includes(trig) || qUnacc.includes(trig)) {
          matchedIntents.push(item);
          break;
        }
      }
    }

    // 2. Chấm điểm từng cuốn sách
    const scored = [];

    for (const b of this.books) {
      let score = 0;

      // A. Khớp chính xác cụm từ (Exact Phrase Match)
      if (b._normTitle.includes(qClean) || b._unaccTitle.includes(qUnacc)) {
        score += 200;
      }
      if (b._normSubcat.includes(qClean) || b._unaccSubcat.includes(qUnacc)) {
        score += 150;
      }
      if (b._normKeywords.includes(qClean)) {
        score += 80;
      }
      if (b._normDesc.includes(qClean)) {
        score += 25;
      }

      // B. Khớp Intent ngữ nghĩa (Semantic Intent Weighting)
      for (const intent of matchedIntents) {
        if (intent.targetCategories.some(tc => b.category.includes(tc))) {
          score += 100;
        }
        if (intent.targetSubcats.some(ts => b.subcategory.includes(ts))) {
          score += 160;
        }
        for (const kw of intent.keywords) {
          if (b._normTitle.includes(kw)) score += 60;
          if (b._normSubcat.includes(kw)) score += 50;
          if (b._normKeywords.includes(kw)) score += 25;
        }
      }

      // C. Khớp theo từng từ đơn có chọn lọc (Tokenized Matching)
      const qTokens = qClean.split(/\s+/).filter(w => 
        w.length > 2 && !['sách', 'cuốn', 'tìm', 'cho', 'mình', 'em', 'tôi', 'bạn', 'muốn', 'đang', 'nhé', 'giúp'].includes(w)
      );
      for (const token of qTokens) {
        if (b._normTitle.includes(token)) score += 20;
        if (b._normAuthor.includes(token)) {
          if (matchedIntents.length === 0 || token.length > 4) {
            score += 15;
          }
        }
        if (b._normKeywords.includes(token)) score += 10;
      }

      // D. Khử nhiễu: Ngăn chặn tác giả hoặc truyện văn học tình cờ chứa từ khoá ngoại ngữ
      if (matchedIntents.some(i => i.intent === 'JAPANESE_LANG' || i.intent === 'ENGLISH_LANG' || i.intent === 'CHINESE_LANG' || i.intent === 'KOREAN_LANG')) {
        if (b.category.includes('Văn học') && !b.category.includes('Ngoại ngữ') && !b.subcategory.includes('Ngoại ngữ')) {
          score -= 150;
        }
      }

      if (score > 0) {
        scored.push({ book: b, score });
      }
    }

    if (scored.length === 0) {
      return this.books.slice(0, topK);
    }

    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, topK).map(s => s.book);
  }

  getMatchedIntent(query) {
    const qClean = cleanText(query);
    const qUnacc = stripAccents(query);
    for (const item of SEMANTIC_INTENTS) {
      for (const trig of item.triggers) {
        if (qClean.includes(trig) || qUnacc.includes(trig)) {
          return item;
        }
      }
    }
    return null;
  }
}

export const catalogService = new CatalogService();
