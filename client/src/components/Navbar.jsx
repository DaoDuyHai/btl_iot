import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar({ deviceStatus }) {
  const location = useLocation();
  const isOnline = deviceStatus?.status === 'online';

  return (
    <header style={{
      background: '#ffffff',
      borderBottom: '1px solid #e2e8f0',
      padding: '16px 32px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '28px' }}>📚</span>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.5px' }}>
            SMART LIBRARY KIOSK
          </h1>
          <p style={{ fontSize: '12px', color: '#64748b' }}>Hệ Thống Mượn/Trả Sách Tự Phục Vụ</p>
        </div>
      </div>

      <nav style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <Link
          to="/kiosk"
          style={{
            textDecoration: 'none',
            padding: '8px 18px',
            borderRadius: '10px',
            fontWeight: '600',
            fontSize: '14px',
            transition: 'all 0.2s',
            background: location.pathname === '/kiosk' ? '#2563eb' : '#f1f5f9',
            color: location.pathname === '/kiosk' ? '#ffffff' : '#475569'
          }}
        >
          🖥️ Màn Hình Kiosk
        </Link>
        <Link
          to="/admin"
          style={{
            textDecoration: 'none',
            padding: '8px 18px',
            borderRadius: '10px',
            fontWeight: '600',
            fontSize: '14px',
            transition: 'all 0.2s',
            background: location.pathname === '/admin' ? '#2563eb' : '#f1f5f9',
            color: location.pathname === '/admin' ? '#ffffff' : '#475569'
          }}
        >
          ⚙️ Quản Trị Thủ Thư
        </Link>
      </nav>

      {/* Trạng thái Kiosk IoT */}
      <div className={`kiosk-badge ${isOnline ? 'badge-online' : 'badge-offline'}`}>
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: isOnline ? '#16a34a' : '#dc2626',
          display: 'inline-block'
        }}></span>
        <span>{isOnline ? 'ESP32 ONLINE' : 'ESP32 OFFLINE'}</span>
        {isOnline && deviceStatus.rssi && (
          <span style={{ fontSize: '11px', opacity: 0.8 }}>({deviceStatus.rssi} dBm)</span>
        )}
      </div>
    </header>
  );
}

