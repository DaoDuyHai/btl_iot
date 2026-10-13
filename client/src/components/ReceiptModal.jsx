import React from 'react';
import { CheckCircle2, Mail, FileText, Calendar, User, ArrowRight, ShieldCheck } from 'lucide-react';

export default function ReceiptModal({ title, reader, items, actionType, onClose }) {
  if (!items) return null;

  const actionLabel = actionType === 'BORROW' ? 'Mượn tài liệu' : actionType === 'RETURN' ? 'Trả tài liệu' : 'Gia hạn';

  return (
    <div className="swipe-modal-backdrop">
      <div className="swipe-modal-box" style={{ maxWidth: '520px', padding: '34px 32px' }}>
        {/* Biểu tượng hoàn tất nổi bật */}
        <div style={{
          width: '68px',
          height: '68px',
          borderRadius: '22px',
          background: 'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)',
          color: '#15803d',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px auto',
          boxShadow: '0 8px 20px -4px rgba(22, 101, 52, 0.25)',
          border: '2px solid #ffffff'
        }}>
          <CheckCircle2 size={38} strokeWidth={2.5} />
        </div>

        <h2 style={{ fontSize: '24px', fontWeight: '900', color: '#0f172a', marginBottom: '6px' }}>
          {title || 'GIAO DỊCH THÀNH CÔNG'}
        </h2>
        
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          color: '#475569',
          fontSize: '13px',
          marginBottom: '20px',
          background: '#f8fafc',
          padding: '8px 16px',
          borderRadius: '9999px',
          border: '1px solid #e2e8f0'
        }}>
          <Mail size={15} color="#b91c1c" />
          <span>Biên lai đã gửi: <strong style={{ color: '#0f172a' }}>{reader?.email || 'sinhvien@ptit.edu.vn'}</strong></span>
        </div>

        {/* Khung biên lai điện tử E-Ticket PTIT Kiosk */}
        <div className="receipt-ticket">
          {/* Con dấu xác nhận thư viện PTIT */}
          <div className="receipt-stamp">
            PTIT VERIFIED
          </div>

          <div style={{ borderBottom: '1.5px dashed #cbd5e1', paddingBottom: '12px', marginBottom: '14px' }}>
            <div style={{ fontSize: '11px', fontWeight: '800', color: '#991b1b', letterSpacing: '0.5px' }}>
              THƯ VIỆN HỌC VIỆN CNBCVT • KIOSK TỰ PHỤC VỤ
            </div>
            <div style={{ fontSize: '15px', fontWeight: '800', color: '#0f172a', marginTop: '2px' }}>
              PHIẾU XÁC NHẬN {actionLabel.toUpperCase()}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', fontSize: '13px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748b' }}>
              <User size={14} color="#b91c1c" /> Bạn đọc: <strong style={{ color: '#0f172a' }}>{reader?.name || 'Bạn đọc'}</strong>
            </span>
            <span>MSSV: <strong style={{ color: '#b91c1c', fontFamily: 'monospace' }}>{reader?.studentId || 'N/A'}</strong></span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '13px' }}>
            <strong style={{ color: '#334155' }}>Danh mục tài liệu ({items.length}):</strong>
            <span style={{ fontSize: '11px', background: '#fee2e2', color: '#991b1b', padding: '3px 8px', borderRadius: '6px', fontWeight: '800' }}>
              {actionLabel}
            </span>
          </div>

          {/* Danh sách sách */}
          <div style={{ maxHeight: '140px', overflowY: 'auto', paddingRight: '4px', marginBottom: '14px' }}>
            {items.map((it, idx) => {
              const bookTitle = it.title || it.bookId?.title || it.book?.title;
              const hasFine = it.isOverdue || (it.fineAmount && it.fineAmount > 0);
              const fineText = hasFine ? ` (Phạt: ${it.fineAmount?.toLocaleString('vi-VN')} đ)` : '';

              return (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px dotted #e2e8f0', fontSize: '13px' }}>
                  <span style={{ maxWidth: '290px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: '600', color: '#1e293b' }}>
                    {idx + 1}. {bookTitle}
                  </span>
                  <span style={{ color: '#15803d', fontWeight: '800', fontSize: '12px', flexShrink: 0 }}>
                    ✓ Hợp lệ{fineText}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Barcode giả lập dưới đáy biên lai */}
          <div style={{ borderTop: '1.5px dashed #cbd5e1', paddingTop: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
            <div style={{
              height: '24px',
              width: '180px',
              background: 'repeating-linear-gradient(90deg, #0f172a, #0f172a 2px, transparent 2px, transparent 5px, #0f172a 5px, #0f172a 7px, transparent 7px, transparent 9px)',
              opacity: 0.75
            }}></div>
            <div style={{ fontSize: '10px', color: '#94a3b8', letterSpacing: '2px', fontFamily: 'monospace' }}>
              * {new Date().getTime().toString().slice(-8)} *
            </div>
          </div>

          <div style={{ marginTop: '10px', fontSize: '11px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Hệ thống quản trị thư viện Koha</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Calendar size={12} /> {new Date().toLocaleString('vi-VN')}
            </span>
          </div>
        </div>

        {/* Nút Hoàn tất */}
        <button
          className="btn-kiosk-finish"
          style={{ width: '100%', marginTop: '20px', padding: '15px' }}
          onClick={onClose}
        >
          <span>Hoàn tất & Quay về Trang chủ</span>
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}


