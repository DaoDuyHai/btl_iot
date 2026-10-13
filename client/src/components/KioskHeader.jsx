import React from 'react';
import { Link } from 'react-router-dom';
import { Home, Settings, Radio, BookOpen } from 'lucide-react';

export default function KioskHeader({ title, icon, onBackHome, deviceStatus }) {
  const isOnline = deviceStatus?.status === 'online';

  return (
    <header className="kiosk-header">
      {/* Góc trái: Logo PTIT & Tên trung tâm */}
      <div className="kiosk-header-left">
        <div className="ptit-logo-container">
          <img src="/PTIT.png" alt="PTIT Logo" className="ptit-logo-img" />
        </div>
        <div>
          <div className="kiosk-header-title">
            HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG
          </div>
          <div style={{ fontSize: '11px', color: '#fef08a', fontWeight: '700', letterSpacing: '0.4px', textTransform: 'uppercase' }}>
            LIBRARY & INFORMATION CENTER • TRẠM KIOSK TỰ PHỤC VỤ
          </div>
        </div>
      </div>

      {/* Ở giữa: Tiêu đề màn hình con (nếu đang ở màn hình con) */}
      {title && (
        <div className="kiosk-header-center">
          {icon && <span>{icon}</span>}
          <span>{title}</span>
        </div>
      )}

      {/* Góc phải: Nút điều hướng, Icon sách mở và Trạng thái ESP32 */}
      <div className="kiosk-header-right">
        {onBackHome ? (
          <button
            onClick={onBackHome}
            style={{
              background: 'rgba(255, 255, 255, 0.2)',
              border: '1px solid rgba(255, 255, 255, 0.35)',
              color: '#ffffff',
              padding: '7px 16px',
              borderRadius: '9999px',
              cursor: 'pointer',
              fontWeight: '700',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s'
            }}
          >
            <Home size={16} />
            <span>Trang Chủ</span>
          </button>
        ) : (
          <Link
            to="/admin"
            style={{
              textDecoration: 'none',
              background: 'rgba(255, 255, 255, 0.18)',
              color: '#ffffff',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: '700',
              border: '1px solid rgba(255, 255, 255, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: '5px'
            }}
          >
            <Settings size={14} />
            <span>Thủ thư</span>
          </Link>
        )}

        {/* Trạng thái Kiosk */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '7px',
          fontSize: '12px',
          fontWeight: '700',
          background: 'rgba(0, 0, 0, 0.3)',
          padding: '5px 12px',
          borderRadius: '9999px',
          border: '1px solid rgba(255, 255, 255, 0.15)'
        }}>
          <Radio size={14} color={isOnline ? '#4ade80' : '#f87171'} />
          <span style={{ color: isOnline ? '#4ade80' : '#f87171' }}>
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* Biểu tượng Sách Mở lớn đặc trưng thư viện */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ffffff',
          marginLeft: '4px'
        }}>
          <BookOpen size={30} strokeWidth={2} />
        </div>
      </div>
    </header>
  );
}
