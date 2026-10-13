import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, QrCode, Building2, CreditCard, Loader2, ArrowRight, X } from 'lucide-react';

export default function VietQrModal({ data, onClose, onConfirmPaid }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  if (!data) return null;

  const { book, reader, fineAmount, vietQrUrl } = data;
  const loanId = data.loan?._id || data.loanId || data._id;
  const qrImage = vietQrUrl || `https://img.vietqr.io/image/970422-000124135246-compact2.png?amount=${fineAmount || 0}&addInfo=PHAT%20${reader?.studentId || 'SV'}&accountName=THU%20VIEN`;

  async function handleConfirm() {
    setIsSubmitting(true);
    try {
      await onConfirmPaid(loanId);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ textAlign: 'center', maxWidth: '520px', padding: '34px 32px' }}>
        {/* Nút X đóng góc trên */}
        <button
          onClick={onClose}
          disabled={isSubmitting}
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

        {/* Badge trạng thái nộp phạt */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          background: '#fee2e2',
          color: '#991b1b',
          padding: '6px 16px',
          borderRadius: '9999px',
          fontSize: '12px',
          fontWeight: '800',
          marginBottom: '16px',
          border: '1px solid #fecaca'
        }}>
          <AlertTriangle size={15} color="#dc2626" />
          <span>TÀI LIỆU QUÁ HẠN • PHÁT SINH LỆ PHÍ PHẠT</span>
        </div>

        <h2 style={{ fontSize: '22px', fontWeight: '900', color: '#0f172a', marginBottom: '6px' }}>
          Thanh Toán Nộp Phạt Tự Động
        </h2>
        <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '18px', lineHeight: 1.5 }}>
          Tài liệu <strong>"{book?.title || 'Tài liệu thư viện'}"</strong> của bạn đọc <strong>{reader?.name || 'Bạn đọc'}</strong> đã quá hạn mượn theo quy định.
        </p>

        {/* Card số tiền nộp phạt nổi bật */}
        <div style={{
          background: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
          border: '1.5px solid #fecaca',
          borderRadius: '16px',
          padding: '14px 20px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ textAlign: 'left' }}>
            <span style={{ fontSize: '12px', color: '#991b1b', fontWeight: '700', textTransform: 'uppercase' }}>
              Số tiền phạt cần nộp:
            </span>
            <div style={{ fontSize: '26px', fontWeight: '900', color: '#b91c1c', lineHeight: 1.2 }}>
              {fineAmount?.toLocaleString('vi-VN')} <span style={{ fontSize: '16px', fontWeight: '700' }}>VNĐ</span>
            </div>
          </div>
          <span style={{
            fontSize: '11px',
            background: '#ffffff',
            color: '#991b1b',
            padding: '4px 10px',
            borderRadius: '8px',
            fontWeight: '800',
            border: '1px solid #fca5a5'
          }}>
            Napas 24/7
          </span>
        </div>

        {/* Khung VietQR Tech Scanner với Corner Brackets */}
        {qrImage && (
          <div style={{ marginBottom: '20px' }}>
            <div className="qr-scanner-frame">
              <span className="qr-corner qr-corner-tl"></span>
              <span className="qr-corner qr-corner-tr"></span>
              <span className="qr-corner qr-corner-bl"></span>
              <span className="qr-corner qr-corner-br"></span>
              <img
                src={qrImage}
                alt="VietQR nộp phạt"
                style={{
                  width: '210px',
                  height: '210px',
                  borderRadius: '12px',
                  display: 'block'
                }}
              />
            </div>

            {/* Thông tin chuyển khoản ngân hàng chuẩn */}
            <div style={{
              marginTop: '14px',
              padding: '12px 18px',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '14px',
              fontSize: '12px',
              color: '#334155',
              textAlign: 'left',
              lineHeight: 1.7
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #e2e8f0', paddingBottom: '4px', marginBottom: '4px' }}>
                <span style={{ color: '#64748b' }}>Ngân hàng thụ hưởng:</span>
                <strong>MB Bank (Ngân hàng Quân Đội)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #e2e8f0', paddingBottom: '4px', marginBottom: '4px' }}>
                <span style={{ color: '#64748b' }}>Số tài khoản:</span>
                <strong style={{ color: '#b91c1c', fontSize: '14px', fontFamily: 'monospace' }}>000124135246</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Nội dung chuyển khoản:</span>
                <strong style={{ color: '#0f172a', fontFamily: 'monospace' }}>PHAT {reader?.studentId || 'SV'}</strong>
              </div>
            </div>
          </div>
        )}

        {/* Nút hành động */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button 
            className="btn-kiosk-finish" 
            style={{ flex: 1, padding: '14px 20px', fontSize: '14px' }}
            disabled={isSubmitting}
            onClick={handleConfirm}
          >
            {isSubmitting ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Đang ghi nhận nộp phạt...</span>
              </>
            ) : (
              <>
                <CheckCircle2 size={18} strokeWidth={2.5} />
                <span>Đã chuyển khoản • Xác nhận nộp phạt</span>
              </>
            )}
          </button>
          
          <button 
            className="btn-kiosk-secondary" 
            disabled={isSubmitting}
            onClick={onClose}
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}


