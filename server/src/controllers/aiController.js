import Book from '../models/Book.js';
import Reader from '../models/Reader.js';

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

    // Fallback: Tìm kiếm từ khóa trực tiếp từ MongoDB (Zero downtime)
    console.warn(`⚠️ [AI Gateway] AI Service không phản hồi tại ${AI_SERVICE_URL}, chuyển sang chế độ dự phòng MongoDB`);
    const regex = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
    const fallbackBooks = await Book.find({
      isDeleted: { $ne: true },
      $or: [
        { title: regex },
        { author: regex },
        { category: regex },
        { description: regex }
      ]
    }).limit(topK);

    const formattedFallback = fallbackBooks.map((b, idx) => ({
      book_id: b.bookId || `B${String(idx + 1).padStart(4, '0')}`,
      title: b.title,
      author: b.author,
      category: b.category,
      subcategory: b.subcategory,
      description: b.description,
      score: 0.85 - idx * 0.05,
      rank: idx + 1,
      floor: b.floor || 1,
      shelf: b.shelf || 'A',
      position: b.position || 'A1-01',
      available: b.availableCopies || 1,
      total: b.totalCopies || 1,
      rfidTag: b.rfidTag,
      status: b.status
    }));

    res.json({
      success: true,
      source: 'mongodb_fallback',
      query: q,
      latency_ms: 10,
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

    // Fallback: Lấy sách ngẫu nhiên/nổi bật từ MongoDB
    const fallbackBooks = await Book.find({
      status: 'available',
      isDeleted: { $ne: true }
    }).limit(topK);

    res.json({
      success: true,
      source: 'mongodb_fallback',
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
        available: b.availableCopies || 1,
        total: b.totalCopies || 1,
        rfidTag: b.rfidTag,
        status: b.status,
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
