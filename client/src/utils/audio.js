// Tiện ích âm thanh phản hồi Kiosk (Web Audio API)
export function playKioskBeep(type = 'success') {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    
    if (type === 'success') {
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
  } catch (e) {
    // Không chặn nếu trình duyệt chưa cấp quyền audio
  }
}

