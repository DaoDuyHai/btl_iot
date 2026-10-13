import React from 'react';
import { BookDown, BookUp, UserCheck, RefreshCw } from 'lucide-react';

export default function KioskHome({ onSelectFeature, reader, onLogout }) {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', marginBottom: '28px' }}>
        <h2 style={{ fontSize: '26px', fontWeight: '900', color: '#991b1b', marginBottom: '8px', letterSpacing: '0.3px' }}>
          CHÀO MỪNG BẠN ĐỌC ĐẾN VỚI KIOSK TỰ PHỤC VỤ PTIT
        </h2>
        {reader ? (
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '12px',
            background: '#fee2e2',
            border: '1px solid #fecaca',
            borderRadius: '9999px',
            padding: '6px 18px',
            marginTop: '4px'
          }}>
            <span style={{ fontSize: '14px', color: '#991b1b', fontWeight: '700' }}>
              👤 Đang đăng nhập: {reader.name} ({reader.studentId})
            </span>
            <button
              onClick={onLogout}
              style={{
                background: '#ffffff',
                border: '1px solid #fca5a5',
                color: '#b91c1c',
                borderRadius: '9999px',
                padding: '3px 12px',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer'
              }}
            >
              Đăng xuất / Kết thúc
            </button>
          </div>
        ) : (
          <p style={{ color: '#64748b', fontSize: '15px' }}>
            Vui lòng chọn một trong các thao tác bên dưới hoặc quẹt thẻ bạn đọc để bắt đầu phiên giao dịch
          </p>
        )}
      </div>

      {/* 4 Nút chức năng lớn đúng kích thước chuẩn phong cách thẻ Shadcn/UI Luxury */}
      <div className="home-buttons-grid">
        {/* 1. Mượn tài liệu */}
        <button
          className="kiosk-big-btn btn-borrow"
          onClick={() => onSelectFeature('BORROW')}
        >
          <div className="kiosk-big-btn-icon">
            <BookDown size={54} strokeWidth={2.2} />
          </div>
          <div className="kiosk-big-btn-label">Mượn tài liệu</div>
        </button>

        {/* 2. Trả tài liệu */}
        <button
          className="kiosk-big-btn btn-return"
          onClick={() => onSelectFeature('RETURN')}
        >
          <div className="kiosk-big-btn-icon">
            <BookUp size={54} strokeWidth={2.2} />
          </div>
          <div className="kiosk-big-btn-label">Trả tài liệu</div>
        </button>

        {/* 3. Thông tin bạn đọc */}
        <button
          className="kiosk-big-btn btn-reader"
          onClick={() => onSelectFeature('ACCOUNT')}
        >
          <div className="kiosk-big-btn-icon">
            <UserCheck size={54} strokeWidth={2.2} />
          </div>
          <div className="kiosk-big-btn-label">Thông tin bạn đọc</div>
        </button>

        {/* 4. Gia hạn */}
        <button
          className="kiosk-big-btn btn-renew"
          onClick={() => onSelectFeature('RENEW')}
        >
          <div className="kiosk-big-btn-icon">
            <RefreshCw size={54} strokeWidth={2.2} />
          </div>
          <div className="kiosk-big-btn-label">Gia hạn</div>
        </button>
      </div>

      <div style={{ marginTop: '24px', fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>
        Học Viện Công Nghệ Bưu Chính Viễn Thông - Trung Tâm Thông Tin Thư Viện
      </div>
    </div>
  );
}
