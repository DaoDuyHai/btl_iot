import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  Compass, 
  RefreshCw, 
  ArrowLeft,
  Bot, 
  Send, 
  Mic, 
  MicOff,
  MessageCircle
} from 'lucide-react';
import { apiService } from '../../api/apiService.js';
import ShelfLocatorModal from '../../components/ShelfLocatorModal.jsx';
import { playKioskBeep } from '../../utils/audio.js';

// Regex nhận diện từ khóa đánh thức "Hey Nova" (và mọi biến thể phát âm tiếng Việt kể cả trong môi trường ồn)
const WAKE_WORD_REGEX = /(?:(?:hey|he|hê|ê|hay|hây|chào|alo|a\s*lô|ơi)\s+)?(?:nova|nô\s*va|nôva|no\s*va|nô\s*ba|no\s*ba|lô\s*va|rô\s*va)(?:\s*ơi)?/i;

export default function AiSearchSection({ reader, onFinish }) {
  // State tin nhắn trò chuyện cùng AI Agent
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'welcome',
      role: 'agent',
      text: 'Xin chào! Mình là Trợ lý Thủ thư AI (Nova) của Học viện PTIT 🤖. Bạn có thể gọi "Nova" bất cứ lúc nào (hoặc bấm Micro) để mở đợt trò chuyện rảnh tay nhé!',
      books: [],
      model: 'Nova Semantic Reasoner V2 (Hybrid E5 + BM25Okapi)'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isAgentReplying, setIsAgentReplying] = useState(false);
  const chatBottomRef = useRef(null);

  // Chế độ: 'WAITING_FOR_WAKE_WORD' (đang chờ gọi "Hey Nova") hoặc 'LISTENING_FOR_QUERY' (đang lắng nghe câu hỏi)
  const [mode, setMode] = useState('WAITING_FOR_WAKE_WORD');
  const modeRef = useRef('WAITING_FOR_WAKE_WORD');
  modeRef.current = mode;

  // Trạng thái micro browser đang chạy
  const isRunningRef = useRef(false);
  const isSendingRef = useRef(false);
  const isTypingRef = useRef(false);   // Bạn đọc đang chủ động gõ phím
  const latestTranscriptRef = useRef('');
  const lastProcessedIndexRef = useRef(0); // Vị trí kết quả SpeechRecognition đã xử lý (tránh dính buffer continuous)
  const lastSubmittedQueryRef = useRef({ text: '', time: 0 }); // Bộ lọc chống gửi trùng lặp câu hỏi (Double-send Guard)

  // Timers
  const silenceTimerRef = useRef(null);
  const timeoutTimerRef = useRef(null);
  const restartTimerRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const maxSpeechTimerRef = useRef(null); // Giới hạn tối đa thời gian nói trong môi trường ồn
  const audioStreamRef = useRef(null);    // Stream giữ bộ lọc chống ồn phần cứng WebRTC

  const chatMessagesRef = useRef(chatMessages);
  chatMessagesRef.current = chatMessages;

  const isAgentReplyingRef = useRef(isAgentReplying);
  isAgentReplyingRef.current = isAgentReplying;

  const handleSendMessageRef = useRef(null);
  const recognitionRef = useRef(null);

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

  // Khởi động microphone an toàn
  function startMicSafe() {
    if (!recognitionRef.current || isAgentReplyingRef.current || isSendingRef.current) return;
    if (isRunningRef.current) return;
    try {
      recognitionRef.current.start();
    } catch (err) {
      if (err.name === 'InvalidStateError') {
        isRunningRef.current = true;
      }
    }
  }

  // Đánh thức Nova (Giống Hey Siri)
  function wakeNova(optionalQuery = '') {
    // 1. Âm thanh chuông đánh thức
    playKioskBeep('wake');

    // 2. Chuyển ngay chế độ sang lắng nghe câu hỏi
    modeRef.current = 'LISTENING_FOR_QUERY';
    setMode('LISTENING_FOR_QUERY');
    setInputMessage('');
    latestTranscriptRef.current = '';

    // 3. Nếu người dùng nói liền một hơi (ví dụ: "Hey Nova tìm giúp tôi sách C++")
    const cleanedQuery = (optionalQuery || '').replace(WAKE_WORD_REGEX, '').replace(/^[,:.\s]+/, '').trim();
    if (cleanedQuery.length >= 3) {
      setInputMessage(cleanedQuery);
      latestTranscriptRef.current = cleanedQuery;

      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (maxSpeechTimerRef.current) clearTimeout(maxSpeechTimerRef.current);
      silenceTimerRef.current = setTimeout(() => {
        submitQuery(latestTranscriptRef.current);
      }, 1000);
      return;
    }

    // 4. Người dùng chỉ mới gọi: "Hey Nova" -> Chào đón bạn đọc trong chat (Không phát loa)
    const greetingText = 'Xin chào bạn! Nova nghe đây ạ 🤖. Bạn cần tìm cuốn sách nào hay muốn thủ thư hỗ trợ gì cứ nói tự nhiên nhé!';
    setChatMessages(prev => [
      ...prev,
      {
        id: `greet_${Date.now()}`,
        role: 'agent',
        text: greetingText,
        books: [],
        model: 'Nova Wake Assistant'
      }
    ]);

    // Hẹn giờ 7 giây nếu không nói câu hỏi nào thì tự đóng lại chế độ chờ
    if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
    timeoutTimerRef.current = setTimeout(() => {
      if (modeRef.current === 'LISTENING_FOR_QUERY' && !latestTranscriptRef.current?.trim()) {
        modeRef.current = 'WAITING_FOR_WAKE_WORD';
        setMode('WAITING_FOR_WAKE_WORD');
        setInputMessage('');
        latestTranscriptRef.current = '';
      }
    }, 7000);

    // 5. Xả sạch buffer audio cũ để không bị dính từ "nova" vào input câu hỏi
    lastProcessedIndexRef.current = 999999;
    try {
      if (recognitionRef.current && isRunningRef.current) {
        recognitionRef.current.abort();
      }
    } catch (_e) {}
  }

  // Gửi câu hỏi và ĐÓNG NGAY phiên nói chuyện (đúng chuẩn Siri)
  function submitQuery(rawQuery) {
    const text = (rawQuery || latestTranscriptRef.current || inputMessage).trim();
    if (!text || isSendingRef.current || isAgentReplyingRef.current) return;

    // Lọc sạch wake word nếu còn sót ở đầu câu
    const cleanText = text.replace(WAKE_WORD_REGEX, '').replace(/^[,:.\s]+/, '').trim();
    if (!cleanText) {
      // Chuỗi chỉ chứa từ khóa đánh thức -> Không tìm sách và tuyệt đối KHÔNG gọi lại wakeNova
      setInputMessage('');
      latestTranscriptRef.current = '';
      return;
    }

    // Chống gửi trùng lặp câu hỏi (Double-send Guard trong 3s)
    const now = Date.now();
    if (cleanText.toLowerCase() === lastSubmittedQueryRef.current.text.toLowerCase() && (now - lastSubmittedQueryRef.current.time) < 3000) {
      setInputMessage('');
      latestTranscriptRef.current = '';
      return;
    }
    lastSubmittedQueryRef.current = { text: cleanText, time: now };

    isSendingRef.current = true;
    isAgentReplyingRef.current = true;

    // 1. Đóng ngay chế độ lắng nghe câu hỏi -> Trở về trạng thái chờ "Hey Nova" tiếp theo (chuẩn Siri)
    modeRef.current = 'WAITING_FOR_WAKE_WORD';
    setMode('WAITING_FOR_WAKE_WORD');
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
    if (maxSpeechTimerRef.current) clearTimeout(maxSpeechTimerRef.current);

    // Đánh dấu buffer cũ đã bị tiêu thụ hết (tránh onresult phát sinh khi abort đọc lại)
    lastProcessedIndexRef.current = 999999;

    // Tạm dừng micro trong lúc gửi tin nhắn và chờ AI trả lời để không nhận nhầm tạp âm
    try {
      if (recognitionRef.current && isRunningRef.current) {
        recognitionRef.current.abort();
      }
    } catch (_e) {}

    // 2. Gửi câu hỏi cho AI Agent
    handleSendMessageRef.current?.(cleanText, true);
  }

  // Khởi tạo Web Speech Recognition chạy ngầm liên tục
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Trình duyệt không hỗ trợ Web Speech API.');
      return;
    }

    let isUnmounted = false;
    let recognition = null;

    function initRecognition() {
      if (isUnmounted) return;
      try {
        if (recognition) {
          recognition.onstart = null;
          recognition.onresult = null;
          recognition.onerror = null;
          recognition.onend = null;
          try { recognition.abort(); } catch (_e) {}
        }
      } catch (_e) {}

      recognition = new SpeechRecognition();
      recognition.lang = 'vi-VN';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        isRunningRef.current = true;
        lastProcessedIndexRef.current = 0; // Reset an toàn khi phiên nhận diện mới bắt đầu
      };

      recognition.onresult = (event) => {
        // Nếu bạn đọc đang gõ phím hoặc AI đang bận trả lời / gửi -> Tuyệt đối không ghi đè và bỏ qua audio
        if (isTypingRef.current || isAgentReplyingRef.current || isSendingRef.current) {
          return;
        }

        // Lấy đoạn transcript từ index chưa xử lý (tránh dính buffer cũ của continuous = true)
        let currentSegment = '';
        const startIdx = Math.max(event.resultIndex, lastProcessedIndexRef.current);
        for (let i = startIdx; i < event.results.length; i++) {
          currentSegment += event.results[i][0].transcript;
        }
        const trimmed = currentSegment.trim();
        if (!trimmed) return;

        // TÌNH HUỐNG 1: Đang chờ gọi "Hey Nova" (Chế độ ngủ)
        if (modeRef.current === 'WAITING_FOR_WAKE_WORD') {
          const match = trimmed.match(WAKE_WORD_REGEX);
          if (match) {
            // Đánh dấu đã tiêu thụ hết kết quả hiện tại để không lặp lại
            lastProcessedIndexRef.current = event.results.length;
            // Lấy câu hỏi phía sau từ khóa (nếu có)
            const remaining = trimmed.substring(match.index + match[0].length).replace(/^[,:.\s]+/, '').trim();
            wakeNova(remaining);
          }
        } 
        // TÌNH HUỐNG 2: Đã thức dậy, đang lắng nghe câu hỏi của bạn đọc
        else if (modeRef.current === 'LISTENING_FOR_QUERY') {
          // Lọc sạch từ khóa Hey Nova
          const cleanText = trimmed.replace(WAKE_WORD_REGEX, '').replace(/^[,:.\s]+/, '').trim();

          // NẾU cleanText RỖNG (chỉ có từ khóa Hey Nova sót lại hoặc tiếng thở dài):
          // TUYỆT ĐỐI BỎ QUA! Không cập nhật inputMessage, không bật silence timer!
          if (!cleanText) {
            return;
          }

          if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);

          const isTextChanged = cleanText !== latestTranscriptRef.current;
          setInputMessage(cleanText);
          latestTranscriptRef.current = cleanText;

          // 1. Hard-cap Timer (2.5s): Chống kẹt mic trong môi trường ồn.
          // Khi đã nhận được câu hỏi hợp lệ (>= 4 ký tự), tối đa 2.5s sau sẽ tự động chốt gửi
          // để không bị tiếng ồn trong lớp liên tục cướp mic hoặc kéo dài vô tận!
          if (!maxSpeechTimerRef.current && cleanText.length >= 4) {
            maxSpeechTimerRef.current = setTimeout(() => {
              const currentText = latestTranscriptRef.current?.trim();
              if (currentText && currentText.length >= 2) {
                submitQuery(currentText);
              }
            }, 2500);
          }

          // 2. Silence Timer (1.0s): Tự động gửi khi dứt câu 1 giây.
          // Chỉ reset timer nếu nội dung có thêm từ mới (tránh tạp âm nền lặp lại liên tục trì hoãn việc gửi)
          if (isTextChanged || !silenceTimerRef.current) {
            if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = setTimeout(() => {
              const finalQuery = latestTranscriptRef.current?.trim();
              if (finalQuery && finalQuery.length >= 2) {
                submitQuery(finalQuery);
              }
            }, 1000);
          }
        }
      };

      recognition.onerror = (event) => {
        if (event.error === 'not-allowed') {
          console.warn('Microphone permission bị từ chối');
          return;
        }
        if (event.error !== 'no-speech') {
          console.warn('SpeechRecognition status:', event.error);
        }
      };

      recognition.onend = () => {
        isRunningRef.current = false;
        if (isUnmounted) return;

        // Tự động duy trì lắng nghe nếu AI không bận
        if (!isAgentReplyingRef.current && !isSendingRef.current) {
          if (restartTimerRef.current) clearTimeout(restartTimerRef.current);
          restartTimerRef.current = setTimeout(() => {
            if (!isUnmounted && !isAgentReplyingRef.current && !isSendingRef.current && !isRunningRef.current) {
              try {
                recognition.start();
              } catch (_e) {
                // Nếu start thất bại do lỗi state, tái khởi tạo mới
                initRecognition();
              }
            }
          }, 200);
        }
      };

      recognitionRef.current = recognition;

      try {
        recognition.start();
      } catch (_e) {}
    }

    // Kích hoạt bộ lọc chống ồn phần cứng WebRTC của trình duyệt cho Microphone
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      }).then(stream => {
        audioStreamRef.current = stream;
      }).catch(_e => {});
    }

    initRecognition();

    return () => {
      isUnmounted = true;
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
      if (restartTimerRef.current) clearTimeout(restartTimerRef.current);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      if (maxSpeechTimerRef.current) clearTimeout(maxSpeechTimerRef.current);
      if (audioStreamRef.current) {
        try {
          audioStreamRef.current.getTracks().forEach(track => track.stop());
        } catch (_e) {}
      }
      if (recognition) {
        // Hủy toàn bộ event listener để không bắn sự kiện ma sau khi unmount
        recognition.onstart = null;
        recognition.onresult = null;
        recognition.onerror = null;
        recognition.onend = null;
        try {
          recognition.abort();
        } catch (_e) {}
      }
    };
  }, []);

  // Đảm bảo micro luôn được kích hoạt khi người dùng tương tác với màn hình Kiosk
  useEffect(() => {
    function handleGlobalTouchOrClick() {
      if (!isRunningRef.current && !isAgentReplyingRef.current) {
        startMicSafe();
      }
    }
    window.addEventListener('click', handleGlobalTouchOrClick, { passive: true });
    window.addEventListener('touchstart', handleGlobalTouchOrClick, { passive: true });

    return () => {
      window.removeEventListener('click', handleGlobalTouchOrClick);
      window.removeEventListener('touchstart', handleGlobalTouchOrClick);
    };
  }, []);

  // Xử lý nút bấm Micro thủ công
  function handleToggleVoice() {
    if (isAgentReplying) return;

    if (modeRef.current === 'LISTENING_FOR_QUERY') {
      // Đang lắng nghe câu hỏi mà bấm Micro:
      const text = latestTranscriptRef.current?.trim() || inputMessage.trim();
      const clean = text.replace(WAKE_WORD_REGEX, '').replace(/^[,:.\s]+/, '').trim();
      if (clean) {
        // Nếu đã có câu hỏi -> Bấm Micro sẽ gửi ngay lập tức
        submitQuery(clean);
      } else {
        // Đóng lại nếu chưa nói gì
        modeRef.current = 'WAITING_FOR_WAKE_WORD';
        setMode('WAITING_FOR_WAKE_WORD');
        setInputMessage('');
        latestTranscriptRef.current = '';
        if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      }
    } else {
      // Bấm Micro khi đang chờ -> Tương đương gọi "Hey Nova" (Thức dậy và chào hỏi)
      wakeNova();
    }
  }

  // Cuộn xuống tin nhắn mới nhất
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isAgentReplying]);

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
            model: 'Nova Semantic Reasoner V2 (Hybrid E5 + BM25Okapi)'
          }
        ];
      });
    }
  }, [reader]);

  // Gửi tin nhắn trò chuyện tới AI Agent
  async function handleSendMessage(customText, isFromSubmit = false) {
    const textToSend = (customText !== undefined ? customText : (inputMessage || latestTranscriptRef.current)).trim();
    if (!textToSend || (isAgentReplyingRef.current && !isFromSubmit)) return;

    if (!isFromSubmit) {
      const now = Date.now();
      if (textToSend.toLowerCase() === lastSubmittedQueryRef.current.text.toLowerCase() && (now - lastSubmittedQueryRef.current.time) < 3000) {
        setInputMessage('');
        latestTranscriptRef.current = '';
        return;
      }
      lastSubmittedQueryRef.current = { text: textToSend, time: now };
    }

    // Đóng chế độ lắng nghe câu hỏi
    modeRef.current = 'WAITING_FOR_WAKE_WORD';
    setMode('WAITING_FOR_WAKE_WORD');
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
    if (maxSpeechTimerRef.current) clearTimeout(maxSpeechTimerRef.current);

    isSendingRef.current = true;
    isAgentReplyingRef.current = true;
    setIsAgentReplying(true);

    playKioskBeep('success');
    const userMsg = {
      id: `user_${Date.now()}`,
      role: 'user',
      text: textToSend
    };

    setChatMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    latestTranscriptRef.current = '';

    try {
      // Lọc bỏ lời chào để giữ lịch sử hội thoại thuần túy câu hỏi - câu trả lời
      const historyPayload = chatMessagesRef.current
        .filter(m => m.id !== 'welcome' && m.id !== 'reader_welcome' && !m.id?.startsWith('greet_'))
        .slice(-4)
        .map(m => ({
          role: m.role === 'user' ? 'user' : 'model',
          text: m.text
        }));

      const res = await apiService.chatWithAiLibrarian({
        message: textToSend,
        history: historyPayload,
        studentInfo: reader ? { name: reader.name, department: reader.department } : {}
      });

      if (res && res.success) {
        const replyText = res.reply || 'Dưới đây là một số tựa sách mình gợi ý cho bạn:';
        const agentMsg = {
          id: `agent_${Date.now()}`,
          role: 'agent',
          text: replyText,
          books: Array.isArray(res.books) ? res.books : [],
          model: 'Nova Semantic Reasoner V2 (Hybrid E5 + BM25Okapi)'
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
          text: 'Xin lỗi bạn, kết nối tới dịch vụ AI đang bị gián đoạn. Bạn hãy thử chọn lại câu hỏi mẫu hoặc thử lại sau giây lát nhé!',
          books: [],
          model: 'PTIT System Fallback'
        }
      ]);
    } finally {
      setIsAgentReplying(false);
      isAgentReplyingRef.current = false;
      isSendingRef.current = false;

      // Sau khi AI hoàn tất, micro nền sẵn sàng chờ "Hey Nova"
      setTimeout(() => {
        startMicSafe();
      }, 400);
    }
  }

  handleSendMessageRef.current = handleSendMessage;

  // Tách lời thoại chính và câu hỏi gợi ý mở
  function parseAgentReply(fullText) {
    if (!fullText) return { mainText: '', clarifyQuestion: '' };

    if (fullText.includes('💬')) {
      const idx = fullText.indexOf('💬');
      const mainText = fullText.substring(0, idx).trim();
      const clarifyQuestion = fullText.substring(idx + 1).replace(/^[\*\s]+|[\*\s]+$/g, '').trim();
      return { mainText, clarifyQuestion };
    }

    const parts = fullText.split(/\n\n(?=\*|🧭)/);
    if (parts.length > 1) {
      const mainText = parts[0].trim();
      const clarifyQuestion = parts.slice(1).join('\n\n').replace(/^[\*\s]+|[\*\s]+$/g, '').trim();
      return { mainText, clarifyQuestion };
    }

    return { mainText: fullText, clarifyQuestion: '' };
  }

  const isQueryMode = mode === 'LISTENING_FOR_QUERY';

  return (
    <div className="kiosk-workspace" style={{ maxWidth: '1280px', flexDirection: 'column', height: '100%', padding: '0 12px 16px' }}>
      <style>{`
        @keyframes micPulse {
          0% {
            box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7);
            transform: scale(1);
          }
          50% {
            box-shadow: 0 0 0 12px rgba(220, 38, 38, 0);
            transform: scale(1.06);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(220, 38, 38, 0);
            transform: scale(1);
          }
        }
        .mic-listening-btn {
          animation: micPulse 1.4s infinite !important;
        }
      `}</style>

      {/* 1. Header Chính */}
      <div style={{
        background: '#ffffff',
        border: '1.5px solid #e2e8f0',
        borderRadius: '20px',
        padding: '16px 24px',
        marginBottom: '14px',
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
            boxShadow: '0 4px 12px rgba(153, 27, 27, 0.25)'
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
              gap: '10px'
            }}>
              TRỢ LÝ THỦ THƯ AI (NOVA)
              <span style={{
                background: isQueryMode ? '#fee2e2' : '#dcfce7',
                color: isQueryMode ? '#b91c1c' : '#15803d',
                fontSize: '11px',
                padding: '3px 10px',
                borderRadius: '9999px',
                border: isQueryMode ? '1px solid #fecaca' : '1px solid #bbf7d0',
                fontWeight: '800',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}>
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: isQueryMode ? '#dc2626' : '#16a34a'
                }}></span>
                {isQueryMode ? 'NOVA ĐANG LẮNG NGHE' : 'SẴN SÀNG: "NOVA"'}
              </span>
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '3px 0 0' }}>
              Nói <strong>"Nova"</strong> để đánh thức • Tự động gửi câu hỏi sau 1.6s dứt lời • Tra cứu 3.000 đầu sách thực tế
            </p>
          </div>
        </div>

        {/* Nút thoát / hoàn tất */}
        {onFinish && (
          <button
            type="button"
            onClick={onFinish}
            style={{
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              color: '#475569',
              padding: '8px 18px',
              borderRadius: '9999px',
              fontSize: '13px',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s'
            }}
          >
            <ArrowLeft size={16} />
            <span>Quay lại Kiosk</span>
          </button>
        )}
      </div>

      {/* 2. Container Khung Chat Box */}
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
        {/* Quick Prompts Bar (Gợi ý câu hỏi nhanh) */}
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
          <span style={{ fontSize: '12px', fontWeight: '800', color: '#991b1b', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
            <Sparkles size={14} /> Gợi ý chủ đề:
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
                padding: '6px 14px',
                borderRadius: '9999px',
                fontSize: '12px',
                fontWeight: '700',
                cursor: isAgentReplying ? 'not-allowed' : 'pointer',
                flexShrink: 0,
                transition: 'all 0.15s',
                boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
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
          {chatMessages.map((msg) => {
            const { mainText, clarifyQuestion } = msg.role === 'agent' ? parseAgentReply(msg.text) : { mainText: msg.text, clarifyQuestion: '' };

            return (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  width: '100%'
                }}
              >
                {msg.role === 'agent' ? (
                  <div style={{ maxWidth: '88%', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <div style={{
                      background: 'linear-gradient(135deg, #991b1b, #7f1d1d)',
                      color: '#ffffff',
                      padding: '9px',
                      borderRadius: '12px',
                      marginTop: '2px',
                      flexShrink: 0,
                      boxShadow: '0 2px 6px rgba(153, 27, 27, 0.25)'
                    }}>
                      <Bot size={20} />
                    </div>
                    <div style={{ flex: 1 }}>
                      {/* Bong bóng tin nhắn AI */}
                      <div style={{
                        background: '#ffffff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '0 18px 18px 18px',
                        padding: '14px 18px',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.04)',
                        fontSize: '14.5px',
                        color: '#1e293b',
                        lineHeight: 1.6
                      }}>
                        <div>{mainText}</div>

                        {/* Câu hỏi gợi mở tương tác tiếp theo */}
                        {clarifyQuestion && (
                          <div style={{
                            marginTop: '12px',
                            background: '#eff6ff',
                            borderLeft: '4px solid #2563eb',
                            borderRadius: '0 8px 8px 0',
                            padding: '8px 12px',
                            fontSize: '13.5px',
                            color: '#1e40af',
                            fontWeight: '600',
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '8px'
                          }}>
                            <MessageCircle size={16} style={{ marginTop: '2px', flexShrink: 0 }} />
                            <span>{clarifyQuestion}</span>
                          </div>
                        )}
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
                          marginTop: '8px'
                        }}>
                          {msg.books.map((b, bIdx) => {
                            const floor = b.floor || 1;
                            const shelf = (b.shelf || 'A').toUpperCase();
                            const available = b.available !== undefined ? b.available : 1;

                            return (
                              <div
                                key={bIdx}
                                style={{
                                  background: '#ffffff',
                                  border: '1.5px solid #fed7aa',
                                  borderRadius: '14px',
                                  padding: '14px',
                                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  justifyContent: 'space-between',
                                  gap: '10px',
                                  transition: 'all 0.2s'
                                }}
                              >
                                <div>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
                                    <span style={{
                                      background: '#fff7ed',
                                      color: '#c2410c',
                                      fontSize: '11px',
                                      fontWeight: '800',
                                      padding: '3px 8px',
                                      borderRadius: '6px'
                                    }}>
                                      {b.category || 'Tài liệu'}
                                    </span>
                                    <span style={{
                                      fontSize: '11px',
                                      color: available > 0 ? '#15803d' : '#b91c1c',
                                      fontWeight: '800',
                                      background: available > 0 ? '#dcfce7' : '#fee2e2',
                                      padding: '2px 8px',
                                      borderRadius: '9999px'
                                    }}>
                                      {available > 0 ? `Sẵn có: ${available}` : 'Hết sách'}
                                    </span>
                                  </div>

                                  <h4 style={{
                                    fontSize: '14px',
                                    fontWeight: '800',
                                    color: '#0f172a',
                                    margin: '0 0 4px 0',
                                    lineHeight: '1.4',
                                    display: '-webkit-box',
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient: 'vertical',
                                    overflow: 'hidden'
                                  }}>
                                    {b.title}
                                  </h4>

                                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>
                                    Tác giả: <strong>{b.author || 'Không rõ tác giả'}</strong>
                                  </div>

                                  {/* Vị trí kệ tầng */}
                                  <div style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    background: '#f1f5f9',
                                    color: '#334155',
                                    fontSize: '12px',
                                    fontWeight: '700',
                                    padding: '4px 10px',
                                    borderRadius: '8px',
                                    width: '100%',
                                    boxSizing: 'border-box'
                                  }}>
                                    <Compass size={14} color="#991b1b" />
                                    <span>Khu vực Kệ {shelf} • Tầng {floor}</span>
                                  </div>
                                </div>

                                <button
                                  onClick={() => setSelectedBookForMap(b)}
                                  style={{
                                    background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
                                    color: '#ffffff',
                                    border: 'none',
                                    padding: '8px 12px',
                                    borderRadius: '8px',
                                    fontSize: '12.5px',
                                    fontWeight: '700',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '6px',
                                    width: '100%',
                                    boxShadow: '0 2px 4px rgba(153, 27, 27, 0.2)',
                                    transition: 'all 0.15s'
                                  }}
                                >
                                  <Compass size={14} />
                                  <span>Xem sơ đồ kệ {shelf}</span>
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  /* Tin nhắn của Bạn đọc (User Message) */
                  <div style={{
                    background: 'linear-gradient(135deg, #991b1b, #b91c1c)',
                    color: '#ffffff',
                    borderRadius: '18px 18px 4px 18px',
                    padding: '12px 20px',
                    maxWidth: '75%',
                    fontSize: '14.5px',
                    fontWeight: '600',
                    boxShadow: '0 4px 12px rgba(153, 27, 27, 0.25)',
                    lineHeight: 1.5
                  }}>
                    {msg.text}
                  </div>
                )}
              </div>
            );
          })}

          {/* Trạng thái AI đang suy nghĩ */}
          {isAgentReplying && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', maxWidth: '85%' }}>
              <div style={{
                background: '#991b1b',
                color: '#ffffff',
                padding: '9px',
                borderRadius: '12px',
                display: 'flex'
              }}>
                <Bot size={20} />
              </div>
              <div style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '0 16px 16px 16px',
                padding: '12px 18px',
                fontSize: '13.5px',
                color: '#64748b',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.03)'
              }}>
                <RefreshCw size={15} className="animate-spin" color="#991b1b" />
                <span>Thủ thư AI đang tra cứu kho 3.000 sách và phân tích vị trí kệ...</span>
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Thanh Nhập Liệu Tích hợp Giọng Nói & Text */}
        <div style={{
          background: '#ffffff',
          borderTop: '1px solid #e2e8f0',
          padding: '14px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          {/* Thông báo trạng thái: Đang mở đợt nói (Siri active) hoặc Đang chờ "Hey Nova" */}
          {isQueryMode ? (
            <div style={{
              background: '#fef2f2',
              color: '#991b1b',
              border: '1.5px solid #fecaca',
              padding: '8px 16px',
              borderRadius: '12px',
              fontSize: '13px',
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              boxShadow: '0 2px 8px rgba(220, 38, 38, 0.08)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                <span style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: '#dc2626',
                  display: 'inline-block',
                  flexShrink: 0,
                  boxShadow: '0 0 10px #dc2626'
                }}></span>
                <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {inputMessage
                    ? `🎙️ Đang nghe: "${inputMessage}" (Dứt câu 1.8s sẽ tự gửi & tắt mic)`
                    : '⚡ Nova đã thức dậy và đang lắng nghe... Hãy nói câu hỏi hoặc tựa sách cần tìm!'}
                </span>
              </div>
              <span style={{ fontSize: '12px', color: '#b91c1c', fontWeight: '600', flexShrink: 0 }}>
                [Bấm Micro hoặc Enter để gửi ngay]
              </span>
            </div>
          ) : (
            <div style={{
              background: '#f8fafc',
              color: '#475569',
              border: '1px solid #e2e8f0',
              padding: '7px 16px',
              borderRadius: '10px',
              fontSize: '12.5px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '10px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#16a34a', display: 'inline-block', boxShadow: '0 0 6px #16a34a' }}></span>
                <span>🎙️ Bạn có thể gọi <strong>"Nova"</strong> để mở đợt trò chuyện rảnh tay (không cần chạm tay).</span>
              </div>
              <span style={{ fontSize: '11.5px', color: '#94a3b8' }}>[Rảnh tay thông minh]</span>
            </div>
          )}

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => {
                setInputMessage(e.target.value);
                // Khi người dùng chủ động gõ phím: Hủy ngay các bộ đếm tự động gửi để không bị cướp quyền
                if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
                if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
                if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
                isTypingRef.current = true;
                typingTimeoutRef.current = setTimeout(() => {
                  isTypingRef.current = false;
                }, 3000);
              }}
              onFocus={() => {
                if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
                if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
                isTypingRef.current = true;
              }}
              onBlur={() => {
                typingTimeoutRef.current = setTimeout(() => {
                  isTypingRef.current = false;
                }, 1000);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  isTypingRef.current = false;
                  submitQuery(inputMessage);
                }
              }}
              placeholder='Nói "Nova" để mở đợt trò chuyện hoặc gõ câu hỏi, tâm sự...'
              disabled={isAgentReplying}
              style={{
                flex: 1,
                padding: '14px 20px',
                borderRadius: '14px',
                border: isQueryMode ? '2px solid #ef4444' : '2px solid #e2e8f0',
                boxShadow: isQueryMode ? '0 0 0 3px rgba(239, 68, 68, 0.15)' : 'none',
                fontSize: '14.5px',
                fontWeight: '600',
                color: '#0f172a',
                outline: 'none',
                background: '#ffffff',
                transition: 'all 0.2s'
              }}
            />

            {/* Nút Nhận diện giọng nói (Voice-to-Text) */}
            <button
              type="button"
              onClick={handleToggleVoice}
              disabled={isAgentReplying}
              className={isQueryMode ? 'mic-listening-btn' : ''}
              style={{
                background: isQueryMode ? '#dc2626' : '#f8fafc',
                color: isQueryMode ? '#ffffff' : '#64748b',
                border: isQueryMode ? '2px solid #ef4444' : '1.5px solid #cbd5e1',
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                cursor: isAgentReplying ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'all 0.2s',
                boxShadow: isQueryMode ? '0 0 15px rgba(220, 38, 38, 0.5)' : 'none'
              }}
              title={isQueryMode ? 'Đang lắng nghe... Bấm để gửi ngay' : 'Bấm để mở đợt nói (hoặc nói "Nova")'}
            >
              {isQueryMode ? <MicOff size={22} /> : <Mic size={22} />}
            </button>

            {/* Nút Gửi */}
            <button
              onClick={() => submitQuery(inputMessage)}
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
                transition: 'all 0.2s',
                flexShrink: 0
              }}
            >
              <Send size={16} />
              <span>Gửi</span>
            </button>
          </div>
        </div>
      </div>

      {/* Sơ đồ chỉ đường đến kệ */}
      {selectedBookForMap && (
        <ShelfLocatorModal
          book={selectedBookForMap}
          onClose={() => setSelectedBookForMap(null)}
        />
      )}
    </div>
  );
}
