import React from 'react';
import { 
  BookOpen, 
  AlertTriangle, 
  CreditCard, 
  BookmarkCheck, 
  Clock, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowRight, 
  X, 
  Calendar, 
  Sparkles,
  Info
} from 'lucide-react';

export default function AccountDetailModal({ 
  modalType, 
  reader, 
  activeLoans = [], 
  onClose, 
  onNavigate 
}) {
  if (!modalType) return null;

  const now = new Date();

  // Danh sách các sách quá hạn
  const overdueLoans = activeLoans.filter(l => now > new Date(l.dueDate));
  
  // Tính tổng tiền phạt
  const totalFine = activeLoans.reduce((sum, l) => {
    if (l.fineAmount) return sum + l.fineAmount;
    if (now > new Date(l.dueDate)) {
      const diffTime = Math.abs(now - new Date(l.dueDate));
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return sum + (diffDays * 5000);
    }
    return sum;
  }, 0);

  // Cấu hình tiêu đề và nội dung theo từng loại thẻ
  const config = {
    BORROWED: {
      title: `Danh sách tài liệu đang mượn (${activeLoans.length})`,
      icon: <BookOpen size={24} color="#9333ea" />,
      bgIcon: '#f3e8ff',
      desc: 'Chi tiết các cuốn sách bạn đọc hiện đang mượn từ thư viện PTIT.'
    },
    OVERDUE: {
      title: `Danh sách tài liệu quá hạn (${overdueLoans.length})`,
      icon: <AlertTriangle size={24} color="#dc2626" />,
      bgIcon: '#fee2e2',
      desc: 'Các tài liệu đã vượt quá thời hạn mượn và đang phát sinh tiền phạt trễ hạn.'
    },
    FINES: {
      title: 'Chi tiết tiền phạt & lệ phí trễ hạn',
      icon: <CreditCard size={24} color="#b91c1c" />,
      bgIcon: '#fee2e2',
      desc: 'Chính sách phạt trễ hạn: 5.000 VNĐ / ngày / tài liệu theo quy định thư viện PTIT.'
    },
    HOLDS: {
      title: 'Yêu cầu đặt mượn trước (Holds)',
      icon: <BookmarkCheck size={24} color="#2563eb" />,
      bgIcon: '#eff6ff',
      desc: 'Danh sách các tài liệu bạn đọc đã đăng ký giữ chỗ trước trên hệ thống.'
    },
    UNAVAILABLE_HOLDS: {
      title: 'Tài liệu đặt mượn không có sẵn',
      icon: <Clock size={24} color="#ea580c" />,
      bgIcon: '#fff7ed',
      desc: 'Các tài liệu bạn đọc đặt trước nhưng đang được mượn bởi độc giả khác.'
    },
    RECALLS: {
      title: 'Tài liệu được yêu cầu thu hồi',
      icon: <ShieldAlert size={24} color="#d97706" />,
      bgIcon: '#fef3c7',
      desc: 'Các tài liệu thuộc diện thu hồi đặc biệt theo yêu cầu của ban quản lý thư viện.'
    }
  }[modalType] || {
    title: 'Chi tiết thông tin bạn đọc',
    icon: <Info size={24} color="#475569" />,
    bgIcon: '#f1f5f9',
    desc: ''
  };

  return (
    <div className="swipe-modal-backdrop" style={{ zIndex: 120 }}>
      <div className="swipe-modal-box" style={{ maxWidth: '800px', textAlign: 'left', padding: '32px 34px' }}>
        {/* Header Modal */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '16px',
              background: config.bgIcon,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
            }}>
              {config.icon}
            </div>
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: '900', color: '#0f172a', margin: 0 }}>
                {config.title}
              </h2>
              <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
                {config.desc}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: '#f1f5f9',
              border: 'none',
              borderRadius: '50%',
              width: '36px',
              height: '36px',
              cursor: 'pointer',
              color: '#64748b',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Nội dung danh sách theo loại modal */}
        <div style={{ maxHeight: '380px', overflowY: 'auto', marginBottom: '22px', paddingRight: '6px' }}>
          {/* 1. HIỂN THỊ DANH SÁCH SÁCH ĐANG MƯỢN */}
          {modalType === 'BORROWED' && (
            activeLoans.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '44px 20px', color: '#94a3b8' }}>
                <BookOpen size={48} color="#cbd5e1" style={{ margin: '0 auto 12px' }} />
                <div style={{ fontSize: '16px', fontWeight: '700', color: '#334155' }}>Hiện bạn không có cuốn sách nào đang mượn.</div>
                <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
                  Bạn đọc có thể sang mục Mượn sách để đăng ký mượn tài liệu mới.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {activeLoans.map((loan, idx) => {
                  const dueDate = new Date(loan.dueDate);
                  const isOverdue = now > dueDate;
                  const diffTime = Math.abs(now - dueDate);
                  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                  return (
                    <div 
                      key={loan._id || idx}
                      style={{
                        padding: '16px 20px',
                        borderRadius: '14px',
                        border: isOverdue ? '1.5px solid #fecaca' : '1.5px solid #e2e8f0',
                        background: isOverdue ? '#fffdfd' : '#f8fafc',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: '800', color: '#0f172a', fontSize: '15px' }}>
                          {idx + 1}. {loan.bookId?.title || 'Tài liệu thư viện'}
                        </div>
                        <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>
                          Tác giả: <strong>{loan.bookId?.author || 'N/A'}</strong> | Thể loại: {loan.bookId?.category || 'Chung'} | RFID: <code>{loan.bookId?.rfidTag}</code>
                        </div>
                        <div style={{ fontSize: '12px', color: '#475569', marginTop: '4px' }}>
                          Ngày mượn: {loan.borrowDate ? new Date(loan.borrowDate).toLocaleDateString('vi-VN') : 'N/A'} 
                          {' ➔ '} 
                          Hạn trả: <strong style={{ color: isOverdue ? '#dc2626' : '#0f172a' }}>{dueDate.toLocaleDateString('vi-VN')}</strong>
                        </div>
                      </div>

                      <div style={{ textAlign: 'right', flexShrink: 0 }}>
                        {isOverdue ? (
                          <span style={{
                            padding: '6px 14px',
                            borderRadius: '9999px',
                            background: '#fee2e2',
                            color: '#b91c1c',
                            fontSize: '12px',
                            fontWeight: '800',
                            border: '1px solid #fecaca'
                          }}>
                            Quá hạn ({diffDays} ngày)
                          </span>
                        ) : (
                          <span style={{
                            padding: '6px 14px',
                            borderRadius: '9999px',
                            background: '#dcfce7',
                            color: '#15803d',
                            fontSize: '12px',
                            fontWeight: '800',
                            border: '1px solid #bbf7d0'
                          }}>
                            Còn {diffDays} ngày
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )
          )}

          {/* 2. HIỂN THỊ DANH SÁCH SÁCH QUÁ HẠN */}
          {modalType === 'OVERDUE' && (
            overdueLoans.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '44px 20px', color: '#15803d' }}>
                <CheckCircle2 size={48} color="#16a34a" style={{ margin: '0 auto 12px' }} />
                <div style={{ fontSize: '17px', fontWeight: '800', color: '#15803d' }}>Tài khoản của bạn rất tốt!</div>
                <p style={{ fontSize: '13px', color: '#64748b', marginTop: '6px' }}>
                  Không có tài liệu nào bị trễ hạn. Bạn đọc luôn trả sách đúng hạn quy định.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {overdueLoans.map((loan, idx) => {
                  const dueDate = new Date(loan.dueDate);
                  const diffTime = Math.abs(now - dueDate);
                  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                  const bookFine = diffDays * 5000;

                  return (
                    <div 
                      key={loan._id || idx}
                      style={{
                        padding: '16px 20px',
                        borderRadius: '14px',
                        border: '1.5px solid #fecaca',
                        background: '#fffdfd',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: '800', color: '#991b1b', fontSize: '15px' }}>
                          {idx + 1}. {loan.bookId?.title}
                        </div>
                        <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>
                          Tác giả: {loan.bookId?.author} | Hạn trả gốc: {dueDate.toLocaleDateString('vi-VN')}
                        </div>
                        <div style={{ fontSize: '12px', color: '#b91c1c', fontWeight: '700', marginTop: '4px' }}>
                          Trễ hạn: {diffDays} ngày (5.000đ/ngày)
                        </div>
                      </div>

                      <div style={{ textAlign: 'right', flexShrink: 0 }}>
                        <div style={{ fontSize: '16px', fontWeight: '900', color: '#dc2626' }}>
                          Phạt: {bookFine.toLocaleString('vi-VN')} đ
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )
          )}

          {/* 3. HIỂN THỊ CHI TIẾT LỆ PHÍ VÀ THANH TOÁN VIETQR */}
          {modalType === 'FINES' && (
            totalFine === 0 ? (
              <div style={{ textAlign: 'center', padding: '44px 20px', color: '#15803d' }}>
                <CheckCircle2 size={48} color="#16a34a" style={{ margin: '0 auto 12px' }} />
                <div style={{ fontSize: '17px', fontWeight: '800', color: '#15803d' }}>Số dư nợ phạt: 0 VNĐ</div>
                <p style={{ fontSize: '13px', color: '#64748b', marginTop: '6px' }}>
                  Bạn đọc không có bất kỳ khoản phí phạt hoặc lệ phí tồn đọng nào.
                </p>
              </div>
            ) : (
              <div>
                <div style={{
                  background: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
                  border: '1.5px solid #fecaca',
                  borderRadius: '16px',
                  padding: '16px 20px',
                  marginBottom: '18px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <span style={{ fontSize: '12px', color: '#7f1d1d', fontWeight: '700', textTransform: 'uppercase' }}>
                      Tổng tiền phạt trễ hạn tồn đọng:
                    </span>
                    <div style={{ fontSize: '26px', fontWeight: '900', color: '#b91c1c' }}>
                      {totalFine.toLocaleString('vi-VN')} VNĐ
                    </div>
                  </div>
                  <span style={{
                    padding: '6px 14px',
                    borderRadius: '9999px',
                    background: '#ffffff',
                    color: '#991b1b',
                    fontSize: '12px',
                    fontWeight: '800',
                    border: '1px solid #fca5a5'
                  }}>
                    {overdueLoans.length} cuốn quá hạn
                  </span>
                </div>

                {/* Mã QR thanh toán nộp phạt nhanh */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '20px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '16px',
                  padding: '18px'
                }}>
                  <div className="qr-scanner-frame" style={{ padding: '8px' }}>
                    <img 
                      src={`https://img.vietqr.io/image/970422-000124135246-compact2.png?amount=${totalFine}&addInfo=PHAT%20${reader?.studentId || 'SV'}&accountName=THU%20VIEN`}
                      alt="VietQR nộp phạt"
                      style={{ width: '130px', height: '130px', borderRadius: '8px', display: 'block' }}
                    />
                  </div>
                  <div style={{ fontSize: '13px', color: '#334155' }}>
                    <div style={{ fontWeight: '800', fontSize: '15px', marginBottom: '6px', color: '#0f172a' }}>
                      Thanh toán nộp phạt tự động qua VietQR:
                    </div>
                    <div>• Ngân hàng: <strong>MB Bank (Ngân hàng Quân Đội)</strong></div>
                    <div>• Số tài khoản: <strong style={{ color: '#b91c1c', fontSize: '14px', fontFamily: 'monospace' }}>000124135246</strong></div>
                    <div>• Nội dung CK: <strong style={{ fontFamily: 'monospace' }}>PHAT {reader?.studentId}</strong></div>
                    <div style={{ fontSize: '12px', color: '#64748b', marginTop: '6px' }}>
                      <em>Bạn đọc mở bất kỳ App ngân hàng nào (MB, VCB, BIDV, Momo,...) quét mã để thanh toán tức thì.</em>
                    </div>
                  </div>
                </div>
              </div>
            )
          )}

          {/* 4. CÁC MỤC ĐẶT MƯỢN / THU HỒI CHƯA CÓ DỮ LIỆU */}
          {['HOLDS', 'UNAVAILABLE_HOLDS', 'RECALLS'].includes(modalType) && (
            <div style={{ textAlign: 'center', padding: '44px 20px', color: '#64748b' }}>
              <Sparkles size={44} color="#94a3b8" style={{ margin: '0 auto 12px' }} />
              <div style={{ fontSize: '16px', fontWeight: '800', color: '#334155' }}>
                Hiện không có dữ liệu nào trong mục này
              </div>
              <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '6px' }}>
                Tài khoản bạn đọc đang ở trạng thái chuẩn của hệ thống Koha PTIT.
              </p>
            </div>
          )}
        </div>

        {/* Footer Buttons */}
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          gap: '12px',
          borderTop: '1px solid #e2e8f0',
          paddingTop: '18px'
        }}>
          {modalType === 'BORROWED' && activeLoans.length > 0 && (
            <button
              className="btn-kiosk-action"
              style={{ background: 'linear-gradient(135deg, #166534 0%, #14532d 100%)', padding: '12px 22px' }}
              onClick={() => {
                onClose();
                onNavigate('RENEW');
              }}
            >
              <span>Sang trang Gia hạn sách</span>
              <ArrowRight size={16} />
            </button>
          )}

          {modalType === 'OVERDUE' && overdueLoans.length > 0 && (
            <button
              className="btn-kiosk-finish"
              style={{ padding: '12px 24px', fontSize: '14px' }}
              onClick={() => {
                onClose();
                onNavigate('RETURN');
              }}
            >
              <span>Sang trang Trả tài liệu & Nộp phạt</span>
              <ArrowRight size={16} />
            </button>
          )}

          <button
            className="btn-kiosk-secondary"
            onClick={onClose}
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}


