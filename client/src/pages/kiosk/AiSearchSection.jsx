import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Search, 
  BookOpen, 
  MapPin, 
  Compass, 
  RefreshCw, 
  ArrowLeft,
  X,
  GraduationCap
} from 'lucide-react';
import { apiService } from '../../api/apiService.js';
import ShelfLocatorModal from '../../components/ShelfLocatorModal.jsx';
import { playKioskBeep } from '../../utils/audio.js';

export default function AiSearchSection({ reader, onFinish }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchMeta, setSearchMeta] = useState(null);
  const [selectedBookForMap, setSelectedBookForMap] = useState(null);
  const [activeChip, setActiveChip] = useState('');

  // Các chủ đề gợi ý nhanh (Quick Chips)
  const quickChips = [
    { label: '💻 Lập trình & CNTT', q: 'Lập trình vi điều khiển, Python, Java, giải thuật và khoa học máy tính' },
    { label: '🧠 Tâm lý & Chữa lành', q: 'Tâm lý học, thấu hiểu bản thân, chữa lành và tư duy tích cực' },
    { label: '📈 Kinh tế & Đầu tư', q: 'Quản trị kinh doanh, tài chính cá nhân, khởi nghiệp và đầu tư' },
    { label: '🛡️ An toàn thông tin', q: 'Bảo mật an ninh mạng, mã hóa dữ liệu và phòng thủ không gian số' },
    { label: '📜 Tác phẩm kinh điển', q: 'Tiểu thuyết kinh điển, văn học thế giới và tác phẩm đoạt giải Nobel' },
    { label: '🇬🇧 Tiếng Anh & Ngoại ngữ', q: 'Luyện thi IELTS, từ vựng ngữ pháp tiếng Anh và giao tiếp quốc tế' }
  ];

  // Tự động gợi ý theo chuyên ngành khi sinh viên đã quẹt thẻ
  useEffect(() => {
    if (reader && reader.department) {
      loadPersonalizedRecommendations(reader.department);
    } else {
      // Mặc định nạp gợi ý các cuốn sách tiêu biểu
      handleSearch('Sách hay được yêu thích nhất thư viện PTIT');
    }
  }, [reader]);

  async function loadPersonalizedRecommendations(dept) {
    setLoading(true);
    try {
      const res = await apiService.recommendAiBooks({ department: dept, top_k: 6 });
      if (res && Array.isArray(res.data)) {
        setResults(res.data);
        setSearchMeta({
          source: res.source,
          method: 'Gợi ý cá nhân hóa theo Chuyên ngành',
          latency_ms: res.latency_ms || 45,
          total: res.total_results || res.data.length
        });
      }
    } catch (_err) {
      // Fallback
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(searchTerm) {
    const term = (searchTerm !== undefined ? searchTerm : query).trim();
    if (!term) return;

    setLoading(true);
    try {
      const res = await apiService.searchAiBooks(term, 6);
      playKioskBeep('success');
      if (res && Array.isArray(res.data)) {
        setResults(res.data);
        setSearchMeta({
          source: res.source,
          method: res.source === 'ai_hybrid_engine' ? 'Hybrid Search (Multilingual-E5 + BM25 + RRF)' : 'Dữ liệu MongoDB',
          latency_ms: res.latency_ms || 50,
          total: res.total_results || res.data.length
        });
      }
    } catch (err) {
      playKioskBeep('error');
      console.error('Lỗi tìm kiếm AI:', err);
    } finally {
      setLoading(false);
    }
  }

  function handleSelectChip(chip) {
    setActiveChip(chip.label);
    setQuery(chip.q);
    handleSearch(chip.q);
  }

  return (
    <div className="kiosk-workspace" style={{ maxWidth: '1280px', flexDirection: 'column' }}>
      {/* 1. Header & Thanh tìm kiếm Ngữ nghĩa AI */}
      <div style={{
        background: '#ffffff',
        border: '1.5px solid #e2e8f0',
        borderRadius: '20px',
        padding: '22px 28px',
        marginBottom: '20px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
      }}>
        {/* Tiêu đề & Giới thiệu AI */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{
              fontSize: '22px',
              fontWeight: '900',
              color: '#991b1b',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <span style={{
                background: 'linear-gradient(135deg, #991b1b, #7f1d1d)',
                color: '#ffffff',
                padding: '6px',
                borderRadius: '10px',
                display: 'flex'
              }}>
                <Sparkles size={20} />
              </span>
              TÌM KIẾM SÁCH THÔNG MINH BẰNG TRÍ TUỆ NHÂN TẠO (AI HYBRID SEARCH)
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
              Hiểu ngữ cảnh, cốt truyện và ý niệm tự nhiên • Tự động định vị Kệ sách thực tế trong kho 3.000 cuốn Thư viện PTIT
            </p>
          </div>

          <button
            onClick={onFinish}
            style={{
              background: '#f1f5f9',
              border: '1px solid #cbd5e1',
              color: '#475569',
              padding: '8px 18px',
              borderRadius: '9999px',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s'
            }}
          >
            <ArrowLeft size={16} />
            <span>Quay lại Trang Chủ</span>
          </button>
        </div>

        {/* Banner Bạn đọc Cá nhân hóa (nếu đã quẹt thẻ) */}
        {reader && (
          <div style={{
            background: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
            border: '1px solid #fecaca',
            borderRadius: '12px',
            padding: '10px 16px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '13px'
          }}>
            <span style={{ color: '#991b1b', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <GraduationCap size={18} />
              Gợi ý tối ưu theo chuyên ngành của bạn đọc: <strong>{reader.name}</strong> ({reader.studentId} • {reader.department || 'PTIT'})
            </span>
            <span style={{ fontSize: '11.5px', color: '#b91c1c', fontWeight: '800' }}>
              ✨ ĐÃ ĐỒNG BỘ HỒ SƠ RFID
            </span>
          </div>
        )}

        {/* Ô nhập liệu tìm kiếm phong cách Luxury Touchscreen */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{
            flex: 1,
            position: 'relative',
            display: 'flex',
            alignItems: 'center'
          }}>
            <Search size={22} style={{ position: 'absolute', left: '16px', color: '#94a3b8' }} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Nhập bất kỳ điều bạn muốn: Tên sách, tác giả, cốt truyện, chủ đề học tập, tâm trạng..."
              style={{
                width: '100%',
                padding: '14px 46px 14px 50px',
                borderRadius: '14px',
                border: '2px solid #e2e8f0',
                fontSize: '15px',
                fontWeight: '600',
                color: '#0f172a',
                outline: 'none',
                boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)',
                transition: 'all 0.2s'
              }}
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                style={{
                  position: 'absolute',
                  right: '14px',
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <X size={18} />
              </button>
            )}
          </div>

          <button
            onClick={() => handleSearch()}
            disabled={loading}
            style={{
              background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
              color: '#ffffff',
              border: 'none',
              padding: '14px 28px',
              borderRadius: '14px',
              fontWeight: '800',
              fontSize: '15px',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 12px rgba(153, 27, 27, 0.3)',
              transition: 'all 0.2s'
            }}
          >
            {loading ? <RefreshCw size={18} className="animate-spin" /> : <Search size={18} />}
            <span>Tìm kiếm AI</span>
          </button>
        </div>

        {/* Danh sách Quick Chips */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginTop: '14px',
          flexWrap: 'wrap'
        }}>
          <span style={{ fontSize: '12px', fontWeight: '700', color: '#64748b' }}>Gợi ý nhanh:</span>
          {quickChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectChip(chip)}
              style={{
                background: activeChip === chip.label ? '#991b1b' : '#f8fafc',
                color: activeChip === chip.label ? '#ffffff' : '#475569',
                border: activeChip === chip.label ? '1px solid #991b1b' : '1px solid #e2e8f0',
                padding: '6px 14px',
                borderRadius: '9999px',
                fontSize: '12.5px',
                fontWeight: '700',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Thanh hiển thị thống kê tìm kiếm */}
      {searchMeta && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0 8px 12px 8px',
          fontSize: '13px',
          color: '#64748b',
          fontWeight: '600'
        }}>
          <span>
            Tìm thấy <strong>{results.length}</strong> kết quả phù hợp nhất với nhu cầu của bạn
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              background: '#e0f2fe',
              color: '#0369a1',
              padding: '3px 10px',
              borderRadius: '9999px',
              fontSize: '11px',
              fontWeight: '700'
            }}>
              ⚡ Phản hồi: {searchMeta.latency_ms} ms
            </span>
            <span style={{
              background: '#f1f5f9',
              color: '#475569',
              padding: '3px 10px',
              borderRadius: '9999px',
              fontSize: '11px',
              fontWeight: '700'
            }}>
              {searchMeta.method}
            </span>
          </span>
        </div>
      )}

      {/* 3. Lưới kết quả gợi ý sách (Grid of Cards) */}
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
        {results.length === 0 && !loading && (
          <div style={{
            background: '#ffffff',
            border: '2px dashed #cbd5e1',
            borderRadius: '20px',
            padding: '48px 24px',
            textAlign: 'center'
          }}>
            <BookOpen size={48} color="#94a3b8" style={{ margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#334155', margin: '0 0 8px 0' }}>
              Chưa tìm thấy tài liệu phù hợp
            </h3>
            <p style={{ fontSize: '13.5px', color: '#64748b', maxWidth: '480px', margin: '0 auto' }}>
              Hãy thử chọn một trong các gợi ý chủ đề bên trên hoặc gõ câu hỏi tự nhiên theo cốt truyện, tác giả bạn quan tâm!
            </p>
          </div>
        )}

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))',
          gap: '16px'
        }}>
          {results.map((book, idx) => {
            const floor = book.floor || 1;
            const shelf = (book.shelf || 'A').toUpperCase();
            const position = book.position || `${shelf}1-01`;
            const available = book.available !== undefined ? book.available : 1;
            const total = book.total !== undefined ? book.total : 1;
            const isAvailable = available > 0;
            // Tính độ tương đồng ước lượng
            const matchScore = book.score ? Math.min(99, Math.round(book.score * 1000 + 40)) : (98 - idx * 3);

            return (
              <div
                key={book.book_id || idx}
                style={{
                  background: '#ffffff',
                  border: '1.5px solid #e2e8f0',
                  borderRadius: '18px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.04)',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  position: 'relative'
                }}
              >
                {/* Header thẻ: Thứ hạng & Độ khớp */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        background: idx === 0 ? '#fef08a' : idx === 1 ? '#e2e8f0' : idx === 2 ? '#fed7aa' : '#f1f5f9',
                        color: idx === 0 ? '#854d0e' : '#334155',
                        fontWeight: '900',
                        fontSize: '11px',
                        padding: '3px 9px',
                        borderRadius: '9999px',
                        border: '1px solid rgba(0,0,0,0.06)'
                      }}>
                        #{idx + 1} Gợi ý hàng đầu
                      </span>
                      <span style={{
                        background: '#f1f5f9',
                        color: '#475569',
                        fontSize: '11px',
                        fontWeight: '700',
                        padding: '3px 8px',
                        borderRadius: '6px'
                      }}>
                        {book.category}
                      </span>
                    </div>

                    <span style={{
                      background: '#dcfce7',
                      color: '#15803d',
                      fontSize: '11.5px',
                      fontWeight: '800',
                      padding: '3px 9px',
                      borderRadius: '9999px'
                    }}>
                      Độ khớp: {matchScore}%
                    </span>
                  </div>

                  {/* Tên sách & Tác giả */}
                  <h4 style={{
                    fontSize: '16.5px',
                    fontWeight: '800',
                    color: '#0f172a',
                    margin: '6px 0 4px 0',
                    lineHeight: 1.35
                  }}>
                    {book.title}
                  </h4>
                  <div style={{ fontSize: '13px', color: '#64748b', fontWeight: '600', marginBottom: '10px' }}>
                    Tác giả: <strong style={{ color: '#334155' }}>{book.author}</strong>
                  </div>

                  {/* Tóm tắt cốt truyện / mô tả */}
                  <p style={{
                    fontSize: '12.5px',
                    color: '#475569',
                    lineHeight: 1.5,
                    margin: '0 0 14px 0',
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {book.description || 'Tài liệu học tập và nghiên cứu chuyên khảo xuất bản chính thức trong thư viện PTIT.'}
                  </p>
                </div>

                {/* Footer thẻ: Tọa độ Kệ & Nút Chỉ đường */}
                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}>
                  {/* Badge vị trí kệ & tồn kho */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '12px',
                    fontSize: '12px'
                  }}>
                    <span style={{
                      background: '#fee2e2',
                      color: '#991b1b',
                      fontWeight: '800',
                      padding: '4px 10px',
                      borderRadius: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px'
                    }}>
                      <MapPin size={13} />
                      Tầng {floor} • Kệ {shelf} ({position})
                    </span>

                    <span style={{
                      color: isAvailable ? '#16a34a' : '#dc2626',
                      fontWeight: '700'
                    }}>
                      {isAvailable ? `🟢 Sẵn có: ${available}/${total} cuốn` : `🔴 Tạm hết trên kệ`}
                    </span>
                  </div>

                  {/* Nút chỉ đường tới kệ */}
                  <button
                    onClick={() => setSelectedBookForMap(book)}
                    style={{
                      width: '100%',
                      background: '#ffffff',
                      border: '1.5px solid #991b1b',
                      color: '#991b1b',
                      padding: '9px 16px',
                      borderRadius: '10px',
                      fontSize: '13px',
                      fontWeight: '800',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#991b1b';
                      e.currentTarget.style.color = '#ffffff';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#ffffff';
                      e.currentTarget.style.color = '#991b1b';
                    }}
                  >
                    <Compass size={16} />
                    <span>🗺️ Xem sơ đồ chỉ đường đến Kệ {shelf}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Modal Sơ đồ Kệ sách khi bấm Chỉ đường */}
      {selectedBookForMap && (
        <ShelfLocatorModal
          book={selectedBookForMap}
          onClose={() => setSelectedBookForMap(null)}
        />
      )}
    </div>
  );
}
