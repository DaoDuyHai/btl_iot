import React, { useState } from 'react';
import { RefreshCw, Printer, CheckCircle2, AlertCircle, BookOpen } from 'lucide-react';

export default function RenewSection({ 
  reader, 
  activeLoans, 
  onRenewLoans, 
  onFinish, 
  onPrintReceipt 
}) {
  const [selectedIds, setSelectedIds] = useState([]);

  const now = new Date();
  // Chỉ các sách chưa quá hạn mới được phép gia hạn
  const renewableLoans = activeLoans.filter(l => now <= new Date(l.dueDate));

  function toggleSelect(loan) {
    const isOverdue = now > new Date(loan.dueDate);
    if (isOverdue) return; // Chặn không cho chọn sách quá hạn

    setSelectedIds(prev => 
      prev.includes(loan._id) ? prev.filter(x => x !== loan._id) : [...prev, loan._id]
    );
  }

  function handleSelectAll() {
    if (selectedIds.length === renewableLoans.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(renewableLoans.map(l => l._id));
    }
  }

  function handleRenewSelected() {
    if (selectedIds.length === 0) return;
    onRenewLoans(selectedIds);
    setSelectedIds([]);
  }

  function handleRenewAll() {
    const allRenewableIds = renewableLoans.map(l => l._id);
    if (allRenewableIds.length === 0) return;
    onRenewLoans(allRenewableIds);
    setSelectedIds([]);
  }

  return (
    <div className="kiosk-workspace" style={{ maxWidth: '1100px' }}>
      <main className="kiosk-content-right" style={{ width: '100%' }}>
        {/* Tiêu đề & Thông tin độc giả */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#991b1b', margin: 0 }}>
              GIA HẠN TÀI LIỆU TRỰC TUYẾN
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
              Bạn đọc: <strong>{reader?.name}</strong> (MSSV: {reader?.studentId})
            </p>
          </div>
          <span style={{ fontSize: '12px', background: '#fee2e2', color: '#991b1b', padding: '5px 14px', borderRadius: '9999px', fontWeight: '700', border: '1px solid #fecaca' }}>
            Đang mượn: {activeLoans.length} cuốn
          </span>
        </div>

        {/* Bảng danh sách sách gia hạn */}
        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '14px', minHeight: '320px', background: '#ffffff' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '100px 1fr 220px',
            padding: '12px 16px',
            background: '#f8fafc',
            borderBottom: '2px solid #e2e8f0',
            fontWeight: '800',
            color: '#475569',
            fontSize: '13px',
            textTransform: 'uppercase'
          }}>
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }} onClick={handleSelectAll}>
              <input 
                type="checkbox" 
                checked={selectedIds.length === renewableLoans.length && renewableLoans.length > 0} 
                onChange={handleSelectAll}
                style={{ cursor: 'pointer', width: '16px', height: '16px' }}
              />
              <span>Chọn tất</span>
            </div>
            <div>Tiêu đề & Thông tin tài liệu</div>
            <div style={{ textAlign: 'right' }}>Hạn trả hiện tại</div>
          </div>

          {activeLoans.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: '#f8fafc', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <BookOpen size={32} color="#94a3b8" />
              </div>
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#334155' }}>Bạn hiện không có tài liệu nào cần gia hạn</div>
            </div>
          ) : (
            activeLoans.map((loan) => {
              const isChecked = selectedIds.includes(loan._id);
              const dueDate = new Date(loan.dueDate);
              const dueDateStr = `${dueDate.toLocaleDateString('vi-VN')} 23:59`;
              const isOverdue = now > dueDate;

              return (
                <div 
                  key={loan._id} 
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '100px 1fr 220px',
                    padding: '16px',
                    borderBottom: '1px solid #f1f5f9',
                    alignItems: 'center',
                    background: isOverdue ? '#fef2f2' : isChecked ? '#fff1f2' : 'transparent',
                    cursor: isOverdue ? 'not-allowed' : 'pointer',
                    opacity: isOverdue ? 0.75 : 1
                  }}
                  onClick={() => toggleSelect(loan)}
                >
                  <div>
                    <input 
                      type="checkbox" 
                      disabled={isOverdue}
                      checked={isChecked} 
                      onChange={() => toggleSelect(loan)}
                      style={{ cursor: isOverdue ? 'not-allowed' : 'pointer', width: '18px', height: '18px' }}
                    />
                  </div>
                  <div>
                    <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '15px' }}>
                      {loan.bookId?.title}
                    </div>
                    <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                      Tác giả: <strong>{loan.bookId?.author}</strong> | RFID: <code>{loan.bookId?.rfidTag}</code> | Đã gia hạn: <strong>{loan.renewCount || 0}/2 lần</strong>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ 
                      fontWeight: '800', 
                      color: isOverdue ? '#b91c1c' : '#0f172a',
                      fontSize: '14px' 
                    }}>
                      {dueDateStr}
                    </span>
                    <div>
                      {isOverdue ? (
                        <span style={{ fontSize: '11px', color: '#b91c1c', fontWeight: '700', background: '#fee2e2', padding: '2px 8px', borderRadius: '4px' }}>
                          ⚠️ Quá hạn - Không thể gia hạn
                        </span>
                      ) : (
                        <span style={{ fontSize: '11px', color: '#16a34a', fontWeight: '600' }}>
                          ✓ Hợp lệ để gia hạn (+14 ngày)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Thanh nút thao tác dưới đáy */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '20px',
          paddingTop: '16px',
          borderTop: '1px solid #e2e8f0'
        }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              className="btn-kiosk-action"
              onClick={handleRenewAll}
              disabled={renewableLoans.length === 0}
              style={{
                background: '#b91c1c',
                opacity: renewableLoans.length === 0 ? 0.5 : 1,
                cursor: renewableLoans.length === 0 ? 'not-allowed' : 'pointer'
              }}
            >
              <RefreshCw size={16} />
              <span>Gia hạn tất cả ({renewableLoans.length})</span>
            </button>

            <button
              className="btn-kiosk-action"
              onClick={handleRenewSelected}
              disabled={selectedIds.length === 0}
              style={{
                background: selectedIds.length > 0 ? '#991b1b' : '#cbd5e1',
                color: selectedIds.length > 0 ? '#ffffff' : '#64748b',
                cursor: selectedIds.length > 0 ? 'pointer' : 'not-allowed'
              }}
            >
              <RefreshCw size={16} />
              <span>Gia hạn đã chọn ({selectedIds.length})</span>
            </button>

            <button
              className="btn-kiosk-secondary"
              onClick={onPrintReceipt}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Printer size={16} />
              <span>In biên lai</span>
            </button>
          </div>

          <button className="btn-kiosk-finish" onClick={onFinish}>
            <CheckCircle2 size={20} strokeWidth={2.5} />
            <span>Hoàn thành</span>
          </button>
        </div>
      </main>
    </div>
  );
}
