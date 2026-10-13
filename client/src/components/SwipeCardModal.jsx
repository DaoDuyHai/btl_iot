import React from 'react';
import { CreditCard, Radio, ArrowLeft, Wifi, Sparkles, X } from 'lucide-react';

export default function SwipeCardModal({ targetFunction, onClose }) {
  return (
    <div className="swipe-modal-backdrop">
      <div className="swipe-modal-box" style={{ maxWidth: '520px', padding: '38px 32px' }}>
        {/* Nút X đóng góc trên */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: '#f1f5f9',
            border: 'none',
            borderRadius: '50%',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: '#64748b'
          }}
        >
          <X size={18} />
        </button>

        {/* Tiêu đề chức năng đang chờ */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          background: '#fee2e2',
          color: '#991b1b',
          padding: '6px 18px',
          borderRadius: '9999px',
          fontSize: '12px',
          fontWeight: '800',
          marginBottom: '16px',
          border: '1px solid #fecaca'
        }}>
          <Radio size={14} className="animate-pulse" />
          <span>{targetFunction || 'XÁC THỰC DANH TÍNH BẠN ĐỌC'}</span>
        </div>

        <h2 style={{ fontSize: '24px', fontWeight: '900', color: '#0f172a', marginBottom: '8px' }}>
          Vui Lòng Đặt Thẻ Lên Đầu Đọc
        </h2>
        <p style={{ color: '#64748b', fontSize: '14px', lineHeight: 1.5 }}>
          Chạm thẻ sinh viên PTIT hoặc thẻ bạn đọc vào khu vực cảm biến <strong>RFID (RC522)</strong> để Kiosk tự động nhận diện.
        </p>

        {/* Animation minh họa quẹt thẻ kèm sóng radar contactless */}
        <div className="swipe-card-anim-container">
          <div className="rfid-radar-wave"></div>
          <div className="rfid-radar-wave"></div>
          <div className="rfid-radar-wave"></div>
          
          <div className="reader-slot"></div>
          
          <div className="rfid-card-visual">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '11px', fontWeight: '900', letterSpacing: '0.5px' }}>PTIT SMARTCARD</span>
              <Wifi size={14} />
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '28px',
                height: '20px',
                borderRadius: '4px',
                background: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
                border: '1px solid #d97706'
              }}></div>
              <div style={{ fontSize: '10px', fontWeight: '800', opacity: 0.85, fontFamily: 'monospace' }}>
                RFID NFC
              </div>
            </div>

            <div style={{ fontSize: '11px', fontWeight: '700', letterSpacing: '1px' }}>STUDENT ID CARD</div>
          </div>
        </div>

        {/* Trạng thái chờ tín hiệu */}
        <div style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '14px',
          padding: '12px 18px',
          marginBottom: '24px',
          fontSize: '13px',
          color: '#475569',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px'
        }}>
          <span className="rfid-pulse-dot" style={{ width: '10px', height: '10px', background: '#22c55e', borderRadius: '50%', display: 'inline-block', boxShadow: '0 0 8px #22c55e' }}></span>
          <span>Đang lắng nghe tín hiệu từ cảm biến thiết bị Kiosk...</span>
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button
            className="btn-kiosk-secondary"
            style={{ width: '100%', padding: '13px 24px', fontSize: '15px' }}
            onClick={onClose}
          >
            <ArrowLeft size={16} /> Quay lại trang chủ
          </button>
        </div>
      </div>
    </div>
  );
}


