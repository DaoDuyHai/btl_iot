import React from 'react';
import ReaderInfoSidebar from '../../components/ReaderInfoSidebar.jsx';
import { BookUp, QrCode, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function ReturnSection({ 
  reader, 
  returnedBooks, 
  onConfirmFinish, 
  onOpenVietQrModal
}) {
  return (
    <div className="kiosk-workspace">
      {/* 1/4 Cột Trái */}
      <ReaderInfoSidebar 
        reader={reader} 
        isReadingActive={true} 
      />

      {/* 3/4 Cột Phải */}
      <main className="kiosk-content-right">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#991b1b', margin: 0 }}>
              DANH SÁCH TÀI LIỆU TRẢ ({returnedBooks.length})
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
              Đặt sách vào khu vực đầu đọc RFID để hệ thống tự động ghi nhận hoàn trả
            </p>
          </div>
          <span style={{ fontSize: '12px', background: '#f8fafc', color: '#475569', padding: '5px 14px', borderRadius: '9999px', fontWeight: '700', border: '1px solid #e2e8f0' }}>
            Tự động đối soát CSDL
          </span>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '14px', background: '#ffffff' }}>
          <div className="kiosk-table-header">
            <div>Số lượng</div>
            <div>Tiêu đề & Tác giả</div>
            <div style={{ textAlign: 'right' }}>Trạng thái hoàn trả</div>
          </div>

          {returnedBooks.length === 0 ? (
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
                <BookUp size={32} />
              </div>
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#334155' }}>
                Vui lòng đặt tài liệu cần trả lên đầu đọc RFID
              </div>
              <p style={{ fontSize: '13px', marginTop: '6px', color: '#64748b' }}>
                Hệ thống sẽ tự động cập nhật kho sách và tính toán tiền phạt nếu có trễ hạn
              </p>
            </div>
          ) : (
            returnedBooks.map((res, idx) => (
              <div key={res.loan?._id || idx} className="kiosk-table-row">
                <div style={{ fontWeight: '800', color: '#b91c1c' }}>#{idx + 1}</div>
                <div>
                  <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '15px' }}>
                    {res.book?.title}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                    Tác giả: <strong>{res.book?.author}</strong> | RFID: <code>{res.book?.rfidTag}</code>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                  {res.isOverdue ? (
                    res.isPaid ? (
                      <span style={{
                        padding: '5px 12px',
                        borderRadius: '9999px',
                        fontSize: '12px',
                        fontWeight: '700',
                        background: '#dcfce7',
                        color: '#15803d',
                        border: '1px solid #bbf7d0',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}>
                        <CheckCircle2 size={14} />
                        Đã nộp phạt VietQR (+{res.fineAmount?.toLocaleString('vi-VN')} đ)
                      </span>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          padding: '5px 10px',
                          borderRadius: '9999px',
                          fontSize: '12px',
                          fontWeight: '700',
                          background: '#fee2e2',
                          color: '#b91c1c',
                          border: '1px solid #fecaca',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          <AlertTriangle size={13} />
                          Chưa nộp phạt (+{res.fineAmount?.toLocaleString('vi-VN')} đ)
                        </span>
                        <button
                          className="btn-kiosk-action"
                          style={{ padding: '6px 14px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '5px', background: '#b91c1c', color: '#ffffff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                          onClick={() => onOpenVietQrModal(res)}
                        >
                          <QrCode size={13} />
                          Quét VietQR nộp phạt
                        </button>
                      </div>
                    )
                  ) : (
                    <span style={{
                      padding: '5px 12px',
                      borderRadius: '9999px',
                      fontSize: '12px',
                      fontWeight: '700',
                      background: '#f0fdf4',
                      color: '#16a34a',
                      border: '1px solid #bbf7d0',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      <CheckCircle2 size={13} />
                      Đúng hạn (0đ)
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Nút Hoàn thành (Chặn tuyệt đối nếu chưa nộp phạt sách quá hạn) */}
        {(() => {
          const unpaidCount = returnedBooks.filter(b => b.isOverdue && !b.isPaid).length;
          const hasUnpaidFines = unpaidCount > 0;
          const isDisabled = returnedBooks.length === 0 || hasUnpaidFines;

          return (
            <div className="kiosk-bottom-bar" style={{ flexDirection: 'column', gap: '10px' }}>
              {hasUnpaidFines && (
                <div style={{
                  width: '100%',
                  padding: '10px 16px',
                  background: '#fffbeb',
                  border: '1px solid #fde68a',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  color: '#92400e',
                  fontSize: '13px'
                }}>
                  <AlertTriangle size={18} color="#d97706" style={{ flexShrink: 0 }} />
                  <span>
                    <strong>Yêu cầu nộp phạt:</strong> Có {unpaidCount} cuốn sách quá hạn chưa thanh toán. Vui lòng bấm <strong>"Quét VietQR nộp phạt"</strong> và xác nhận để hoàn tất giao dịch!
                  </span>
                </div>
              )}

              <button
                className="btn-kiosk-finish"
                disabled={isDisabled}
                style={{
                  width: '100%',
                  opacity: isDisabled ? 0.5 : 1,
                  cursor: isDisabled ? 'not-allowed' : 'pointer',
                  background: hasUnpaidFines ? '#64748b' : undefined
                }}
                onClick={onConfirmFinish}
              >
                <CheckCircle2 size={20} strokeWidth={2.5} />
                <span>
                  {hasUnpaidFines 
                    ? `Chờ nộp phạt trễ hạn (${unpaidCount} cuốn chưa thanh toán)` 
                    : `Hoàn thành trả sách (${returnedBooks.length})`}
                </span>
              </button>
            </div>
          );
        })()}
      </main>
    </div>
  );
}
