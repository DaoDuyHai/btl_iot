import React from 'react';
import { BookMarked, User } from 'lucide-react';

export default function ReaderInfoSidebar({ reader, isReadingActive = true }) {
  if (!reader) return null;

  return (
    <aside className="kiosk-sidebar-left">
      {/* Thông tin độc giả góc trái */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '14px',
            background: '#fee2e2',
            color: '#b91c1c',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '18px',
            fontWeight: '800',
            border: '1px solid #fecaca'
          }}>
            {reader.name?.charAt(0) || 'U'}
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a' }}>
              {reader.name}
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b' }}>
              MSSV: <strong style={{ color: '#b91c1c' }}>{reader.studentId}</strong>
            </p>
          </div>
        </div>

        <div style={{ fontSize: '12px', color: '#64748b', borderTop: '1px solid #f1f5f9', paddingTop: '8px', lineHeight: 1.4 }}>
          {reader.department || 'Khoa Công Nghệ Thông Tin 1 - PTIT'}
        </div>
      </div>

      {/* Khung hướng dẫn Đặt tài liệu vào khu vực đầu đọc */}
      <div className={`reader-graphic-box ${isReadingActive ? 'active' : ''}`}>
        <div className="reader-pulse-circle"></div>
        <div className="reader-book-icon-anim">
          <BookMarked size={34} color="#b91c1c" />
        </div>
        <div style={{
          fontSize: '14px',
          fontWeight: '800',
          color: isReadingActive ? '#b91c1c' : '#475569',
          marginTop: '6px'
        }}>
          Đặt tài liệu vào khu vực đầu đọc
        </div>
        <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '600' }}>
          (RFID Sensor Active • 13.56 MHz)
        </span>
      </div>
    </aside>
  );
}
