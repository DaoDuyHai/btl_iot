import React, { useState, useEffect } from 'react';
import { apiService } from '../../api/apiService.js';
import { socket } from '../../socket/socketClient.js';
import { 
  ClipboardCheck, 
  BookOpen, 
  Users, 
  History, 
  Activity, 
  CheckCircle, 
  FileText
} from 'lucide-react';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('DASHBOARD'); // 'DASHBOARD' | 'INSPECTION' | 'BOOKS' | 'READERS' | 'LOANS' | 'AUDIT'
  const [books, setBooks] = useState([]);
  const [readers, setReaders] = useState([]);
  const [loans, setLoans] = useState([]);
  const [pendingInspections, setPendingInspections] = useState([]);
  const [deviceLogs, setDeviceLogs] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);

  // Form states
  const [newBook, setNewBook] = useState({ isbn: '', title: '', author: '', category: 'CNTT', rfidTag: '', copyCode: '' });
  const [editingBook, setEditingBook] = useState(null);
  const [newReader, setNewReader] = useState({ studentId: '', name: '', email: '', phone: '', rfidCard: '' });
  const [editingReader, setEditingReader] = useState(null);

  // Modal kiểm tra tình trạng vật lý sách
  const [inspectModalLoan, setInspectModalLoan] = useState(null);
  const [inspectForm, setInspectForm] = useState({
    result: 'normal',
    damageType: 'none',
    damageDescription: '',
    damageFine: 0,
    inspectionNotes: ''
  });

  // Modal trả sách thủ công
  const [manualReturnModal, setManualReturnModal] = useState(null);
  const [manualReturnReason, setManualReturnReason] = useState('Nhãn RFID bị rách hoặc không đọc được');

  const [msg, setMsg] = useState(null);

  useEffect(() => {
    loadAllData();

    socket.on('loans:changed', () => {
      loadAllData();
    });

    return () => socket.off('loans:changed');
  }, []);

  async function loadAllData() {
    try {
      const [b, r, l, d, p, a] = await Promise.all([
        apiService.getBooks(),
        apiService.getReaders(),
        apiService.getLoanHistory(50),
        apiService.getDeviceLogs(20),
        apiService.getPendingInspection(),
        apiService.getAudits(30)
      ]);
      setBooks(b || []);
      setReaders(r || []);
      setLoans(l || []);
      setDeviceLogs(d || []);
      setPendingInspections(p || []);
      setAuditLogs(a || []);
    } catch (err) {
      console.error('Lỗi tải dữ liệu admin:', err);
    }
  }

  function showToast(text) {
    setMsg(text);
    setTimeout(() => setMsg(null), 3500);
  }

  // Thêm sách mới
  async function handleAddBook(e) {
    e.preventDefault();
    try {
      await apiService.createBook(newBook);
      showToast('✅ Đã thêm tài liệu mới vào kho thành công!');
      setNewBook({ isbn: '', title: '', author: '', category: 'CNTT', rfidTag: '', copyCode: '' });
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Cập nhật sách
  async function handleUpdateBook(e) {
    e.preventDefault();
    if (!editingBook) return;
    try {
      await apiService.updateBook(editingBook._id, editingBook);
      showToast('✅ Đã cập nhật thông tin tài liệu thành công!');
      setEditingBook(null);
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Xóa mềm sách
  async function handleDeleteBook(id, title) {
    if (!window.confirm(`Bạn có chắc chắn muốn ngừng lưu hành (Xóa mềm) cuốn sách "${title}"?`)) return;
    try {
      await apiService.deleteBook(id);
      showToast('✅ Đã ngừng lưu hành tài liệu thành công!');
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Thêm độc giả mới
  async function handleAddReader(e) {
    e.preventDefault();
    try {
      await apiService.createReader(newReader);
      showToast('✅ Đã thêm độc giả mới thành công!');
      setNewReader({ studentId: '', name: '', email: '', phone: '', rfidCard: '' });
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Cập nhật độc giả
  async function handleUpdateReader(e) {
    e.preventDefault();
    if (!editingReader) return;
    try {
      await apiService.updateReader(editingReader._id, editingReader);
      showToast('✅ Đã cập nhật thông tin độc giả thành công!');
      setEditingReader(null);
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Khóa / Mở khóa độc giả
  async function handleToggleBlockReader(reader) {
    const newStatus = !reader.active;
    const reason = newStatus ? '' : 'Bị tạm khóa do nợ phạt quá hạn hoặc vi phạm quy chế';
    try {
      await apiService.updateReader(reader._id, { active: newStatus, blockReason: reason });
      showToast(newStatus ? '✅ Đã mở khóa tài khoản độc giả!' : '🔒 Đã tạm khóa tài khoản độc giả!');
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Thực hiện nghiệm thu / kiểm tra sách sau trả
  async function handleInspectSubmit(e) {
    e.preventDefault();
    if (!inspectModalLoan) return;
    try {
      await apiService.inspectBook({
        loanId: inspectModalLoan._id,
        result: inspectForm.result,
        damageType: inspectForm.damageType,
        damageDescription: inspectForm.damageDescription,
        damageFine: Number(inspectForm.damageFine) || 0,
        inspectionNotes: inspectForm.inspectionNotes,
        actor: 'Thủ thư Trưởng'
      });
      showToast('✅ Đã hoàn tất kiểm tra vật lý tài liệu!');
      setInspectModalLoan(null);
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Trả sách thủ công
  async function handleManualReturnSubmit(e) {
    e.preventDefault();
    if (!manualReturnModal) return;
    try {
      await apiService.manualReturn({
        loanId: manualReturnModal._id,
        actor: 'Thủ thư Trưởng',
        reason: manualReturnReason
      });
      showToast('✅ Đã ghi nhận trả sách thủ công thành công! Sách chuyển sang chờ kiểm tra.');
      setManualReturnModal(null);
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Miễn phạt
  async function handleWaiveFine(loanId) {
    const reason = window.prompt('Nhập lý do miễn phạt cho độc giả (ví dụ: Miễn phạt theo quy chế):');
    if (!reason) return;
    try {
      await apiService.waiveFine(loanId, reason, 'Thủ thư Trưởng');
      showToast('✅ Đã miễn khoản phạt cho bạn đọc thành công!');
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Gửi lệnh test MQTT tới Kiosk
  async function handleTestFeedback(status) {
    try {
      await apiService.sendDeviceCommand('kiosk_01', 'feedback', status);
      showToast(`Đã gửi lệnh test còi & đèn (${status}) tới Kiosk!`);
    } catch (err) {
      alert('Lỗi gửi lệnh tới Kiosk: ' + (err.message || ''));
    }
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '24px auto', padding: '0 20px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      {/* Toast Notification */}
      {msg && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          background: '#0f172a',
          color: '#ffffff',
          padding: '12px 24px',
          borderRadius: '10px',
          zIndex: 9999,
          fontWeight: '700',
          boxShadow: '0 10px 25px rgba(0,0,0,0.2)'
        }}>
          {msg}
        </div>
      )}

      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: '900', color: '#991b1b', margin: 0 }}>
            HỆ THỐNG QUẢN TRỊ THƯ VIỆN KIOSK IOT - PTIT
          </h2>
          <p style={{ color: '#64748b', fontSize: '13px', margin: '4px 0 0' }}>
            Quản trị Vận hành, Kiểm tra Tài liệu sau Trả, Kiểm toán & Giám sát Phần cứng ESP32
          </p>
        </div>

        {/* Tab Navigation Buttons */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {[
            { id: 'DASHBOARD', label: '📊 Giám Sát IoT', icon: Activity },
            { id: 'INSPECTION', label: `🔍 Sách Chờ Kiểm Tra (${pendingInspections.length})`, icon: ClipboardCheck, badge: pendingInspections.length },
            { id: 'BOOKS', label: '📚 Kho Sách', icon: BookOpen },
            { id: 'READERS', label: '🎓 Độc Giả', icon: Users },
            { id: 'LOANS', label: '📜 Mượn & Trả', icon: History },
            { id: 'AUDIT', label: '🛡️ Nhật Ký Kiểm Toán', icon: FileText }
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                style={{
                  background: isActive ? '#991b1b' : '#ffffff',
                  color: isActive ? '#ffffff' : '#334155',
                  border: '1px solid',
                  borderColor: isActive ? '#991b1b' : '#cbd5e1',
                  padding: '8px 14px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ========================================================== */}
      {/* TAB 1: DASHBOARD & GIÁM SÁT IOT                           */}
      {/* ========================================================== */}
      {activeTab === 'DASHBOARD' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <div className="card" style={{ background: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '13px', color: '#64748b', fontWeight: '600' }}>Tổng đầu sách</span>
              <div style={{ fontSize: '28px', fontWeight: '800', color: '#1e293b', marginTop: '4px' }}>{books.length}</div>
            </div>
            <div className="card" style={{ background: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '13px', color: '#64748b', fontWeight: '600' }}>Sách đang mượn</span>
              <div style={{ fontSize: '28px', fontWeight: '800', color: '#d97706', marginTop: '4px' }}>
                {books.filter(b => b.status === 'borrowed').length}
              </div>
            </div>
            <div className="card" style={{ background: '#fef2f2', padding: '16px', borderRadius: '12px', border: '1px solid #fecaca' }}>
              <span style={{ fontSize: '13px', color: '#991b1b', fontWeight: '700' }}>Sách chờ thủ thư kiểm tra</span>
              <div style={{ fontSize: '28px', fontWeight: '900', color: '#b91c1c', marginTop: '4px' }}>
                {pendingInspections.length}
              </div>
            </div>
            <div className="card" style={{ background: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '13px', color: '#64748b', fontWeight: '600' }}>Độc giả đang hoạt động</span>
              <div style={{ fontSize: '28px', fontWeight: '800', color: '#16a34a', marginTop: '4px' }}>
                {readers.filter(r => r.active).length}
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
            <div className="card" style={{ background: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', marginBottom: '12px' }}>
                🎮 Điều Khiển Trạm Kiosk Từ Xa (MQTT)
              </h3>
              <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px', lineHeight: '1.5' }}>
                Gửi bản tin điều khiển trực tiếp từ Web xuống phần cứng ESP32 qua topic <code>kiosk/kiosk_01/command</code>.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <button
                  type="button"
                  style={{ background: '#16a34a', color: '#ffffff', border: 'none', padding: '10px 16px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                  onClick={() => handleTestFeedback('success')}
                >
                  🔊 Test Còi Bíp + Nhấp Nháy LED Xanh (Thành công)
                </button>
                <button
                  type="button"
                  style={{ background: '#dc2626', color: '#ffffff', border: 'none', padding: '10px 16px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                  onClick={() => handleTestFeedback('error')}
                >
                  🚨 Test Còi Bíp 3 Tiếng + LED Đỏ (Lỗi/Từ chối)
                </button>
              </div>
            </div>

            <div className="card" style={{ background: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', marginBottom: '12px' }}>
                📡 Nhật Ký Phần Cứng (Device Logs Realtime)
              </h3>
              <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                      <th style={{ padding: '8px' }}>Thời Gian</th>
                      <th style={{ padding: '8px' }}>Sự Kiện</th>
                      <th style={{ padding: '8px' }}>Dữ Liệu Gói Tin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {deviceLogs.map(log => (
                      <tr key={log._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '8px', color: '#64748b' }}>{new Date(log.timestamp).toLocaleTimeString('vi-VN')}</td>
                        <td style={{ padding: '8px' }}>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontWeight: '700',
                            background: log.event === 'scan' ? '#eff6ff' : '#f0fdf4',
                            color: log.event === 'scan' ? '#1d4ed8' : '#15803d'
                          }}>
                            {log.event.toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '8px' }}><code>{JSON.stringify(log.payload || {})}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* TAB 2: SÁCH CHỜ KIỂM TRA (MỤC 5)                           */}
      {/* ========================================================== */}
      {activeTab === 'INSPECTION' && (
        <div style={{ background: '#ffffff', padding: '24px', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#991b1b', margin: 0 }}>
                DANH SÁCH TÀI LIỆU VỪA TRẢ TẠI KIOSK - CHỜ THỦ THƯ KIỂM TRA VẬT LÝ ({pendingInspections.length})
              </h3>
              <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
                RFID chỉ xác thực số hiệu tài liệu. Thủ thư cần kiểm tra thực tế xem sách có bị rách bìa, vẽ bậy, ướt hoặc mất trang không trước khi nhập kho cho mượn tiếp.
              </p>
            </div>
          </div>

          {pendingInspections.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '50px 20px', color: '#64748b' }}>
              <CheckCircle size={48} color="#16a34a" style={{ margin: '0 auto 12px' }} />
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#1e293b' }}>
                Hiện tại không có tài liệu nào đang chờ kiểm tra!
              </div>
              <p style={{ fontSize: '13px', marginTop: '4px' }}>
                Mọi sách trả từ Kiosk đã được nghiệm thu và sắp xếp về đúng vị trí kho sách.
              </p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#475569' }}>
                    <th style={{ padding: '10px' }}>Tài Liệu</th>
                    <th style={{ padding: '10px' }}>Người Vừa Trả</th>
                    <th style={{ padding: '10px' }}>Thời Điểm Trả</th>
                    <th style={{ padding: '10px' }}>Phạt Quá Hạn</th>
                    <th style={{ padding: '10px' }}>Hình Thức Trả</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Thao Tác Nghiệm Thu</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingInspections.map(loan => (
                    <tr key={loan._id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '12px 10px' }}>
                        <div style={{ fontWeight: '700', color: '#0f172a' }}>{loan.bookId?.title}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>
                          Mã bản sao: <strong>{loan.bookId?.copyCode || 'CP-01'}</strong> | RFID: <code>{loan.bookId?.rfidTag}</code>
                        </div>
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <div style={{ fontWeight: '700', color: '#1e293b' }}>{loan.readerId?.name}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>MSSV: {loan.readerId?.studentId}</div>
                      </td>
                      <td style={{ padding: '12px 10px', color: '#475569' }}>
                        {loan.returnDate ? new Date(loan.returnDate).toLocaleString('vi-VN') : 'Mới đây'}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        {loan.overdueFine > 0 ? (
                          <span style={{ color: '#b91c1c', fontWeight: '700' }}>
                            +{loan.overdueFine?.toLocaleString('vi-VN')} đ ({loan.isPaid ? 'Đã nộp' : 'Ghi nợ'})
                          </span>
                        ) : (
                          <span style={{ color: '#16a34a', fontWeight: '600' }}>Đúng hạn (0đ)</span>
                        )}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', background: '#f1f5f9', color: '#334155' }}>
                          {loan.returnMethod === 'manual_librarian' ? 'Thủ công' : 'Kiosk RFID'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                        <button
                          type="button"
                          style={{
                            background: '#991b1b',
                            color: '#ffffff',
                            border: 'none',
                            padding: '6px 14px',
                            borderRadius: '6px',
                            fontWeight: '700',
                            fontSize: '12px',
                            cursor: 'pointer'
                          }}
                          onClick={() => {
                            setInspectModalLoan(loan);
                            setInspectForm({
                              result: 'normal',
                              damageType: 'none',
                              damageDescription: '',
                              damageFine: 0,
                              inspectionNotes: ''
                            });
                          }}
                        >
                          📋 Kiểm Tra & Nghiệm Thu
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ========================================================== */}
      {/* TAB 3: QUẢN LÝ KHO SÁCH                                   */}
      {/* ========================================================== */}
      {activeTab === 'BOOKS' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
          {/* Form thêm hoặc sửa sách */}
          <div style={{ background: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '800', marginBottom: '16px', color: '#0f172a' }}>
              {editingBook ? '✏️ Cập Nhật Thông Tin Sách' : '➕ Thêm Sách Mới'}
            </h3>
            <form onSubmit={editingBook ? handleUpdateBook : handleAddBook} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Tên Tài Liệu:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  value={editingBook ? editingBook.title : newBook.title}
                  onChange={e => editingBook ? setEditingBook({ ...editingBook, title: e.target.value }) : setNewBook({ ...newBook, title: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Tác Giả:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  value={editingBook ? editingBook.author : newBook.author}
                  onChange={e => editingBook ? setEditingBook({ ...editingBook, author: e.target.value }) : setNewBook({ ...newBook, author: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Mã Thẻ RFID (Gắn trên bìa sách):</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: A1B2C3D4"
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', textTransform: 'uppercase' }}
                  value={editingBook ? editingBook.rfidTag : newBook.rfidTag}
                  onChange={e => editingBook ? setEditingBook({ ...editingBook, rfidTag: e.target.value.toUpperCase() }) : setNewBook({ ...newBook, rfidTag: e.target.value.toUpperCase() })}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Mã Bản Sao (CopyCode):</label>
                  <input
                    type="text"
                    placeholder="CP-001"
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                    value={editingBook ? editingBook.copyCode : newBook.copyCode}
                    onChange={e => editingBook ? setEditingBook({ ...editingBook, copyCode: e.target.value }) : setNewBook({ ...newBook, copyCode: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Mã ISBN:</label>
                  <input
                    type="text"
                    required
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                    value={editingBook ? editingBook.isbn : newBook.isbn}
                    onChange={e => editingBook ? setEditingBook({ ...editingBook, isbn: e.target.value }) : setNewBook({ ...newBook, isbn: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button
                  type="submit"
                  style={{ flex: 1, background: '#991b1b', color: '#ffffff', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer' }}
                >
                  {editingBook ? 'Lưu Thay Đổi' : '➕ Thêm Vào Kho Sách'}
                </button>
                {editingBook && (
                  <button
                    type="button"
                    style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '10px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer' }}
                    onClick={() => setEditingBook(null)}
                  >
                    Hủy
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Danh mục sách */}
          <div style={{ background: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '800', marginBottom: '16px', color: '#0f172a' }}>Danh Sách Kho Tài Liệu</h3>
            <div style={{ maxHeight: '420px', overflowY: 'auto' }}>
              <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                    <th style={{ padding: '8px' }}>Tên Sách & Tác Giả</th>
                    <th style={{ padding: '8px' }}>Bản Sao / RFID</th>
                    <th style={{ padding: '8px' }}>Trạng Thái</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Hành Động</th>
                  </tr>
                </thead>
                <tbody>
                  {books.map(b => (
                    <tr key={b._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '10px 8px' }}>
                        <div style={{ fontWeight: '700', color: '#0f172a' }}>{b.title}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>{b.author}</div>
                      </td>
                      <td style={{ padding: '10px 8px' }}>
                        <div><code>{b.copyCode || 'CP-CHUNG'}</code></div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>RFID: <code>{b.rfidTag}</code></div>
                      </td>
                      <td style={{ padding: '10px 8px' }}>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: '700',
                          background: b.status === 'available' ? '#dcfce7' : b.status === 'borrowed' ? '#fef3c7' : b.status === 'pending_inspection' ? '#fee2e2' : '#f1f5f9',
                          color: b.status === 'available' ? '#15803d' : b.status === 'borrowed' ? '#b45309' : b.status === 'pending_inspection' ? '#b91c1c' : '#475569'
                        }}>
                          {b.status === 'available' ? 'Sẵn sàng' : b.status === 'borrowed' ? 'Đang mượn' : b.status === 'pending_inspection' ? 'Chờ kiểm tra' : b.status}
                        </span>
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                        <button
                          type="button"
                          style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '700', marginRight: '6px', cursor: 'pointer' }}
                          onClick={() => setEditingBook(b)}
                        >
                          Sửa
                        </button>
                        <button
                          type="button"
                          style={{ background: '#fee2e2', border: '1px solid #fecaca', color: '#ef4444', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                          onClick={() => handleDeleteBook(b._id, b.title)}
                        >
                          Xóa mềm
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* TAB 4: QUẢN LÝ ĐỘC GIẢ                                    */}
      {/* ========================================================== */}
      {activeTab === 'READERS' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
          {/* Form thêm/sửa độc giả */}
          <div style={{ background: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '800', marginBottom: '16px', color: '#0f172a' }}>
              {editingReader ? '✏️ Cập Nhật Độc Giả' : '➕ Thêm Độc Giả Mới'}
            </h3>
            <form onSubmit={editingReader ? handleUpdateReader : handleAddReader} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Mã Sinh Viên (MSSV):</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  value={editingReader ? editingReader.studentId : newReader.studentId}
                  onChange={e => editingReader ? setEditingReader({ ...editingReader, studentId: e.target.value.toUpperCase() }) : setNewReader({ ...newReader, studentId: e.target.value.toUpperCase() })}
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Họ Và Tên:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  value={editingReader ? editingReader.name : newReader.name}
                  onChange={e => editingReader ? setEditingReader({ ...editingReader, name: e.target.value }) : setNewReader({ ...newReader, name: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Email Nhận Biên Lai:</label>
                <input
                  type="email"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  value={editingReader ? editingReader.email : newReader.email}
                  onChange={e => editingReader ? setEditingReader({ ...editingReader, email: e.target.value }) : setNewReader({ ...newReader, email: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Mã Thẻ RFID (Thẻ Sinh Viên):</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: E2801192"
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', textTransform: 'uppercase' }}
                  value={editingReader ? editingReader.rfidCard : newReader.rfidCard}
                  onChange={e => editingReader ? setEditingReader({ ...editingReader, rfidCard: e.target.value.toUpperCase() }) : setNewReader({ ...newReader, rfidCard: e.target.value.toUpperCase() })}
                />
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button
                  type="submit"
                  style={{ flex: 1, background: '#991b1b', color: '#ffffff', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer' }}
                >
                  {editingReader ? 'Lưu Thay Đổi' : '➕ Lưu Độc Giả'}
                </button>
                {editingReader && (
                  <button
                    type="button"
                    style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '10px', borderRadius: '6px', fontWeight: '700', cursor: 'pointer' }}
                    onClick={() => setEditingReader(null)}
                  >
                    Hủy
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Danh sách độc giả */}
          <div style={{ background: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '800', marginBottom: '16px', color: '#0f172a' }}>Danh Sách Độc Giả</h3>
            <div style={{ maxHeight: '420px', overflowY: 'auto' }}>
              <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                    <th style={{ padding: '8px' }}>MSSV & Tên</th>
                    <th style={{ padding: '8px' }}>Mã Thẻ RFID</th>
                    <th style={{ padding: '8px' }}>Trạng Thái</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Hành Động</th>
                  </tr>
                </thead>
                <tbody>
                  {readers.map(r => (
                    <tr key={r._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '10px 8px' }}>
                        <div style={{ fontWeight: '700', color: '#0f172a' }}>{r.name}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>MSSV: {r.studentId} | {r.email}</div>
                      </td>
                      <td style={{ padding: '10px 8px' }}>
                        <code>{r.rfidCard}</code>
                      </td>
                      <td style={{ padding: '10px 8px' }}>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: '700',
                          background: r.active ? '#dcfce7' : '#fee2e2',
                          color: r.active ? '#15803d' : '#b91c1c'
                        }}>
                          {r.active ? 'Hoạt động' : 'Đã khóa thẻ'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                        <button
                          type="button"
                          style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '700', marginRight: '6px', cursor: 'pointer' }}
                          onClick={() => setEditingReader(r)}
                        >
                          Sửa
                        </button>
                        <button
                          type="button"
                          style={{
                            background: r.active ? '#fee2e2' : '#f0fdf4',
                            border: '1px solid',
                            borderColor: r.active ? '#fecaca' : '#bbf7d0',
                            color: r.active ? '#dc2626' : '#16a34a',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: '700',
                            cursor: 'pointer'
                          }}
                          onClick={() => handleToggleBlockReader(r)}
                        >
                          {r.active ? 'Khóa thẻ' : 'Mở khóa'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* TAB 5: LỊCH SỬ MƯỢN TRẢ & TRẢ THỦ CÔNG                    */}
      {/* ========================================================== */}
      {activeTab === 'LOANS' && (
        <div style={{ background: '#ffffff', padding: '24px', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a', margin: 0 }}>
                Lịch Sử Mượn Trả & Quản Lý Phiếu Mượn
              </h3>
              <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0' }}>
                Hỗ trợ xác nhận trả sách thủ công khi tem RFID bị hỏng và miễn/hủy phạt theo quy chế.
              </p>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#475569' }}>
                  <th style={{ padding: '10px' }}>Độc Giả</th>
                  <th style={{ padding: '10px' }}>Tài Liệu Mượn</th>
                  <th style={{ padding: '10px' }}>Ngày Mượn</th>
                  <th style={{ padding: '10px' }}>Hạn Trả</th>
                  <th style={{ padding: '10px' }}>Trạng Thái</th>
                  <th style={{ padding: '10px' }}>Tiền Phạt</th>
                  <th style={{ padding: '10px', textAlign: 'right' }}>Thao Tác</th>
                </tr>
              </thead>
              <tbody>
                {loans.map(loan => (
                  <tr key={loan._id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                    <td style={{ padding: '10px' }}>
                      <div style={{ fontWeight: '700', color: '#0f172a' }}>{loan.readerId?.name}</div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>MSSV: {loan.readerId?.studentId}</div>
                    </td>
                    <td style={{ padding: '10px' }}>
                      <div style={{ fontWeight: '600' }}>{loan.bookId?.title}</div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>RFID: <code>{loan.bookId?.rfidTag}</code></div>
                    </td>
                    <td style={{ padding: '10px', color: '#475569' }}>
                      {new Date(loan.borrowDate).toLocaleDateString('vi-VN')}
                    </td>
                    <td style={{ padding: '10px', color: '#475569' }}>
                      {new Date(loan.dueDate).toLocaleDateString('vi-VN')}
                    </td>
                    <td style={{ padding: '10px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '700',
                        background: loan.status === 'returned' ? '#dcfce7' : loan.status === 'overdue' ? '#fee2e2' : '#eff6ff',
                        color: loan.status === 'returned' ? '#15803d' : loan.status === 'overdue' ? '#b91c1c' : '#1d4ed8'
                      }}>
                        {loan.status === 'returned' ? 'Đã trả' : loan.status === 'overdue' ? 'Quá hạn' : 'Đang mượn'}
                      </span>
                    </td>
                    <td style={{ padding: '10px' }}>
                      {loan.fineAmount > 0 ? (
                        <span style={{ color: '#b91c1c', fontWeight: '700' }}>
                          {loan.fineAmount.toLocaleString('vi-VN')} đ ({loan.fineStatus === 'waived' ? 'Đã miễn' : loan.isPaid ? 'Đã trả' : 'Chưa nộp'})
                        </span>
                      ) : (
                        <span style={{ color: '#64748b' }}>-</span>
                      )}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>
                      {loan.status === 'borrowing' || loan.status === 'overdue' ? (
                        <button
                          type="button"
                          style={{ background: '#2563eb', color: '#ffffff', border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                          onClick={() => {
                            setManualReturnModal(loan);
                            setManualReturnReason('Nhãn RFID bị rách hoặc không đọc được');
                          }}
                        >
                          Trả thủ công
                        </button>
                      ) : loan.fineAmount > 0 && !loan.isPaid && loan.fineStatus !== 'waived' ? (
                        <button
                          type="button"
                          style={{ background: '#10b981', color: '#ffffff', border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                          onClick={() => handleWaiveFine(loan._id)}
                        >
                          Miễn phạt
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* TAB 6: NHẬT KÝ KIỂM TOÁN (AUDIT LOGS)                      */}
      {/* ========================================================== */}
      {activeTab === 'AUDIT' && (
        <div style={{ background: '#ffffff', padding: '24px', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a', marginBottom: '8px' }}>
            🛡️ Nhật Ký Thao Tác & Kiểm Toán (Audit Logs)
          </h3>
          <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
            Ghi nhận toàn bộ thao tác thủ thư: kiểm tra sách sau trả, tạo phạt hư hỏng, miễn phạt, khóa thẻ độc giả.
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                  <th style={{ padding: '10px' }}>Thời Gian</th>
                  <th style={{ padding: '10px' }}>Người Thực Hiện</th>
                  <th style={{ padding: '10px' }}>Hành Động</th>
                  <th style={{ padding: '10px' }}>Đối Tượng</th>
                  <th style={{ padding: '10px' }}>Chi Tiết Thao Tác</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map(audit => (
                  <tr key={audit._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '10px', color: '#64748b' }}>
                      {new Date(audit.timestamp).toLocaleString('vi-VN')}
                    </td>
                    <td style={{ padding: '10px', fontWeight: '700', color: '#1e293b' }}>
                      {audit.actor || 'Thủ thư'}
                    </td>
                    <td style={{ padding: '10px' }}>
                      <span style={{ padding: '3px 8px', borderRadius: '4px', fontWeight: '700', background: '#eff6ff', color: '#1d4ed8' }}>
                        {audit.action}
                      </span>
                    </td>
                    <td style={{ padding: '10px', color: '#64748b' }}>
                      {audit.targetType} (#{audit.targetId?.slice(-6)})
                    </td>
                    <td style={{ padding: '10px' }}>
                      <code>{JSON.stringify(audit.details || {})}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* MODAL KIỂM TRA SÁCH SAU KHI TRẢ (MỤC 5)                    */}
      {/* ========================================================== */}
      {inspectModalLoan && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{ background: '#ffffff', borderRadius: '16px', padding: '24px', maxWidth: '520px', width: '90%', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#991b1b', margin: 0, marginBottom: '6px' }}>
              Kiểm Tra Tình Trạng Vật Lý Sách Sau Trả
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
              Cuốn sách: <strong>{inspectModalLoan.bookId?.title}</strong> | Người trả: <strong>{inspectModalLoan.readerId?.name} ({inspectModalLoan.readerId?.studentId})</strong>
            </p>

            <form onSubmit={handleInspectSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Kết Quả Đánh Giá Thực Tế:</label>
                <select
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontWeight: '600' }}
                  value={inspectForm.result}
                  onChange={e => setInspectForm({ ...inspectForm, result: e.target.value })}
                >
                  <option value="normal">🟢 Bình thường - Đưa trở lại kho cho mượn tiếp (0đ)</option>
                  <option value="minor_damage">🟡 Hỏng nhẹ nhưng vẫn sử dụng được (Có thể phạt nhẹ)</option>
                  <option value="needs_repair">🟠 Cần sửa chữa - Chuyển sang bảo trì (maintenance)</option>
                  <option value="damaged">🔴 Hư hỏng nặng - Lập biên bản bồi thường (damaged)</option>
                  <option value="lost">❌ Báo mất sách - Bồi thường toàn bộ (lost)</option>
                </select>
              </div>

              {(inspectForm.result === 'minor_damage' || inspectForm.result === 'needs_repair' || inspectForm.result === 'damaged' || inspectForm.result === 'lost') && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div>
                      <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Loại Hư Hỏng:</label>
                      <select
                        style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                        value={inspectForm.damageType}
                        onChange={e => setInspectForm({ ...inspectForm, damageType: e.target.value })}
                      >
                        <option value="torn_cover">Rách bìa / Bìa gãy</option>
                        <option value="missing_pages">Mất / Rách trang sách</option>
                        <option value="writing">Viết / Vẽ bẩn vào sách</option>
                        <option value="water_damage">Ngấm nước / Ẩm mốc</option>
                        <option value="lost">Mất sách hoàn toàn</option>
                        <option value="other">Hư hỏng khác</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Tiền Phạt / Bồi Thường (VNĐ):</label>
                      <input
                        type="number"
                        step="5000"
                        placeholder="Ví dụ: 50000"
                        style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                        value={inspectForm.damageFine}
                        onChange={e => setInspectForm({ ...inspectForm, damageFine: e.target.value })}
                      />
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Mô Tả Chi Tiết Hư Hỏng:</label>
                    <textarea
                      rows={2}
                      placeholder="Mô tả cụ thể vết rách, trang bị mất để thông báo cho sinh viên..."
                      style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px', fontSize: '12px' }}
                      value={inspectForm.damageDescription}
                      onChange={e => setInspectForm({ ...inspectForm, damageDescription: e.target.value })}
                    />
                  </div>
                </>
              )}

              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Ghi Chú Của Thủ Thư:</label>
                <input
                  type="text"
                  placeholder="Ghi chú nội bộ..."
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                  value={inspectForm.inspectionNotes}
                  onChange={e => setInspectForm({ ...inspectForm, inspectionNotes: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                <button
                  type="submit"
                  style={{ flex: 1, background: '#991b1b', color: '#ffffff', border: 'none', padding: '10px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Xác Nhận Kết Quả Nghiệm Thu
                </button>
                <button
                  type="button"
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '10px 16px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                  onClick={() => setInspectModalLoan(null)}
                >
                  Đóng
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* MODAL TRẢ SÁCH THỦ CÔNG (MỤC 8)                            */}
      {/* ========================================================== */}
      {manualReturnModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{ background: '#ffffff', borderRadius: '16px', padding: '24px', maxWidth: '480px', width: '90%' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#1e293b', margin: 0, marginBottom: '6px' }}>
              Xác Nhận Trả Sách Thủ Công
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
              Sử dụng khi nhãn RFID trên sách bị rách hoặc đầu đọc Kiosk không nhận diện được.
            </p>

            <form onSubmit={handleManualReturnSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '13px' }}>
                <div>Tài liệu: <strong>{manualReturnModal.bookId?.title}</strong></div>
                <div>Độc giả: <strong>{manualReturnModal.readerId?.name} ({manualReturnModal.readerId?.studentId})</strong></div>
                <div>Hạn trả: {new Date(manualReturnModal.dueDate).toLocaleDateString('vi-VN')}</div>
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: '700', color: '#334155' }}>Lý Do Trả Thủ Công:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
                  value={manualReturnReason}
                  onChange={e => setManualReturnReason(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                <button
                  type="submit"
                  style={{ flex: 1, background: '#2563eb', color: '#ffffff', border: 'none', padding: '10px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Xác Nhận Trả Thủ Công
                </button>
                <button
                  type="button"
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '10px 16px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                  onClick={() => setManualReturnModal(null)}
                >
                  Hủy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
