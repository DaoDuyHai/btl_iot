import React from 'react';
import ReaderInfoSidebar from '../../components/ReaderInfoSidebar.jsx';
import { BookOpen, Trash2, CheckCircle2, Clock } from 'lucide-react';

export default function BorrowSection({ 
  reader, 
  borrowCart, 
  onRemoveBook, 
  onConfirmBorrow 
}) {
  return (
    <div className="kiosk-workspace">
      {/* 1/4 Cột Trái: Thông tin độc giả & Đồ họa đầu đọc RFID */}
      <ReaderInfoSidebar 
        reader={reader} 
        isReadingActive={true} 
      />

      {/* 3/4 Cột Phải: Danh sách tài liệu mượn */}
      <main className="kiosk-content-right">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#991b1b', margin: 0 }}>
              DANH SÁCH TÀI LIỆU MƯỢN ({borrowCart.length})
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
              Đặt tài liệu lên bàn đọc RFID để hệ thống tự động ghi nhận vào giỏ mượn
            </p>
          </div>
          <span style={{ 
            fontSize: '12px', 
            background: '#fee2e2', 
            color: '#991b1b', 
            padding: '5px 14px', 
            borderRadius: '9999px', 
            fontWeight: '700',
            border: '1px solid #fecaca' 
          }}>
            Hạn mượn chuẩn: 14 ngày
          </span>
        </div>

        {/* Bảng sách phong cách Shadcn/UI */}
        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '14px', background: '#ffffff' }}>
          <div className="kiosk-table-header">
            <div>Số lượng</div>
            <div>Tiêu đề & Tác giả</div>
            <div style={{ textAlign: 'right' }}>Hạn trả</div>
          </div>

          {borrowCart.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '16px',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px',
                color: '#94a3b8'
              }}>
                <BookOpen size={32} />
              </div>
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#334155' }}>
                Chưa có tài liệu nào trong khu vực đầu đọc
              </div>
              <p style={{ fontSize: '13px', marginTop: '6px', color: '#64748b' }}>
                Vui lòng đặt tài liệu lên bàn đọc RFID để cảm biến tự động ghi nhận
              </p>
            </div>
          ) : (
            borrowCart.map((book, idx) => {
              const dueDate = new Date();
              dueDate.setDate(dueDate.getDate() + 14);
              const dueDateStr = `${dueDate.toLocaleDateString('vi-VN')} 23:59`;

              return (
                <div key={book._id || idx} className="kiosk-table-row">
                  <div style={{ fontWeight: '800', color: '#b91c1c' }}>#{idx + 1}</div>
                  <div>
                    <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '15px' }}>
                      {book.title}
                    </div>
                    <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                      Tác giả: <strong>{book.author}</strong> | Thể loại: {book.category || 'Chung'} | RFID: <code>{book.rfidTag}</code>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '16px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontWeight: '700', color: '#0f172a', fontSize: '14px' }}>
                        {dueDateStr}
                      </span>
                      <div style={{ fontSize: '11px', color: '#16a34a', fontWeight: '600' }}>
                        (Thời hạn 14 ngày)
                      </div>
                    </div>
                    <button
                      onClick={() => onRemoveBook(idx)}
                      style={{
                        background: '#fee2e2',
                        border: 'none',
                        color: '#dc2626',
                        cursor: 'pointer',
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all 0.15s'
                      }}
                      title="Bỏ cuốn sách này"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Nút Hoàn thành ở góc dưới bên phải */}
        <div className="kiosk-bottom-bar">
          <button
            className="btn-kiosk-finish"
            disabled={borrowCart.length === 0}
            style={{
              opacity: borrowCart.length === 0 ? 0.5 : 1,
              cursor: borrowCart.length === 0 ? 'not-allowed' : 'pointer'
            }}
            onClick={onConfirmBorrow}
          >
            <CheckCircle2 size={20} strokeWidth={2.5} />
            <span>Xác nhận mượn ({borrowCart.length} cuốn)</span>
          </button>
        </div>
      </main>
    </div>
  );
}
