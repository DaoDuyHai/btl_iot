// Singleton AudioContext dùng chung cho toàn bộ vòng đời ứng dụng (Tránh chạm trần 6 AudioContext trên Chrome)
let sharedAudioCtx = null;

function getSharedAudioCtx() {
  if (typeof window === 'undefined') return null;
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return null;
  if (!sharedAudioCtx || sharedAudioCtx.state === 'closed') {
    sharedAudioCtx = new AudioCtx();
  }
  if (sharedAudioCtx.state === 'suspended') {
    sharedAudioCtx.resume().catch(() => {});
  }
  return sharedAudioCtx;
}

// Tiện ích âm thanh phản hồi Kiosk (Web Audio API)
export function playKioskBeep(type = 'success') {
  try {
    const ctx = getSharedAudioCtx();
    if (!ctx) return;
    
    if (type === 'wake') {
      // Âm thanh đánh thức Wake Word 2 nốt "Bính Boong!" vui tai
      [
        { freq: 880, time: 0, dur: 0.12 },
        { freq: 1320, time: 0.12, dur: 0.25 }
      ].forEach(note => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(note.freq, ctx.currentTime + note.time);
        gain.gain.setValueAtTime(0.2, ctx.currentTime + note.time);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + note.time + note.dur);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + note.time);
        osc.stop(ctx.currentTime + note.time + note.dur);
      });
    } else if (type === 'success') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1760, ctx.currentTime); // 1760Hz (A6)
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    } else {
      // Error: 2 bíp trầm
      [0, 0.15].forEach(timeOffset => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(440, ctx.currentTime + timeOffset);
        gain.gain.setValueAtTime(0.15, ctx.currentTime + timeOffset);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + timeOffset + 0.1);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + timeOffset);
        osc.stop(ctx.currentTime + timeOffset + 0.1);
      });
    }
  } catch (_e) {
    // Không chặn nếu trình duyệt chưa cấp quyền audio
  }
}

// Tiện ích giọng đọc phản hồi Tiếng Việt (Web Speech Synthesis)
export function speakText(text, onEndCallback) {
  if (typeof window === 'undefined' || !window.speechSynthesis) {
    if (onEndCallback) onEndCallback();
    return;
  }
  try {
    window.speechSynthesis.cancel();
    if (!text) {
      if (onEndCallback) onEndCallback();
      return;
    }

    // Lọc bỏ markdown, emoji, icon để đọc tự nhiên
    const clean = text
      .replace(/[*#_~`>]/g, '')
      .replace(/[🤖⚡💡📚🧭💬📌❤️✨🚀]/gu, '')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    // Chỉ đọc 2 câu đầu (khoảng 160 ký tự) để giọng đọc súc tích, nhanh gọn
    const sentences = clean.split(/(?<=[.?!])\s+/);
    const textToSpeak = sentences.slice(0, 2).join(' ').slice(0, 180);

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = 'vi-VN';
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const viVoice = voices.find(v => v.lang.includes('vi') || v.lang.includes('VI'));
    if (viVoice) {
      utterance.voice = viVoice;
    }

    utterance.onend = () => {
      if (onEndCallback) onEndCallback();
    };
    utterance.onerror = () => {
      if (onEndCallback) onEndCallback();
    };

    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.warn('SpeechSynthesis error:', err);
    if (onEndCallback) onEndCallback();
  }
}

export function stopSpeaking() {
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch (_e) {}
  }
}

