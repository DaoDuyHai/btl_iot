import React, { useState } from 'react';
import { 
  BookmarkCheck, 
  Clock, 
  BookOpen, 
  AlertTriangle, 
  CreditCard, 
  ShieldAlert, 
  GraduationCap, 
  Mail, 
  Phone, 
  Radio, 
  CheckCircle2, 
  ArrowRight, 
  BookPlus, 
  RefreshCw, 
  User, 
  Sparkles,
  ExternalLink
} from 'lucide-react';
import AccountDetailModal from '../../components/AccountDetailModal.jsx';

export default function AccountSection({ 
  reader, 
  activeLoans = [], 
  onNavigate, 
  onFinish 
}) {
  const [activeModal, setActiveModal] = useState(null);

  const overdueCount = activeLoans.filter(l => new Date() > new Date(l.dueDate)).length;
  const totalFine = activeLoans.reduce((sum, l) => {
    if (l.fineAmount) return sum + l.fineAmount;
    if (new Date() > new Date(l.dueDate)) {
      const diffTime = Math.abs(new Date() - new Date(l.dueDate));
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return sum + (diffDays * 5000);
    }
    return sum;
  }, 0);

  // Avatar initial letter
  const nameInitial = reader?.name ? reader.name.trim().charAt(reader.name.trim().lastIndexOf(' ') + 1) || reader.name.charAt(0) : 'U';

  return (
    <div className="kiosk-workspace" style={{ maxWidth: '1240px' }}>
      {/* 1/3 Cột Trái: Thẻ Sinh Viên Điện Tử PTIT (Smart Student Digital Badge) */}
      <aside className="kiosk-sidebar-left" style={{ width: '340px', padding: 0, background: 'transparent', border: 'none', boxShadow: 'none' }}>
        <div className="ptit-id-badge">
          {/* Header thẻ PTIT */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '6px',
                background: '#b91c1c',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '900',
                fontSize: '12px'
              }}>
                P
              </div>
              <div>
                <div style={{ fontSize: '11px', fontWeight: '900', color: '#991b1b', letterSpacing: '0.5px' }}>
                  HỌC VIỆN CNBCVT
                </div>
                <div style={{ fontSize: '9px', color: '#64748b', fontWeight: '700' }}>
                  PTIT LIBRARY SMARTCARD
                </div>
              </div>
            </div>
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '10px',
              fontWeight: '800',
              background: '#dcfce7',
              color: '#15803d',
              padding: '2px 8px',
              borderRadius: '9999px',
              border: '1px solid #bbf7d0'
            }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e' }}></span>
              ACTIVE
            </span>
          </div>

          {/* Chip EMV & NFC Contactless Symbol */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
            <div className="ptit-chip-visual"></div>
            <Radio size={22} color="#b91c1c" className="animate-pulse" />
          </div>

          {/* Avatar & Họ tên bạn đọc */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #b91c1c 0%, #dc2626 100%)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: '900',
              fontSize: '22px',
              boxShadow: '0 4px 12px rgba(185, 28, 28, 0.3)',
              border: '2px solid #ffffff'
            }}>
              {nameInitial}
            </div>
            <div>
              <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', textTransform: 'uppercase' }}>
                BẠN ĐỌC THƯ VIỆN
              </div>
              <div style={{ fontSize: '18px', fontWeight: '900', color: '#0f172a', lineHeight: 1.2 }}>
                {reader?.name || 'Nguyễn Văn A'}
              </div>
            </div>
          </div>

          {/* Chi tiết thông tin định danh */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.85)',
            borderRadius: '14px',
            padding: '14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            fontSize: '13px',
            border: '1px solid #fecaca'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <User size={13} color="#991b1b" /> Mã SV (MSSV):
              </span>
              <strong style={{ color: '#0f172a', fontFamily: 'monospace', fontSize: '14px', fontWeight: '800' }}>
                {reader?.studentId || 'B21DCCN001'}
              </strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Radio size={13} color="#991b1b" /> Thẻ RFID:
              </span>
              <code style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', color: '#475569' }}>
                {reader?.rfidCard || 'E3A89F02'}
              </code>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Mail size={13} color="#991b1b" /> Email:
              </span>
              <span style={{ color: '#2563eb', fontWeight: '600', maxWidth: '170px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={reader?.email}>
                {reader?.email || 'sinhvien@ptit.edu.vn'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Phone size={13} color="#991b1b" /> Hotline:
              </span>
              <span style={{ color: '#0f172a', fontWeight: '600' }}>
                {reader?.phone || '0988 123 456'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <GraduationCap size={13} color="#991b1b" /> Khoa:
              </span>
              <span style={{ color: '#0f172a', fontWeight: '600', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {reader?.department || 'Khoa CNTT 1'}
              </span>
            </div>
          </div>

          {/* Footer thẻ bạn đọc */}
          <div style={{
            marginTop: '14px',
            padding: '10px 12px',
            background: '#ffffff',
            borderRadius: '10px',
            border: '1px solid #fee2e2',
            fontSize: '11px',
            color: '#64748b',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Sparkles size={14} color="#b91c1c" />
            <span>Đồng bộ thời gian thực với hệ thống <strong>Koha PTIT</strong></span>
          </div>
        </div>
      </aside>

      {/* 2/3 Cột Phải: 6 Thẻ Thống Kê Modern SaaS Dashboard (Click xem chi tiết) */}
      <main className="kiosk-content-right" style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '22px', fontWeight: '900', color: '#0f172a', margin: 0 }}>
                TỔNG QUAN TÀI KHOẢN BẠN ĐỌC
              </h2>
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
              Chạm vào bất kỳ khối chỉ số nào dưới đây để xem danh sách tài liệu chi tiết
            </p>
          </div>
          <span style={{ 
            fontSize: '12px', 
            background: '#fef2f2', 
            color: '#b91c1c', 
            padding: '6px 14px', 
            borderRadius: '9999px', 
            fontWeight: '800', 
            border: '1px solid #fecaca',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <CheckCircle2 size={14} /> Koha Synchronized
          </span>
        </div>

        {/* 6 Khối Dashboard Đẳng Cấp Hiện Đại */}
        <div className="reader-stats-grid" style={{ flex: 1 }}>
          {/* Ô 1: Đặt mượn (Holds) */}
          <div 
            className="stat-card-premium variant-primary"
            onClick={() => setActiveModal('HOLDS')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: '#eff6ff',
                color: '#2563eb',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <BookmarkCheck size={24} />
              </div>
              <span style={{
                fontSize: '11px',
                fontWeight: '700',
                background: '#f1f5f9',
                color: '#475569',
                padding: '4px 8px',
                borderRadius: '6px'
              }}>
                Chờ giữ sách
              </span>
            </div>
            <div style={{ marginTop: '14px' }}>
              <div style={{ fontSize: '28px', fontWeight: '900', color: '#0f172a', lineHeight: 1 }}>
                0
              </div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#334155', marginTop: '6px' }}>
                Yêu cầu đặt mượn trước
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#64748b', marginTop: '8px', fontWeight: '600' }}>
                Chi tiết đặt giữ <ExternalLink size={12} />
              </div>
            </div>
          </div>

          {/* Ô 2: Tài liệu đặt mượn không có sẵn */}
          <div 
            className="stat-card-premium variant-warning"
            onClick={() => setActiveModal('UNAVAILABLE_HOLDS')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: '#fff7ed',
                color: '#ea580c',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Clock size={24} />
              </div>
              <span style={{
                fontSize: '11px',
                fontWeight: '700',
                background: '#f1f5f9',
                color: '#475569',
                padding: '4px 8px',
                borderRadius: '6px'
              }}>
                Đang chờ trả
              </span>
            </div>
            <div style={{ marginTop: '14px' }}>
              <div style={{ fontSize: '28px', fontWeight: '900', color: '#0f172a', lineHeight: 1 }}>
                0
              </div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#334155', marginTop: '6px' }}>
                Đặt mượn chưa có sẵn
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#64748b', marginTop: '8px', fontWeight: '600' }}>
                Xem hàng chờ <ExternalLink size={12} />
              </div>
            </div>
          </div>

          {/* Ô 3: Tài liệu đang mượn */}
          <div 
            className="stat-card-premium variant-primary"
            onClick={() => setActiveModal('BORROWED')}
            style={{
              background: activeLoans.length > 0 ? '#faf5ff' : '#ffffff',
              borderColor: activeLoans.length > 0 ? '#e9d5ff' : '#f1f5f9'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: '#f3e8ff',
                color: '#9333ea',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <BookOpen size={24} />
              </div>
              <span style={{
                fontSize: '11px',
                fontWeight: '800',
                background: activeLoans.length > 0 ? '#dbeafe' : '#f1f5f9',
                color: activeLoans.length > 0 ? '#1d4ed8' : '#475569',
                padding: '4px 10px',
                borderRadius: '9999px'
              }}>
                {activeLoans.length > 0 ? 'Đang lưu hành' : 'Không có'}
              </span>
            </div>
            <div style={{ marginTop: '14px' }}>
              <div style={{ fontSize: '28px', fontWeight: '900', color: '#0f172a', lineHeight: 1 }}>
                {activeLoans.length} <span style={{ fontSize: '16px', fontWeight: '600', color: '#64748b' }}>cuốn</span>
              </div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#334155', marginTop: '6px' }}>
                Tài liệu đang mượn
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#9333ea', marginTop: '8px', fontWeight: '700' }}>
                Bấm xem danh sách ({activeLoans.length}) <ArrowRight size={13} />
              </div>
            </div>
          </div>

          {/* Ô 4: Tài liệu quá hạn */}
          <div 
            className={`stat-card-premium ${overdueCount > 0 ? 'variant-danger' : 'variant-success'}`}
            onClick={() => setActiveModal('OVERDUE')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: overdueCount > 0 ? '#fee2e2' : '#dcfce7',
                color: overdueCount > 0 ? '#dc2626' : '#16a34a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <AlertTriangle size={24} />
              </div>
              <span style={{
                fontSize: '11px',
                fontWeight: '800',
                background: overdueCount > 0 ? '#fee2e2' : '#dcfce7',
                color: overdueCount > 0 ? '#b91c1c' : '#15803d',
                padding: '4px 10px',
                borderRadius: '9999px'
              }}>
                {overdueCount > 0 ? 'Cảnh báo trễ hạn' : 'Đúng hạn tốt'}
              </span>
            </div>
            <div style={{ marginTop: '14px' }}>
              <div style={{ 
                fontSize: '28px', 
                fontWeight: '900', 
                color: overdueCount > 0 ? '#dc2626' : '#15803d', 
                lineHeight: 1 
              }}>
                {overdueCount} <span style={{ fontSize: '16px', fontWeight: '600', color: '#64748b' }}>cuốn</span>
              </div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#334155', marginTop: '6px' }}>
                Tài liệu quá hạn hoàn trả
              </div>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '4px', 
                fontSize: '12px', 
                color: overdueCount > 0 ? '#b91c1c' : '#15803d', 
                marginTop: '8px', 
                fontWeight: '700' 
              }}>
                {overdueCount > 0 ? '⚠️ Xem sách trễ hạn ngay' : 'Không có tài liệu trễ hạn'} <ArrowRight size={13} />
              </div>
            </div>
          </div>

          {/* Ô 5: Tài liệu được yêu cầu trả lại (Recalls) */}
          <div 
            className="stat-card-premium variant-warning"
            onClick={() => setActiveModal('RECALLS')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: '#fef3c7',
                color: '#d97706',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <ShieldAlert size={24} />
              </div>
              <span style={{
                fontSize: '11px',
                fontWeight: '700',
                background: '#f1f5f9',
                color: '#475569',
                padding: '4px 8px',
                borderRadius: '6px'
              }}>
                Thu hồi đặc biệt
              </span>
            </div>
            <div style={{ marginTop: '14px' }}>
              <div style={{ fontSize: '28px', fontWeight: '900', color: '#0f172a', lineHeight: 1 }}>
                0
              </div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#334155', marginTop: '6px' }}>
                Yêu cầu trả khẩn cấp
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#64748b', marginTop: '8px', fontWeight: '600' }}>
                Kiểm tra thông báo <ExternalLink size={12} />
              </div>
            </div>
          </div>

          {/* Ô 6: Tài liệu bị phạt / Lệ phí trễ hạn */}
          <div 
            className={`stat-card-premium ${totalFine > 0 ? 'variant-danger' : 'variant-success'}`}
            onClick={() => setActiveModal('FINES')}
            style={{
              background: totalFine > 0 ? '#fff5f5' : '#ffffff'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: totalFine > 0 ? '#fee2e2' : '#ecfdf5',
                color: totalFine > 0 ? '#b91c1c' : '#059669',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <CreditCard size={24} />
              </div>
              <span style={{
                fontSize: '11px',
                fontWeight: '800',
                background: totalFine > 0 ? '#dc2626' : '#dcfce7',
                color: totalFine > 0 ? '#ffffff' : '#15803d',
                padding: '4px 10px',
                borderRadius: '9999px'
              }}>
                {totalFine > 0 ? 'Cần thanh toán' : 'Không nợ phí'}
              </span>
            </div>
            <div style={{ marginTop: '14px' }}>
              <div style={{ 
                fontSize: '24px', 
                fontWeight: '900', 
                color: totalFine > 0 ? '#dc2626' : '#059669', 
                lineHeight: 1 
              }}>
                {totalFine.toLocaleString('vi-VN')} <span style={{ fontSize: '14px', fontWeight: '700' }}>VNĐ</span>
              </div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#334155', marginTop: '6px' }}>
                Lệ phí phạt trễ hạn
              </div>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '4px', 
                fontSize: '12px', 
                color: totalFine > 0 ? '#dc2626' : '#059669', 
                marginTop: '8px', 
                fontWeight: '800' 
              }}>
                {totalFine > 0 ? '⚡ Bấm quét VietQR nộp phạt' : 'Tài khoản sạch phí'} <ArrowRight size={13} />
              </div>
            </div>
          </div>
        </div>

        {/* Thanh chuyển chức năng nhanh dưới đáy */}
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          gap: '14px',
          marginTop: '26px',
          paddingTop: '20px',
          borderTop: '1.5px solid #e2e8f0'
        }}>
          <button
            className="btn-kiosk-action"
            onClick={() => onNavigate('BORROW')}
            style={{ background: 'linear-gradient(135deg, #15803d 0%, #166534 100%)' }}
          >
            <BookPlus size={18} />
            <span>Mượn thêm sách</span>
          </button>

          <button
            className="btn-kiosk-action"
            onClick={() => onNavigate('RENEW')}
            style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #172554 100%)' }}
          >
            <RefreshCw size={18} />
            <span>Gia hạn tài liệu</span>
          </button>

          <button
            className="btn-kiosk-finish"
            onClick={onFinish}
          >
            <CheckCircle2 size={20} strokeWidth={2.5} />
            <span>Hoàn thành phiên</span>
          </button>
        </div>
      </main>

      {/* Modal chi tiết thông tin */}
      {activeModal && (
        <AccountDetailModal
          modalType={activeModal}
          reader={reader}
          activeLoans={activeLoans}
          onClose={() => setActiveModal(null)}
          onNavigate={(target) => {
            setActiveModal(null);
            onNavigate(target);
          }}
        />
      )}
    </div>
  );
}


