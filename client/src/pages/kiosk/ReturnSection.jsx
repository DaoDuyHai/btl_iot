import React from 'react';
import ReaderInfoSidebar from '../../components/ReaderInfoSidebar.jsx';
import { BookUp, QrCode, CheckCircle2, AlertTriangle, Trash2, Clock, ShieldAlert } from 'lucide-react';

export default function ReturnSection({ 
  reader, 
  pendingReturns, 
  onRemoveItem,
  onConfirmFinish, 
  onOpenVietQrModal,
  isSubmitting = false
}) {
  const totalFine = pendingReturns.reduce((sum, item) => sum + (item.fineAmount || 0), 0);
  const overdueCount = pendingReturns.filter(item => item.isOverdue).length;

  return (
    <div className="kiosk-workspace">
      {/* 1/4 Cột Trái: Hiển thị bạn đọc (nếu có đăng nhập) hoặc Bảng hướng dẫn Trả tự phục vụ */}
      {reader ? (
        <ReaderInfoSidebar 
          reader={reader} 
          isReadingActive={true} 
        />
      ) : (
        <aside className="kiosk-sidebar-left" style={{ background: '#ffffff', borderRight: '1px solid #e2e8f0', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ textAlign: 'center', padding: '16px', background: '#f8fafc', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: '#fee2e2', color: '#b91c1c', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <BookUp size={30} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', margin: 0 }}>
              TRẢ SÁCH TỰ ĐỘNG
            </h3>
            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '6px' }}>
              Không cần quẹt thẻ sinh viên. Hệ thống tự động nhận diện độc giả qua mã RFID gắn trên sách.
            </p>
          </div>

          <div style={{ background: '#eff6ff', borderRadius: '12px', padding: '14px', border: '1px solid #dbeafe', fontSize: '13px', color: '#1e40af' }}>
            <div style={{ fontWeight: '700', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={16} /> Quy trình xử lý sách trả:
            </div>
            <ol style={{ paddingLeft: '18px', margin: 0, lineHeight: '1.6', fontSize: '12px', color: '#1e3a8a' }}>
              <li>Đặt sách vào vùng RFID để nhận diện.</li>
              <li>Kiểm tra thông tin trên màn hình.</li>
              <li>Bấm <strong>Hoàn thành trả sách</strong>.</li>
              <li>Thủ thư sẽ kiểm tra tình trạng vật lý (rách/hỏng) trước khi nhập kho.</li>
            </ol>
          </div>

          {totalFine > 0 && (
            <div style={{ background: '#fef2f2', borderRadius: '12px', padding: '14px', border: '1px solid #fecaca', fontSize: '12px', color: '#991b1b' }}>
              <div style={{ fontWeight: '700', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <ShieldAlert size={16} /> Lưu ý nợ phạt:
              </div>
              Phát hiện {overdueCount} tài liệu quá hạn. Bạn vẫn được hoàn tất trả sách để dừng ngày phạt; tiền phạt được lưu thành công nợ.
            </div>
          )}
        </aside>
      )}

      {/* 3/4 Cột Phải: Danh sách sách chờ xác nhận hoàn trả */}
      <main className="kiosk-content-right">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#991b1b', margin: 0 }}>
              DANH SÁCH CHỜ HOÀN TRẢ ({pendingReturns.length})
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
              Đặt lần lượt các tài liệu lên đầu đọc RFID. Bấm <strong>Hoàn thành trả sách</strong> để ghi nhận giao dịch.
            </p>
          </div>
          <span style={{ fontSize: '12px', background: '#f1f5f9', color: '#334155', padding: '5px 14px', borderRadius: '9999px', fontWeight: '700', border: '1px solid #cbd5e1' }}>
            Trạng thái sau trả: Chờ thủ thư kiểm tra
          </span>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '14px', background: '#ffffff' }}>
          <div className="kiosk-table-header" style={{ gridTemplateColumns: '60px 1fr 140px 180px 60px' }}>
            <div>STT</div>
            <div>Tiêu đề & Tác giả</div>
            <div>Người mượn</div>
            <div>Đối soát thời hạn</div>
            <div style={{ textAlign: 'center' }}>Xóa</div>
          </div>

          {pendingReturns.length === 0 ? (
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
                Hệ thống chỉ tạm lưu vào danh sách chờ và CHƯA cập nhật cơ sở dữ liệu cho đến khi bạn xác nhận.
              </p>
            </div>
          ) : (
            pendingReturns.map((item, idx) => (
              <div key={item.book?._id || item.book?.rfidTag || idx} className="kiosk-table-row" style={{ gridTemplateColumns: '60px 1fr 140px 180px 60px' }}>
                <div style={{ fontWeight: '800', color: '#b91c1c' }}>#{idx + 1}</div>
                <div>
                  <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '15px' }}>
                    {item.book?.title}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                    Tác giả: <strong>{item.book?.author}</strong> | RFID: <code>{item.book?.rfidTag}</code>
                  </div>
                </div>

                {/* Thông tin người đang mượn */}
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '700', color: '#1e293b' }}>
                    {item.reader?.name || 'Bạn đọc'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>
                    MSSV: {item.reader?.studentId || 'N/A'}
                  </div>
                </div>

                {/* Trạng thái quá hạn & tiền phạt */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {item.isOverdue ? (
                    <>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '700',
                        background: '#fee2e2',
                        color: '#b91c1c',
                        border: '1px solid #fecaca',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <AlertTriangle size={12} />
                        Quá hạn {item.overdueDays} ngày (+{item.fineAmount?.toLocaleString('vi-VN')} đ)
                      </span>
                      {item.vietQrUrl && (
                        <button
                          type="button"
                          onClick={() => onOpenVietQrModal(item)}
                          style={{
                            background: '#991b1b',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '3px 8px',
                            fontSize: '11px',
                            fontWeight: '700',
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            width: 'fit-content'
                          }}
                        >
                          <QrCode size={12} /> Quét QR nộp phạt
                        </button>
                      )}
                    </>
                  ) : (
                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '9999px',
                      fontSize: '12px',
                      fontWeight: '700',
                      background: '#f0fdf4',
                      color: '#16a34a',
                      border: '1px solid #bbf7d0',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      width: 'fit-content'
                    }}>
                      <CheckCircle2 size={13} />
                      Đúng hạn (0đ)
                    </span>
                  )}
                </div>

                {/* Nút Xóa khỏi danh sách chờ (Mục 4.1 STT 6) */}
                <div style={{ textAlign: 'center' }}>
                  <button
                    type="button"
                    title="Xóa khỏi danh sách quét nhầm"
                    onClick={() => onRemoveItem(item.book?.rfidTag)}
                    style={{
                      background: '#fee2e2',
                      border: '1px solid #fecaca',
                      color: '#ef4444',
                      borderRadius: '8px',
                      padding: '6px',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Thanh tác vụ dưới cùng: Luôn cho phép tiếp nhận sách kể cả khi chưa nộp phạt (Mục 2.1 STT 6 & 8) */}
        <div className="kiosk-bottom-bar" style={{ flexDirection: 'column', gap: '10px' }}>
          {totalFine > 0 && (
            <div style={{
              width: '100%',
              padding: '10px 16px',
              background: '#fffbeb',
              border: '1px solid #fde68a',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: '#92400e',
              fontSize: '13px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={18} color="#d97706" style={{ flexShrink: 0 }} />
                <span>
                  <strong>Tổng tiền phạt quá hạn:</strong> {totalFine.toLocaleString('vi-VN')} VNĐ ({overdueCount} cuốn trễ hạn).
                  Sách vẫn sẽ được tiếp nhận ngay; tiền phạt được lưu thành công nợ.
                </span>
              </div>
              <button
                type="button"
                onClick={() => onOpenVietQrModal(pendingReturns.find(p => p.isOverdue))}
                style={{
                  background: '#d97706',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '6px 14px',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px'
                }}
              >
                <QrCode size={14} /> Nộp phạt VietQR ngay
              </button>
            </div>
          )}

          <button
            className="btn-kiosk-finish"
            disabled={pendingReturns.length === 0 || isSubmitting}
            style={{
              width: '100%',
              opacity: pendingReturns.length === 0 || isSubmitting ? 0.5 : 1,
              cursor: pendingReturns.length === 0 || isSubmitting ? 'not-allowed' : 'pointer'
            }}
            onClick={onConfirmFinish}
          >
            <CheckCircle2 size={20} strokeWidth={2.5} />
            <span>
              {isSubmitting 
                ? 'Đang thực hiện giao dịch trả sách...' 
                : `Xác nhận hoàn thành trả tài liệu (${pendingReturns.length})`}
            </span>
          </button>
        </div>
      </main>
    </div>
  );
}
