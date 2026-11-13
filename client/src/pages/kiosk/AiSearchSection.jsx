import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  Search, 
  MapPin, 
  Compass, 
  RefreshCw, 
  ArrowLeft,
  X,
  Bot,
  Send,
  MessageSquare,
  Key
} from 'lucide-react';
import { apiService } from '../../api/apiService.js';
import ShelfLocatorModal from '../../components/ShelfLocatorModal.jsx';
import { playKioskBeep } from '../../utils/audio.js';

export default function AiSearchSection({ reader, onFinish }) {
  // Chế độ: 'agent' (Trò chuyện tư vấn AI) hoặc 'search' (Tra cứu nhanh từ khóa)
  const [activeTab, setActiveTab] = useState('agent');
  
  // State của Chế độ Trò chuyện Agent
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'welcome',
      role: 'agent',
      text: 'Xin chào! Mình là Thủ thư Ảo AI của Học viện PTIT 🤖. Bạn đang có tâm sự, băn khoăn về môn học, chuyên ngành hay muốn tìm một cuốn sách đặc biệt nào không? Hãy chia sẻ với mình nhé, mình sẽ lắng nghe và chỉ đường đến tận kệ sách cho bạn!',
      books: [],
      model: 'PTIT AI Librarian Agent'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isAgentReplying, setIsAgentReplying] = useState(false);
  const chatBottomRef = useRef(null);

  // Cấu hình Gemini API Key tùy chọn (lưu tại localStorage máy Kiosk)
  const [geminiApiKey, setGeminiApiKey] = useState(() => localStorage.getItem('ptit_gemini_api_key') || '');
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [tempKey, setTempKey] = useState('');

  // State của Chế độ Tra cứu nhanh
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchMeta, setSearchMeta] = useState(null);

  // Modal sơ đồ chỉ đường đến kệ
  const [selectedBookForMap, setSelectedBookForMap] = useState(null);

  // Câu hỏi mẫu thông minh (Quick Prompts)
  const quickPrompts = [
    { label: '🧠 Đang stress, mất ngủ & áp lực thi cử', prompt: 'Dạo này em hay bị mất ngủ, áp lực học tập và cảm thấy bế tắc, có cuốn sách nào giúp xoa dịu và chữa lành không?' },
    { label: '💻 Sinh viên CNTT tìm sách lập trình & IoT', prompt: 'Em là sinh viên ngành CNTT, muốn tìm sách về lập trình, giải thuật và phát triển hệ thống IoT thực tế.' },
    { label: '🚀 Khởi nghiệp & Quản trị tài chính cá nhân', prompt: 'Gợi ý cho mình các cuốn sách về tư duy tài chính, đầu tư và khởi nghiệp đổi mới sáng tạo cho sinh viên.' },
    { label: '🛡️ Bảo mật mạng & An toàn thông tin', prompt: 'Em muốn tìm hiểu chuyên sâu về an toàn thông tin, bảo mật an ninh mạng và mật mã học.' },
    { label: '💔 Sách tâm lý vượt qua nỗi buồn tình cảm', prompt: 'Tâm sự với thủ thư: Em vừa mới chia tay người yêu, tâm trạng rất tệ, muốn đọc cuốn sách giúp buông bỏ và yêu thương bản thân.' },
    { label: '🇬🇧 Lộ trình tự học tiếng Anh & luyện thi IELTS', prompt: 'Tư vấn giúp em phương pháp tự học tiếng Anh hiệu quả và sách luyện thi chứng chỉ quốc tế.' }
  ];

  // Cuộn xuống tin nhắn mới nhất
  useEffect(() => {
    if (activeTab === 'agent') {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isAgentReplying, activeTab]);

  // Tự động chào theo chuyên ngành khi sinh viên đã quẹt thẻ RFID
  useEffect(() => {
    if (reader && reader.name) {
      setChatMessages(prev => {
        if (prev.some(m => m.id === 'reader_welcome')) return prev;
        return [
          ...prev,
          {
            id: 'reader_welcome',
            role: 'agent',
            text: `Chào bạn ${reader.name} (${reader.studentId} • Khoa ${reader.department || 'PTIT'})! Mình đã nhận diện hồ sơ bạn đọc của bạn qua đầu đọc RFID. Bạn đang cần hỗ trợ tài liệu học tập cho kỳ này hay muốn tìm sách đọc giải trí thư giãn?`,
            books: [],
            model: 'PTIT AI Librarian Agent'
          }
        ];
      });
    }
  }, [reader]);

  // Gửi tin nhắn trò chuyện tới AI Agent
  async function handleSendMessage(customText) {
    const textToSend = (customText || inputMessage).trim();
    if (!textToSend || isAgentReplying) return;

    playKioskBeep('success');
    const userMsg = {
      id: `user_${Date.now()}`,
      role: 'user',
      text: textToSend
    };

    setChatMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsAgentReplying(true);

    try {
      const historyPayload = chatMessages
        .filter(m => m.id !== 'welcome' && m.id !== 'reader_welcome')
        .slice(-4)
        .map(m => ({
          role: m.role === 'user' ? 'user' : 'model',
          text: m.text
        }));

      const res = await apiService.chatWithAiLibrarian({
        message: textToSend,
        history: historyPayload,
        studentInfo: reader ? { name: reader.name, department: reader.department } : {},
        apiKey: geminiApiKey
      });

      if (res && res.success) {
        const agentMsg = {
          id: `agent_${Date.now()}`,
          role: 'agent',
          text: res.reply || 'Dưới đây là một số tựa sách mình gợi ý cho bạn:',
          books: Array.isArray(res.books) ? res.books : [],
          model: res.model || (res.source === 'gemini_agent' ? 'Google Gemini 1.5 Flash' : 'PTIT Local Semantic Reasoner')
        };
        setChatMessages(prev => [...prev, agentMsg]);
      } else {
        throw new Error(res?.message || 'Không nhận được phản hồi từ AI');
      }
    } catch (err) {
      console.error('Lỗi trò chuyện cùng AI Agent:', err);
      playKioskBeep('error');
      setChatMessages(prev => [
        ...prev,
        {
          id: `agent_err_${Date.now()}`,
          role: 'agent',
          text: 'Xin lỗi bạn, kết nối tới dịch vụ AI đang bị gián đoạn. Bạn hãy thử chọn lại câu hỏi mẫu hoặc chuyển sang mục Tìm kiếm nhanh bên cạnh nhé!',
          books: [],
          model: 'System Error Fallback'
        }
      ]);
    } finally {
      setIsAgentReplying(false);
    }
  }

  // Xử lý tìm kiếm nhanh (Fast Search)
  async function handleFastSearch(searchTerm) {
    const term = (searchTerm !== undefined ? searchTerm : query).trim();
    if (!term) return;

    setIsSearching(true);
    playKioskBeep('success');
    try {
      const res = await apiService.searchAiBooks(term, 8);
      if (res && Array.isArray(res.data)) {
        setSearchResults(res.data);
        setSearchMeta({
          source: res.source,
          method: res.source === 'ai_hybrid_engine' ? 'Hybrid Search (Multilingual-E5 + BM25 + RRF)' : 'BM25Okapi Search Engine',
          latency_ms: res.latency_ms || 45,
          total: res.total_results || res.data.length
        });
      }
    } catch (err) {
      console.error('Lỗi tìm kiếm nhanh:', err);
      playKioskBeep('error');
    } finally {
      setIsSearching(false);
    }
  }

  function handleSaveApiKey() {
    const key = tempKey.trim();
    setGeminiApiKey(key);
    if (key) {
      localStorage.setItem('ptit_gemini_api_key', key);
    } else {
      localStorage.removeItem('ptit_gemini_api_key');
    }
    setShowKeyModal(false);
    playKioskBeep('success');
  }

  return (
    <div className="kiosk-workspace" style={{ maxWidth: '1280px', flexDirection: 'column', height: '100%' }}>
      {/* 1. Header Chính */}
      <div style={{
        background: '#ffffff',
        border: '1.5px solid #e2e8f0',
        borderRadius: '20px',
        padding: '18px 24px',
        marginBottom: '16px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #991b1b, #7f1d1d)',
            color: '#ffffff',
            padding: '12px',
            borderRadius: '16px',
            display: 'flex',
            boxShadow: '0 4px 12px rgba(153, 27, 27, 0.3)'
          }}>
            <Bot size={28} />
          </div>
          <div>
            <h2 style={{
              fontSize: '20px',
              fontWeight: '900',
              color: '#991b1b',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              THỦ THƯ ẢO AI - HỌC VIỆN PTIT
              <span style={{
                background: '#fef2f2',
                color: '#b91c1c',
                fontSize: '11px',
                padding: '2px 8px',
                borderRadius: '9999px',
                border: '1px solid #fecaca',
                fontWeight: '800'
              }}>
                AGENTIC RAG 2026
              </span>
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '3px 0 0' }}>
              Thấu hiểu ngữ cảnh tự nhiên • Tư vấn thông minh từ kho 3.000 cuốn • Tự động định vị Kệ sách thực tế
            </p>
          </div>
        </div>

        {/* Cụm công cụ bên phải */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Nút Cấu hình Gemini Key */}
          <button
            onClick={() => { setTempKey(geminiApiKey); setShowKeyModal(true); }}
            style={{
              background: geminiApiKey ? '#ecfdf5' : '#f8fafc',
              border: geminiApiKey ? '1px solid #a7f3d0' : '1px solid #cbd5e1',
              color: geminiApiKey ? '#047857' : '#64748b',
              padding: '8px 14px',
              borderRadius: '9999px',
              fontSize: '12px',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s'
            }}
            title="Cấu hình Google Gemini API Key"
          >
            <Key size={14} />
            <span>{geminiApiKey ? 'Google Gemini: Đã bật' : 'Chế độ: Local Semantic'}</span>
          </button>

          {/* Tab chuyển đổi chế độ */}
          <div style={{
            background: '#f1f5f9',
            padding: '4px',
            borderRadius: '9999px',
            display: 'flex',
            gap: '4px'
          }}>
            <button
              onClick={() => setActiveTab('agent')}
              style={{
                background: activeTab === 'agent' ? '#991b1b' : 'transparent',
                color: activeTab === 'agent' ? '#ffffff' : '#64748b',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '9999px',
                fontSize: '12.5px',
                fontWeight: '800',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.2s'
              }}
            >
              <MessageSquare size={14} />
              <span>Trò chuyện AI</span>
            </button>

            <button
              onClick={() => {
                setActiveTab('search');
                if (searchResults.length === 0) handleFastSearch('Sách nổi bật');
              }}
              style={{
                background: activeTab === 'search' ? '#991b1b' : 'transparent',
                color: activeTab === 'search' ? '#ffffff' : '#64748b',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '9999px',
                fontSize: '12.5px',
                fontWeight: '800',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.2s'
              }}
            >
              <Search size={14} />
              <span>Tra cứu nhanh</span>
            </button>
          </div>

          {/* Nút Quay lại */}
          <button
            onClick={onFinish}
            style={{
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              color: '#334155',
              padding: '8px 16px',
              borderRadius: '9999px',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <ArrowLeft size={15} />
            <span>Thoát</span>
          </button>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* TAB 1: TRÒ CHUYỆN CÙNG THỦ THƯ AI (CONVERSATIONAL AGENT MODE) */}
      {/* ==================================================================== */}
      {activeTab === 'agent' && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          background: '#ffffff',
          border: '1.5px solid #e2e8f0',
          borderRadius: '20px',
          overflow: 'hidden',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
        }}>
          {/* Quick Prompts Bar (Gợi ý nhanh phía trên) */}
          <div style={{
            background: '#fafafa',
            borderBottom: '1px solid #f1f5f9',
            padding: '10px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            overflowX: 'auto',
            whiteSpace: 'nowrap'
          }}>
            <span style={{ fontSize: '12px', fontWeight: '800', color: '#991b1b', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Sparkles size={14} /> Gợi ý câu hỏi:
            </span>
            {quickPrompts.map((qp, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(qp.prompt)}
                disabled={isAgentReplying}
                style={{
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  color: '#334155',
                  padding: '5px 12px',
                  borderRadius: '9999px',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: isAgentReplying ? 'not-allowed' : 'pointer',
                  flexShrink: 0,
                  transition: 'all 0.15s'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#991b1b'; e.currentTarget.style.color = '#991b1b'; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e2e8f0'; e.currentTarget.style.color = '#334155'; }}
              >
                {qp.label}
              </button>
            ))}
          </div>

          {/* Vùng Tin nhắn Trò chuyện (Chat Stream) */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
            background: 'linear-gradient(180deg, #fafafa 0%, #ffffff 100%)'
          }}>
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  width: '100%'
                }}
              >
                {msg.role === 'agent' ? (
                  <div style={{ maxWidth: '85%', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <div style={{
                      background: 'linear-gradient(135deg, #991b1b, #7f1d1d)',
                      color: '#ffffff',
                      padding: '8px',
                      borderRadius: '12px',
                      marginTop: '2px',
                      flexShrink: 0
                    }}>
                      <Bot size={18} />
                    </div>
                    <div>
                      {/* Bong bóng tin nhắn AI */}
                      <div style={{
                        background: '#ffffff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '0 16px 16px 16px',
                        padding: '14px 18px',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.03)',
                        fontSize: '14.5px',
                        color: '#1e293b',
                        lineHeight: 1.6
                      }}>
                        {msg.text}
                      </div>

                      {/* Model badge */}
                      {msg.model && (
                        <div style={{ fontSize: '11px', color: '#94a3b8', margin: '4px 0 10px 4px', fontWeight: '600' }}>
                          ⚡ Trả lời bởi: {msg.model}
                        </div>
                      )}

                      {/* Các thẻ sách gợi ý đính kèm */}
                      {msg.books && msg.books.length > 0 && (
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))',
                          gap: '12px',
                          marginTop: '10px'
                        }}>
                          {msg.books.map((b, bIdx) => {
                            const floor = b.floor || 1;
                            const shelf = (b.shelf || 'A').toUpperCase();
                            const position = b.position || `${shelf}1-01`;
                            const available = b.available !== undefined ? b.available : 1;

                            return (
                              <div
                                key={bIdx}
                                style={{
                                  background: '#ffffff',
                                  border: '1.5px solid #fed7aa',
                                  borderRadius: '14px',
                                  padding: '12px 14px',
                                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  justifyContent: 'space-between',
                                  gap: '10px'
                                }}
                              >
                                <div>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
                                    <span style={{
                                      background: '#fff7ed',
                                      color: '#c2410c',
                                      fontSize: '11px',
                                      fontWeight: '800',
                                      padding: '2px 8px',
                                      borderRadius: '6px'
                                    }}>
                                      {b.category || 'Tài liệu'}
                                    </span>
                                    <span style={{ fontSize: '11px', color: available > 0 ? '#15803d' : '#b91c1c', fontWeight: '800' }}>
                                      {available > 0 ? `Sẵn có: ${available}` : 'Hết sách'}
                                    </span>
                                  </div>

                                  <h4 style={{
                                    fontSize: '13.5px',
                                    fontWeight: '800',
                                    color: '#0f172a',
                                    margin: '0 0 4px 0',
                                    lineHeight: 1.4
                                  }}>
                                    {b.title}
                                  </h4>
                                  <p style={{ fontSize: '12px', color: '#64748b', margin: '0 0 8px 0' }}>
                                    Tác giả: <strong>{b.author}</strong>
                                  </p>

                                  {/* Tọa độ kệ thực tế */}
                                  <div style={{
                                    background: '#f8fafc',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: '8px',
                                    padding: '6px 10px',
                                    fontSize: '11.5px',
                                    color: '#334155',
                                    fontWeight: '700',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px'
                                  }}>
                                    <MapPin size={13} color="#991b1b" />
                                    <span>Tầng {floor} • Kệ {shelf} • Vị trí {position}</span>
                                  </div>
                                </div>

                                <button
                                  onClick={() => setSelectedBookForMap(b)}
                                  style={{
                                    background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
                                    color: '#ffffff',
                                    border: 'none',
                                    borderRadius: '8px',
                                    padding: '8px 12px',
                                    fontSize: '12px',
                                    fontWeight: '800',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '6px',
                                    boxShadow: '0 2px 4px rgba(153, 27, 27, 0.2)'
                                  }}
                                >
                                  <Compass size={14} />
                                  <span>Chỉ đường đến kệ</span>
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  /* Bong bóng tin nhắn Sinh viên */
                  <div style={{
                    maxWidth: '75%',
                    background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
                    color: '#ffffff',
                    borderRadius: '16px 0 16px 16px',
                    padding: '12px 18px',
                    fontSize: '14.5px',
                    fontWeight: '600',
                    lineHeight: 1.5,
                    boxShadow: '0 2px 8px rgba(153, 27, 27, 0.25)'
                  }}>
                    {msg.text}
                  </div>
                )}
              </div>
            ))}

            {/* Hiệu ứng đang gõ phản hồi */}
            {isAgentReplying && (
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <div style={{
                  background: 'linear-gradient(135deg, #991b1b, #7f1d1d)',
                  color: '#ffffff',
                  padding: '8px',
                  borderRadius: '12px',
                  display: 'flex'
                }}>
                  <Bot size={18} />
                </div>
                <div style={{
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0 16px 16px 16px',
                  padding: '12px 16px',
                  fontSize: '13px',
                  color: '#64748b',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <RefreshCw size={14} className="animate-spin" color="#991b1b" />
                  <span>Thủ thư AI đang đọc câu hỏi và tra cứu kho 3.000 sách...</span>
                </div>
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Input Chat Box phía dưới */}
          <div style={{
            padding: '14px 20px',
            background: '#ffffff',
            borderTop: '1px solid #f1f5f9',
            display: 'flex',
            gap: '10px',
            alignItems: 'center'
          }}>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Nhập tâm sự, câu hỏi học tập hoặc nhu cầu của bạn... (VD: Em bị mất ngủ và stress vì thi lại...)"
              disabled={isAgentReplying}
              style={{
                flex: 1,
                padding: '14px 20px',
                borderRadius: '14px',
                border: '2px solid #e2e8f0',
                fontSize: '14.5px',
                fontWeight: '600',
                color: '#0f172a',
                outline: 'none',
                boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)'
              }}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || isAgentReplying}
              style={{
                background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
                color: '#ffffff',
                border: 'none',
                padding: '14px 24px',
                borderRadius: '14px',
                fontWeight: '800',
                fontSize: '14.5px',
                cursor: !inputMessage.trim() || isAgentReplying ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                opacity: !inputMessage.trim() || isAgentReplying ? 0.6 : 1,
                boxShadow: '0 4px 12px rgba(153, 27, 27, 0.3)',
                transition: 'all 0.2s'
              }}
            >
              <Send size={16} />
              <span>Gửi</span>
            </button>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: TRA CỨU NHANH TỪ KHÓA (FAST KEYWORD SEARCH MODE) */}
      {/* ==================================================================== */}
      {activeTab === 'search' && (
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflowY: 'auto' }}>
          {/* Ô nhập liệu tìm kiếm */}
          <div style={{
            background: '#ffffff',
            border: '1.5px solid #e2e8f0',
            borderRadius: '20px',
            padding: '18px 24px',
            marginBottom: '16px'
          }}>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <div style={{ flex: 1, position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Search size={22} style={{ position: 'absolute', left: '16px', color: '#94a3b8' }} />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleFastSearch()}
                  placeholder="Gõ từ khóa tên sách, tác giả, cốt truyện hoặc chủ đề..."
                  style={{
                    width: '100%',
                    padding: '14px 46px 14px 50px',
                    borderRadius: '14px',
                    border: '2px solid #e2e8f0',
                    fontSize: '15px',
                    fontWeight: '600',
                    color: '#0f172a',
                    outline: 'none'
                  }}
                />
                {query && (
                  <button
                    onClick={() => setQuery('')}
                    style={{ position: 'absolute', right: '14px', background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                  >
                    <X size={18} />
                  </button>
                )}
              </div>
              <button
                onClick={() => handleFastSearch()}
                disabled={isSearching}
                style={{
                  background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
                  color: '#ffffff',
                  border: 'none',
                  padding: '14px 26px',
                  borderRadius: '14px',
                  fontWeight: '800',
                  fontSize: '15px',
                  cursor: isSearching ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                {isSearching ? <RefreshCw size={18} className="animate-spin" /> : <Search size={18} />}
                <span>Tìm kiếm</span>
              </button>
            </div>
          </div>

          {/* Lưới kết quả */}
          {searchMeta && (
            <div style={{ fontSize: '13px', color: '#64748b', fontWeight: '600', marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
              <span>Tìm thấy <strong>{searchResults.length}</strong> kết quả</span>
              <span>Độ trễ: {searchMeta.latency_ms} ms • {searchMeta.method}</span>
            </div>
          )}

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
            gap: '16px'
          }}>
            {searchResults.map((book, idx) => {
              const floor = book.floor || 1;
              const shelf = (book.shelf || 'A').toUpperCase();
              const position = book.position || `${shelf}1-01`;
              const available = book.available !== undefined ? book.available : 1;
              const total = book.total !== undefined ? book.total : 1;

              return (
                <div
                  key={idx}
                  style={{
                    background: '#ffffff',
                    border: '1.5px solid #e2e8f0',
                    borderRadius: '18px',
                    padding: '18px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '12px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.03)'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{
                        background: '#fef2f2',
                        color: '#991b1b',
                        padding: '3px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '800'
                      }}>
                        {book.category}
                      </span>
                      <span style={{ fontSize: '12px', fontWeight: '800', color: available > 0 ? '#15803d' : '#b91c1c' }}>
                        {available > 0 ? `Còn ${available}/${total} cuốn` : 'Tạm hết'}
                      </span>
                    </div>

                    <h3 style={{ fontSize: '15px', fontWeight: '800', color: '#0f172a', margin: '0 0 4px 0', lineHeight: 1.4 }}>
                      {book.title}
                    </h3>
                    <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 10px 0' }}>
                      Tác giả: <strong>{book.author}</strong>
                    </p>
                    <p style={{
                      fontSize: '12.5px',
                      color: '#475569',
                      margin: '0 0 12px 0',
                      lineHeight: 1.5,
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden'
                    }}>
                      {book.description || 'Chưa có tóm tắt chi tiết.'}
                    </p>

                    <div style={{
                      background: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '10px',
                      padding: '8px 12px',
                      fontSize: '12.5px',
                      color: '#1e293b',
                      fontWeight: '700',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <MapPin size={15} color="#991b1b" />
                      <span>Tầng {floor} • Kệ {shelf} • Ô {position}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedBookForMap(book)}
                    style={{
                      background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '10px',
                      padding: '10px 16px',
                      fontSize: '13px',
                      fontWeight: '800',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px'
                    }}
                  >
                    <Compass size={16} />
                    <span>Chỉ đường đến kệ</span>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL CẤU HÌNH GOOGLE GEMINI API KEY */}
      {/* ==================================================================== */}
      {showKeyModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(15, 23, 42, 0.65)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 99999,
          padding: '20px'
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: '24px',
            padding: '28px',
            maxWidth: '520px',
            width: '100%',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Key size={20} color="#991b1b" />
                CẤU HÌNH GOOGLE GEMINI API
              </h3>
              <button onClick={() => setShowKeyModal(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <p style={{ fontSize: '13.5px', color: '#475569', lineHeight: 1.5, marginBottom: '16px' }}>
              Tích hợp <strong>Google Gemini 1.5 Flash</strong> giúp Thủ thư AI hiểu sâu sắc 100% ngữ cảnh tiếng Việt, cảm xúc và tâm lý sinh viên.
            </p>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '6px' }}>
                Gemini API Key:
              </label>
              <input
                type="password"
                value={tempKey}
                onChange={(e) => setTempKey(e.target.value)}
                placeholder="AIzaSy..."
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  border: '1.5px solid #cbd5e1',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              <span style={{ fontSize: '11.5px', color: '#64748b', marginTop: '6px', display: 'block' }}>
                💡 Nếu để trống, hệ thống sẽ tự động chuyển sang <strong>PTIT Local Semantic Reasoner</strong> (hoàn toàn miễn phí, không cần mạng).
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => setShowKeyModal(false)}
                style={{
                  background: '#f1f5f9',
                  border: '1px solid #cbd5e1',
                  color: '#475569',
                  padding: '10px 18px',
                  borderRadius: '10px',
                  fontWeight: '700',
                  fontSize: '13px',
                  cursor: 'pointer'
                }}
              >
                Hủy
              </button>
              <button
                onClick={handleSaveApiKey}
                style={{
                  background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
                  color: '#ffffff',
                  border: 'none',
                  padding: '10px 22px',
                  borderRadius: '10px',
                  fontWeight: '800',
                  fontSize: '13px',
                  cursor: 'pointer'
                }}
              >
                Lưu cấu hình
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sơ đồ Kệ Sách Thực Tế Modal (ShelfLocatorModal) */}
      {selectedBookForMap && (
        <ShelfLocatorModal
          book={selectedBookForMap}
          onClose={() => setSelectedBookForMap(null)}
        />
      )}
    </div>
  );
}
