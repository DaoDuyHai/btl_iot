import Book from '../models/Book.js';
import Reader from '../models/Reader.js';
import { catalogService } from '../services/catalogService.js';

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';

/**
 * Tìm kiếm sách bằng AI Semantic Hybrid Search
 * Có cơ chế Fail-Safe: Tự động fallback sang tìm kiếm MongoDB nếu AI service chưa bật
 */
export async function searchBooks(req, res, next) {
  try {
    const q = (req.query.q || '').trim();
    const topK = parseInt(req.query.top_k, 10) || 6;

    if (!q) {
      return res.status(400).json({ success: false, message: 'Nội dung tìm kiếm không được để trống' });
    }

    let aiData = null;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000); // 4s timeout

      const aiResponse = await fetch(`${AI_SERVICE_URL}/api/search?q=${encodeURIComponent(q)}&top_k=${topK}`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (aiResponse.ok) {
        aiData = await aiResponse.json();
      }
    } catch (_err) {
      // AI Service offline -> Tiếp tục fallback
    }

    // Nếu AI service phản hồi thành công
    if (aiData && Array.isArray(aiData.results)) {
      // Đối chiếu trạng thái mượn thực tế từ MongoDB
      const bookIds = aiData.results.map(r => r.book_id || r.work_id);
      const dbBooks = await Book.find({ bookId: { $in: bookIds }, isDeleted: { $ne: true } });
      const dbMap = {};
      dbBooks.forEach(b => {
        dbMap[b.bookId] = b;
      });

      const enrichedResults = aiData.results.map(item => {
        const bid = item.book_id || item.work_id;
        const dbBook = dbMap[bid];
        return {
          ...item,
          rfidTag: dbBook?.rfidTag || `RFID_${bid}`,
          status: dbBook?.status || (item.available > 0 ? 'available' : 'borrowed'),
          floor: dbBook?.floor || item.floor || 1,
          shelf: dbBook?.shelf || item.shelf || 'A',
          position: dbBook?.position || item.position || 'A1-01',
          available: dbBook?.availableCopies !== undefined ? dbBook.availableCopies : item.available,
          total: dbBook?.totalCopies !== undefined ? dbBook.totalCopies : item.total
        };
      });

      return res.json({
        success: true,
        source: 'ai_hybrid_engine',
        query: q,
        latency_ms: aiData.latency_ms,
        total_results: enrichedResults.length,
        data: enrichedResults
      });
    }

    // Fallback: Tìm kiếm chính xác cao từ In-Memory Catalog Service
    console.warn(`⚠️ [AI Gateway] AI Service không phản hồi tại ${AI_SERVICE_URL}, chuyển sang In-Memory Precision Catalog`);
    const fallbackBooks = catalogService.searchPrecision(q, topK);

    const formattedFallback = fallbackBooks.map((b, idx) => ({
      book_id: b.bookId || `B${String(idx + 1).padStart(4, '0')}`,
      title: b.title,
      author: b.author,
      category: b.category,
      subcategory: b.subcategory,
      description: b.description,
      score: 0.95 - idx * 0.05,
      rank: idx + 1,
      floor: b.floor || 1,
      shelf: b.shelf || 'A',
      position: b.position || 'A1-01',
      available: b.availableCopies !== undefined ? b.availableCopies : 1,
      total: b.totalCopies !== undefined ? b.totalCopies : 1,
      rfidTag: b.rfidTag || `RFID_${b.bookId}`,
      status: b.status || 'available'
    }));

    return res.json({
      success: true,
      source: 'catalog_precision_search',
      query: q,
      latency_ms: 2,
      total_results: formattedFallback.length,
      data: formattedFallback
    });
  } catch (err) {
    next(err);
  }
}

/**
 * Gợi ý sách cá nhân hóa theo chuyên ngành hoặc lịch sử bạn đọc
 */
export async function recommendBooks(req, res, next) {
  try {
    const studentId = req.query.studentId;
    let department = req.query.department || '';
    const topK = parseInt(req.query.top_k, 10) || 5;

    // Nếu truyền studentId -> lấy thông tin độc giả từ DB
    if (studentId) {
      const reader = await Reader.findOne({ studentId });
      if (reader && reader.department) {
        department = reader.department;
      }
    }

    let aiData = null;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const aiResponse = await fetch(
        `${AI_SERVICE_URL}/api/recommend?department=${encodeURIComponent(department)}&top_k=${topK}`,
        { signal: controller.signal }
      );
      clearTimeout(timeoutId);

      if (aiResponse.ok) {
        aiData = await aiResponse.json();
      }
    } catch (_err) {
      // AI Service offline -> fallback
    }

    if (aiData && Array.isArray(aiData.results)) {
      const bookIds = aiData.results.map(r => r.book_id || r.work_id);
      const dbBooks = await Book.find({ bookId: { $in: bookIds }, isDeleted: { $ne: true } });
      const dbMap = {};
      dbBooks.forEach(b => {
        dbMap[b.bookId] = b;
      });

      const enrichedResults = aiData.results.map(item => {
        const bid = item.book_id || item.work_id;
        const dbBook = dbMap[bid];
        return {
          ...item,
          rfidTag: dbBook?.rfidTag || `RFID_${bid}`,
          status: dbBook?.status || (item.available > 0 ? 'available' : 'borrowed'),
          floor: dbBook?.floor || item.floor || 1,
          shelf: dbBook?.shelf || item.shelf || 'A',
          position: dbBook?.position || item.position || 'A1-01',
          available: dbBook?.availableCopies !== undefined ? dbBook.availableCopies : item.available,
          total: dbBook?.totalCopies !== undefined ? dbBook.totalCopies : item.total
        };
      });

      return res.json({
        success: true,
        source: 'ai_hybrid_engine',
        department,
        total_results: enrichedResults.length,
        data: enrichedResults
      });
    }

    // Fallback: Gợi ý chính xác từ In-Memory Catalog Service
    const fallbackBooks = catalogService.searchPrecision(department || 'Sách hay tiêu biểu', topK);

    return res.json({
      success: true,
      source: 'catalog_precision_recommend',
      department,
      total_results: fallbackBooks.length,
      data: fallbackBooks.map((b, idx) => ({
        book_id: b.bookId,
        title: b.title,
        author: b.author,
        category: b.category,
        description: b.description,
        floor: b.floor || 1,
        shelf: b.shelf || 'A',
        position: b.position || 'A1-01',
        available: b.availableCopies !== undefined ? b.availableCopies : 1,
        total: b.totalCopies !== undefined ? b.totalCopies : 1,
        rfidTag: b.rfidTag || `RFID_${b.bookId}`,
        status: b.status || 'available',
        rank: idx + 1
      }))
    });
  } catch (err) {
    next(err);
  }
}

/**
 * Kiểm tra trạng thái và thống kê của AI Service
 */
export async function getAiStats(req, res, _next) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const aiResponse = await fetch(`${AI_SERVICE_URL}/api/stats`, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (aiResponse.ok) {
      const data = await aiResponse.json();
      return res.json({ success: true, isAiOnline: true, ...data });
    }
  } catch (_err) {
    // Offline
  }

  // Nếu AI offline, trả về thống kê từ MongoDB
  const totalBooks = await Book.countDocuments({ isDeleted: { $ne: true } });
  res.json({
    success: true,
    isAiOnline: false,
    status: 'fallback_mongodb',
    total_records: totalBooks,
    message: 'AI Service đang khởi động hoặc chưa bật. Đang sử dụng chế độ dự phòng MongoDB.'
  });
}

/**
 * Helper: Tạo phản hồi suy luận thông minh cục bộ khi không có Gemini API key
 */
function generateLocalAgentResponse(cleanMsg, candidateBooks) {
  const matchedIntent = catalogService.getMatchedIntent(cleanMsg);

  let intro = '';
  if (matchedIntent) {
    if (matchedIntent.intent === 'JAPANESE_LANG') {
      intro = 'Chào bạn! Học tiếng Nhật là một hành trình thú vị và mở ra rất nhiều cơ hội việc làm tại các tập đoàn công nghệ. Mình đã tìm trong kho giáo trình ngoại ngữ của thư viện PTIT và chọn ra các bộ sách ngữ pháp, từ vựng và luyện thi JLPT chuẩn nhất cho bạn:';
    } else if (matchedIntent.intent === 'ENGLISH_LANG') {
      intro = 'Chào bạn! Năng lực ngoại ngữ chính là chìa khóa mở ra cánh cửa tri thức quốc tế và cơ hội việc làm toàn cầu cho sinh viên PTIT. Mình gợi ý cho bạn các đầu sách rèn luyện ngữ pháp, từ vựng và luyện thi chứng chỉ IELTS/TOEIC hiệu quả nhất:';
    } else if (matchedIntent.intent === 'CHINESE_LANG') {
      intro = 'Chào bạn! Tiếng Trung/Hán ngữ đang là ngôn ngữ rất phổ biến trong giao thương và công nghệ. Dưới đây là các giáo trình chuẩn HSK và đàm thoại tiếng Hoa hiện có tại thư viện:';
    } else if (matchedIntent.intent === 'KOREAN_LANG') {
      intro = 'Chào bạn! Dưới đây là các đầu sách ngữ pháp và luyện thi TOPIK tiếng Hàn tiêu biểu được nhiều bạn đọc tại thư viện PTIT lựa chọn:';
    } else if (matchedIntent.intent === 'IT_PROGRAMMING') {
      intro = 'Chào bạn! Với sinh viên khối ngành Công nghệ Thông tin, việc nắm vững tư duy lập trình nền tảng và cập nhật công nghệ thực tế là vô cùng quan trọng. Dựa trên câu hỏi của bạn, mình đã chọn ra các giáo trình lập trình và thuật toán chuẩn nhất:';
    } else if (matchedIntent.intent === 'IOT_EMBEDDED') {
      intro = 'Chào bạn! Lĩnh vực IoT và Hệ thống nhúng đòi hỏi sự am hiểu cả về phần cứng mạch điện tử lẫn giao thức lập trình vi điều khiển. Mình đã tìm thấy những cuốn sách chuyên sâu về Arduino, ESP32 và giải pháp IoT thực tế đang có sẵn trên kệ:';
    } else if (matchedIntent.intent === 'CYBER_SECURITY') {
      intro = 'Chào bạn! An toàn thông tin và Phòng thủ không gian số là một trong những lĩnh vực chiến lược đòi hỏi tư duy phân tích rủi ro rất cao. Dưới đây là các tài liệu tiêu biểu về bảo mật mạng và mật mã học hiện có tại thư viện:';
    } else if (matchedIntent.intent === 'HEALING_PSYCHOLOGY') {
      intro = 'Chào bạn! Mình rất thấu hiểu cảm xúc của bạn. Những áp lực trong học tập, thi cử và cuộc sống đôi khi khiến chúng ta cảm thấy kiệt sức và bế tắc. Đừng quá khắt khe với bản thân nhé, một cuốn sách hay có thể trở thành người bạn lắng nghe và chữa lành tâm hồn tốt nhất. Mình đã chọn ra từ kho sách của thư viện những cuốn sách tâm lý và kỹ năng xoa dịu tinh thần phù hợp nhất cho bạn:';
    } else if (matchedIntent.intent === 'BUSINESS_FINANCE') {
      intro = 'Chào bạn! Tư duy quản trị tài chính và tinh thần khởi nghiệp sẽ mang lại cho bạn sự tự chủ vững vàng sau này. Dưới đây là những tác phẩm kinh điển về kinh tế, đầu tư cá nhân và xây dựng mô hình khởi nghiệp đổi mới sáng tạo:';
    } else if (matchedIntent.intent === 'LITERATURE_CLASSIC') {
      intro = 'Chào bạn! Đọc văn học kinh điển là cách tuyệt vời nhất để nuôi dưỡng sự đồng cảm, thế giới quan sâu sắc và thưởng thức nghệ thuật ngôn từ. Dưới đây là những áng văn chương bất hủ có mặt tại thư viện PTIT:';
    }
  }

  if (!intro) {
    intro = `Chào bạn! Mình đã lắng nghe câu hỏi của bạn về "${cleanMsg}". Để giúp bạn có góc nhìn toàn diện và tài liệu tham khảo chính xác nhất, mình đã rà soát kho 3.000 đầu sách của thư viện và chọn ra những ấn phẩm tiêu biểu sau:`;
  }

  const selectedBooks = candidateBooks.slice(0, 4).map((b, idx) => ({
    book_id: b.bookId,
    title: b.title,
    author: b.author,
    category: b.category,
    subcategory: b.subcategory,
    description: b.description,
    shelf: b.shelf || 'A',
    floor: b.floor || 1,
    position: b.position || 'A1-01',
    available: b.availableCopies !== undefined ? b.availableCopies : 1,
    total: b.totalCopies !== undefined ? b.totalCopies : 1,
    status: b.status || 'available',
    rfidTag: b.rfidTag || `RFID_${b.bookId}`,
    rank: idx + 1
  }));

  return {
    reply: intro,
    books: selectedBooks
  };
}

/**
 * Trò chuyện trực tiếp cùng Thủ Thư AI (Conversational Agentic RAG)
 * Tích hợp Google Gemini API + Local Semantic Context Reasoner
 */
export async function chatWithAgent(req, res, next) {
  try {
    const { message, history = [], studentInfo = {}, apiKey } = req.body;
    const cleanMsg = (message || '').trim();

    if (!cleanMsg) {
      return res.status(400).json({ success: false, message: 'Nội dung tin nhắn không được để trống' });
    }

    const geminiKey = apiKey || process.env.GEMINI_API_KEY || '';
    const studentContext = studentInfo?.name ? `[Hồ sơ bạn đọc: ${studentInfo.name} - Khoa ${studentInfo.department || 'PTIT'}] ` : '';

    // 1. Truy vấn ứng viên chính xác từ In-Memory Catalog Service (3.000 sách)
    const candidateBooks = catalogService.searchPrecision(cleanMsg, 12);

    // 2. Nếu có GEMINI_API_KEY -> Sử dụng mô hình Google Gemini 1.5 Flash (Agentic RAG)
    if (geminiKey) {
      try {
        const booksContext = candidateBooks.map((b, idx) => 
          `[${idx + 1}] Mã: ${b.bookId} | Tựa đề: "${b.title}" | Tác giả: ${b.author} | Thể loại: ${b.category} (${b.subcategory || ''}) | Vị trí thực tế: Kệ ${b.shelf}, Tầng ${b.floor}, Ô ${b.position} | Tóm tắt: ${b.description ? b.description.slice(0, 140) : 'Chưa có tóm tắt'}`
        ).join('\n');

        const systemInstruction = `Bạn là "Thủ thư Ảo AI - Học viện Công nghệ Bưu chính Viễn thông (PTIT)".
Bạn có phong cách tư vấn: Thân thiện, tâm lý, hiểu biết sâu rộng, nói chuyện tự nhiên bằng tiếng Việt như một người anh/chị khóa trên hoặc thủ thư tận tâm.
Nhiệm vụ của bạn:
1. Đọc kỹ tâm sự hoặc câu hỏi của sinh viên.
2. Viết phản hồi khoảng 2-3 câu ngắn gọn, thể hiện sự đồng cảm, hiểu rõ bối cảnh và định hướng cho sinh viên.
3. Chọn ra từ 2 đến 4 cuốn sách PHÙ HỢP NHẤT trong danh sách sách có sẵn ở thư viện PTIT được cung cấp dưới đây.
4. Với mỗi cuốn sách được chọn, giải thích 1 câu ngắn gọn lý do vì sao cuốn sách này sẽ giúp ích cho bạn ấy.
5. Luôn kèm mã sách (ví dụ: [B0123]) để hệ thống Kiosk hiển thị thẻ sách và bản đồ vị trí Kệ.

DANH MỤC SÁCH THỰC TẾ TRONG KHO 3.000 CUỐN CỦA THƯ VIỆN PTIT:
${booksContext}`;

        const payload = {
          contents: [
            ...history.slice(-4).map(h => ({
              role: h.role === 'user' ? 'user' : 'model',
              parts: [{ text: h.text }]
            })),
            {
              role: 'user',
              parts: [{ text: `${systemInstruction}\n\n${studentContext}Sinh viên hỏi: "${cleanMsg}"` }]
            }
          ],
          generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 500
          }
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000); // 8s timeout

        const geminiRes = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: controller.signal
          }
        );
        clearTimeout(timeoutId);

        if (geminiRes.ok) {
          const geminiData = await geminiRes.json();
          const replyText = geminiData.candidates?.[0]?.content?.parts?.[0]?.text;
          
          if (replyText) {
            // Lọc ra các cuốn sách được Gemini nhắc tên hoặc mã
            const matchedIds = (replyText.match(/B\d{4}/g) || []);
            const recommendedBooks = candidateBooks.filter(b => 
              matchedIds.includes(b.bookId) || replyText.toLowerCase().includes(b.title.toLowerCase())
            );

            const finalBooks = (recommendedBooks.length > 0 ? recommendedBooks : candidateBooks.slice(0, 3)).map((b, idx) => ({
              book_id: b.bookId,
              title: b.title,
              author: b.author,
              category: b.category,
              subcategory: b.subcategory,
              description: b.description,
              shelf: b.shelf || 'A',
              floor: b.floor || 1,
              position: b.position || 'A1-01',
              available: b.availableCopies !== undefined ? b.availableCopies : 1,
              total: b.totalCopies !== undefined ? b.totalCopies : 1,
              status: b.status || 'available',
              rfidTag: b.rfidTag,
              rank: idx + 1
            }));

            return res.json({
              success: true,
              source: 'gemini_agent',
              model: 'Google Gemini 1.5 Flash (Agentic RAG)',
              reply: replyText,
              books: finalBooks
            });
          }
        }
      } catch (err) {
        console.warn('⚠️ [AI Gateway] Gemini API không phản hồi, chuyển sang Local Reasoning Agent:', err.message);
      }
    }

    // 3. Fallback: Động cơ suy luận ngữ cảnh cục bộ (Local Context Reasoner)
    const localResult = generateLocalAgentResponse(cleanMsg, candidateBooks);
    return res.json({
      success: true,
      source: 'local_smart_agent',
      model: 'PTIT Local Semantic Reasoner (RAG)',
      reply: localResult.reply,
      books: localResult.books
    });
  } catch (err) {
    next(err);
  }
}
