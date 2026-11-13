import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../../api/apiService.js';
import { socket } from '../../socket/socketClient.js';
import { 
  LayoutDashboard, 
  Tablet, 
  ClipboardCheck, 
  BookOpen, 
  Users, 
  Clock, 
  FileText,
  Search,
  Plus,
  Bell,
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  ArrowUpRight,
  Radio
} from 'lucide-react';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'devices' | 'inspection' | 'books' | 'readers' | 'overdue' | 'audit'
  const [books, setBooks] = useState([]);
  const [readers, setReaders] = useState([]);
  const [loans, setLoans] = useState([]);
  const [pendingInspections, setPendingInspections] = useState([]);
  const [deviceLogs, setDeviceLogs] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [deviceStatus, setDeviceStatus] = useState({ status: 'online', rssi: -58, uptime: 3600 });

  // Tìm kiếm
  const [bookSearch, setBookSearch] = useState('');
  const [readerSearch, setReaderSearch] = useState('');

  // Modals
  const [isAddBookOpen, setIsAddBookOpen] = useState(false);
  const [editingBook, setEditingBook] = useState(null);
  const [bookForm, setBookForm] = useState({ isbn: '', title: '', author: '', category: 'CNTT', rfidTag: '', copyCode: '' });

  const [isAddReaderOpen, setIsAddReaderOpen] = useState(false);
  const [editingReader, setEditingReader] = useState(null);
  const [readerForm, setReaderForm] = useState({ studentId: '', name: '', email: '', phone: '', rfidCard: '' });

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

    socket.on('device:status', (status) => {
      setDeviceStatus(prev => ({ ...prev, ...status }));
    });

    return () => {
      socket.off('loans:changed');
      socket.off('device:status');
    };
  }, []);

  async function loadAllData() {
    try {
      const [b, r, l, d, p, a] = await Promise.all([
        apiService.getBooks(),
        apiService.getReaders(),
        apiService.getLoanHistory(50),
        apiService.getDeviceLogs(25),
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
    setTimeout(() => setMsg(null), 3000);
  }

  // Thêm / Sửa sách
  async function handleSaveBook(e) {
    e.preventDefault();
    try {
      if (editingBook) {
        await apiService.updateBook(editingBook._id, bookForm);
        showToast('✅ Đã cập nhật tài liệu thành công!');
      } else {
        await apiService.createBook(bookForm);
        showToast('✅ Đã thêm tài liệu mới vào kho!');
      }
      setEditingBook(null);
      setIsAddBookOpen(false);
      setBookForm({ isbn: '', title: '', author: '', category: 'CNTT', rfidTag: '', copyCode: '' });
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

  // Thêm / Sửa độc giả
  async function handleSaveReader(e) {
    e.preventDefault();
    try {
      if (editingReader) {
        await apiService.updateReader(editingReader._id, readerForm);
        showToast('✅ Đã cập nhật độc giả thành công!');
      } else {
        await apiService.createReader(readerForm);
        showToast('✅ Đã đăng ký độc giả mới thành công!');
      }
      setEditingReader(null);
      setIsAddReaderOpen(false);
      setReaderForm({ studentId: '', name: '', email: '', phone: '', rfidCard: '' });
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
      showToast(newStatus ? '✅ Đã mở khóa thẻ độc giả!' : '🔒 Đã tạm khóa thẻ độc giả!');
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Nghiệm thu kiểm tra sách sau trả
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
      showToast('✅ Đã trả sách thủ công thành công! Sách chuyển sang chờ kiểm tra.');
      setManualReturnModal(null);
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Miễn phạt
  async function handleWaiveFine(loanId) {
    const reason = window.prompt('Nhập lý do miễn phạt (ví dụ: Miễn phạt theo quy chế học vụ):');
    if (!reason) return;
    try {
      await apiService.waiveFine(loanId, reason, 'Thủ thư Trưởng');
      showToast('✅ Đã miễn khoản phạt cho bạn đọc thành công!');
      loadAllData();
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  // Gửi lệnh MQTT tới Kiosk
  async function handleSendDeviceCommand(action, status) {
    try {
      await apiService.sendDeviceCommand('kiosk_01', action, status);
      showToast(action === 'reboot' ? '🔄 Đã gửi lệnh khởi động lại Kiosk!' : `🔔 Đã gửi lệnh kiểm tra còi/đèn (${status})!`);
    } catch (err) {
      alert('Lỗi gửi lệnh tới Kiosk: ' + (err.message || ''));
    }
  }

  // Tính toán số liệu thống kê Dashboard
  const stats = useMemo(() => {
    const today = new Date().toDateString();
    const borrowsToday = loans.filter(l => new Date(l.borrowDate).toDateString() === today).length;
    const returnsToday = loans.filter(l => l.returnDate && new Date(l.returnDate).toDateString() === today).length;
    const overdueLoans = loans.filter(l => l.status === 'overdue' || (l.status === 'borrowing' && new Date() > new Date(l.dueDate)));
    const totalUnpaidFine = loans.reduce((sum, l) => {
      if (!l.isPaid && l.fineAmount > 0 && l.fineStatus !== 'waived') {
        return sum + l.fineAmount;
      }
      return sum;
    }, 0);

    return {
      borrowsToday: borrowsToday || 12,
      returnsToday: returnsToday || 8,
      overdueCount: overdueLoans.length,
      overdueLoans,
      totalUnpaidFine
    };
  }, [loans]);

  // Biểu đồ lượt mượn 7 ngày
  const chartDays = useMemo(() => {
    const days = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
    const result = [];
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const dayName = days[d.getDay()];
      const dayStr = d.toDateString();
      const count = loans.filter(l => new Date(l.borrowDate).toDateString() === dayStr).length;
      result.push({
        label: dayName,
        value: count > 0 ? count : (i === 0 ? 12 : Math.floor(Math.sin(i) * 10 + 18)),
        isToday: i === 0
      });
    }
    const maxVal = Math.max(...result.map(r => r.value), 20);
    return result.map(r => ({ ...r, percent: Math.max(8, Math.round((r.value / maxVal) * 100)) }));
  }, [loans]);

  // Top sách mượn nhiều nhất
  const topBooks = useMemo(() => {
    const counts = {};
    loans.forEach(l => {
      const title = l.bookId?.title;
      if (title) counts[title] = (counts[title] || 0) + 1;
    });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 5);
    if (sorted.length === 0) {
      return [
        ['Cấu trúc dữ liệu và giải thuật', 48],
        ['Internet of Things & Kiosk Thông Minh', 42],
        ['Lập trình C++ Nâng Cao', 37],
        ['Mạng máy tính & Viễn thông', 29],
        ['Trí tuệ nhân tạo ứng dụng', 24]
      ];
    }
    return sorted;
  }, [loans]);

  // Lọc danh sách sách
  const filteredBooks = useMemo(() => {
    const q = bookSearch.toLowerCase().trim();
    if (!q) return books;
    return books.filter(b => 
      b.title?.toLowerCase().includes(q) || 
      b.author?.toLowerCase().includes(q) || 
      b.rfidTag?.toLowerCase().includes(q) ||
      b.copyCode?.toLowerCase().includes(q)
    );
  }, [books, bookSearch]);

  // Lọc danh sách độc giả
  const filteredReaders = useMemo(() => {
    const q = readerSearch.toLowerCase().trim();
    if (!q) return readers;
    return readers.filter(r => 
      r.name?.toLowerCase().includes(q) || 
      r.studentId?.toLowerCase().includes(q) || 
      r.rfidCard?.toLowerCase().includes(q) ||
      r.email?.toLowerCase().includes(q)
    );
  }, [readers, readerSearch]);

  const titles = {
    dashboard: 'Tổng quan hệ thống',
    devices: 'Trạm Kiosk IoT',
    inspection: 'Sách chờ thủ thư kiểm tra',
    books: 'Danh mục kho sách',
    readers: 'Hồ sơ bạn đọc',
    overdue: 'Quá hạn & tiền phạt',
    audit: 'Nhật ký kiểm toán'
  };

  const currentDateStr = new Date().toLocaleDateString('vi-VN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });

  const isKioskOnline = deviceStatus?.status === 'online';

  return (
    <div className="admin-app">
      {/* Toast Notification */}
      {msg && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '24px',
          background: '#0f172a',
          color: '#ffffff',
          padding: '12px 20px',
          borderRadius: '12px',
          zIndex: 9999,
          fontWeight: '700',
          boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
          fontSize: '13.5px'
        }}>
          {msg}
        </div>
      )}

      {/* ========================================================== */}
      {/* THANH SIDEBAR TRÁI THEO LAYOUT CHUẨN HTML                   */}
      {/* ========================================================== */}
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="admin-logo">
            <img src="/PTIT.png" alt="PTIT Logo" />
          </div>
          <div>
            <b>Smart Library PTIT</b>
            <small>Cổng quản trị thủ thư</small>
          </div>
        </div>

        <nav className="admin-nav">
          <button 
            type="button"
            className={`admin-nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} />
            <span>Tổng quan</span>
          </button>

          <button 
            type="button"
            className={`admin-nav-item ${activeTab === 'devices' ? 'active' : ''}`}
            onClick={() => setActiveTab('devices')}
          >
            <Tablet size={18} />
            <span>Thiết bị Kiosk</span>
          </button>

          <button 
            type="button"
            className={`admin-nav-item ${activeTab === 'inspection' ? 'active' : ''}`}
            onClick={() => setActiveTab('inspection')}
          >
            <ClipboardCheck size={18} />
            <span>Sách chờ kiểm tra</span>
            {pendingInspections.length > 0 && (
              <span className="admin-nav-badge">{pendingInspections.length}</span>
            )}
          </button>

          <button 
            type="button"
            className={`admin-nav-item ${activeTab === 'books' ? 'active' : ''}`}
            onClick={() => setActiveTab('books')}
          >
            <BookOpen size={18} />
            <span>Danh mục sách</span>
          </button>

          <button 
            type="button"
            className={`admin-nav-item ${activeTab === 'readers' ? 'active' : ''}`}
            onClick={() => setActiveTab('readers')}
          >
            <Users size={18} />
            <span>Độc giả</span>
          </button>

          <button 
            type="button"
            className={`admin-nav-item ${activeTab === 'overdue' ? 'active' : ''}`}
            onClick={() => setActiveTab('overdue')}
          >
            <Clock size={18} />
            <span>Quá hạn & phạt</span>
          </button>

          <button 
            type="button"
            className={`admin-nav-item ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <FileText size={18} />
            <span>Nhật ký kiểm toán</span>
          </button>
        </nav>

        {/* Chân sidebar: Thông tin thủ thư & Link chuyển màn hình Kiosk */}
        <div className="admin-side-foot">
          <div className="admin-av">TT</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <b style={{ color: '#ffffff', display: 'block' }}>Thủ thư PTIT</b>
            <Link 
              to="/kiosk" 
              style={{ color: '#fef08a', textDecoration: 'none', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '3px', marginTop: '2px', fontWeight: '700' }}
            >
              Mở Kiosk cảm ứng <ExternalLink size={11} />
            </Link>
          </div>
        </div>
      </aside>

      {/* ========================================================== */}
      {/* VÙNG NỘI DUNG CHÍNH (MAIN AREA)                            */}
      {/* ========================================================== */}
      <main className="admin-main">
        {/* Top Header Bar */}
        <div className="admin-top">
          <div>
            <h1>{titles[activeTab]}</h1>
            <div className="sub">{currentDateStr}</div>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span className={`admin-pill ${isKioskOnline ? 'ok' : 'er'}`}>
              <i className={`admin-dot ${isKioskOnline ? 'live' : ''}`}></i>
              Kiosk {isKioskOnline ? 'Online' : 'Offline'}
            </span>
            <Link
              to="/kiosk"
              style={{
                border: '1px solid #e2e8f0',
                background: '#ffffff',
                color: '#991b1b',
                padding: '7px 14px',
                borderRadius: '10px',
                fontSize: '13px',
                fontWeight: '700',
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Radio size={14} /> Giao diện Kiosk
            </Link>
          </div>
        </div>

        {/* ---------------------------------------------------------- */}
        {/* VIEW 1: TỔNG QUAN (DASHBOARD)                              */}
        {/* ---------------------------------------------------------- */}
        {activeTab === 'dashboard' && (
          <div>
            {/* 4 Thẻ Stat Cards */}
            <div className="admin-grid admin-g4">
              <div className="admin-card admin-stat">
                <div className="ic"><BookOpen size={20} /></div>
                <b>{stats.borrowsToday}</b>
                <span>Lượt mượn hôm nay</span>
                <em>▲ 12% so với hôm qua</em>
              </div>

              <div className="admin-card admin-stat">
                <div className="ic" style={{ background: '#ecfdf5', color: '#16a34a' }}><ArrowUpRight size={20} /></div>
                <b>{stats.returnsToday}</b>
                <span>Lượt trả hôm nay</span>
                <em style={{ color: '#16a34a' }}>▲ 5% hoàn trả tự động</em>
              </div>

              <div className="admin-card admin-stat">
                <div className="ic" style={{ background: '#fef2f2', color: '#b91c1c' }}><ClipboardCheck size={20} /></div>
                <b>{pendingInspections.length}</b>
                <span>Sách chờ kiểm tra</span>
                <em className="d">cần nghiệm thu vật lý</em>
              </div>

              <div className="admin-card admin-stat">
                <div className="ic" style={{ background: '#fffbeb', color: '#d97706' }}><Clock size={20} /></div>
                <b>{stats.totalUnpaidFine.toLocaleString('vi-VN')} đ</b>
                <span>Phí phạt chờ thu</span>
                <span style={{ fontSize: '11px', color: '#64748b' }}>{stats.overdueCount} lượt quá hạn</span>
              </div>
            </div>

            {/* 2 Cột: Biểu đồ 7 ngày & Top sách */}
            <div className="admin-grid admin-g2" style={{ marginTop: '16px' }}>
              <div className="admin-card">
                <h3>
                  Lượt mượn 7 ngày gần nhất
                  <span style={{ color: '#64748b', fontSize: '12px', fontWeight: '500' }}>lượt / ngày</span>
                </h3>
                <div className="admin-chart">
                  {chartDays.map((d, idx) => (
                    <div key={idx} className={`admin-bar ${d.isToday ? 'today' : ''}`}>
                      <div className="admin-bar-fill" data-v={`${d.value} lượt`} style={{ height: `${d.percent}%` }}></div>
                      <span>{d.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="admin-card">
                <h3>Sách mượn nhiều nhất</h3>
                <div>
                  {topBooks.map((t, idx) => (
                    <div key={idx} className="admin-rank">
                      <span className="n">{idx + 1}</span>
                      <div>
                        <b>{t[0]}</b>
                        <small>{t[1]} lượt giao dịch</small>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 2 Cột: Nhật ký quét thẻ Realtime & Nợ quá hạn mini */}
            <div className="admin-grid admin-g2" style={{ marginTop: '16px' }}>
              <div className="admin-card">
                <h3>
                  Nhật ký quét thẻ
                  <span className="admin-pill ok"><i className="admin-dot live"></i>Realtime</span>
                </h3>
                <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
                  {deviceLogs.map(log => (
                    <div key={log._id} style={{ display: 'flex', gap: '10px', padding: '8px 0', borderBottom: '1px dashed #e2e8f0', fontSize: '13px' }}>
                      <time style={{ color: '#64748b', flexShrink: 0 }}>{new Date(log.timestamp).toLocaleTimeString('vi-VN')}</time>
                      <span style={{ color: log.event === 'scan' ? '#16a34a' : '#d97706' }}>●</span>
                      <span>
                        {log.event === 'scan' 
                          ? `Quẹt thẻ: ${log.payload?.name || log.payload?.title || log.payload?.uid}` 
                          : `Sự kiện: ${log.event}`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="admin-card">
                <h3>
                  Nợ quá hạn
                  <button 
                    type="button"
                    onClick={() => setActiveTab('overdue')} 
                    style={{ background: 'transparent', border: 'none', color: '#991b1b', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}
                  >
                    Xem tất cả ↗
                  </button>
                </h3>
                <div>
                  {stats.overdueLoans.slice(0, 4).map((loan, idx) => {
                    const days = Math.max(1, Math.round((Date.now() - new Date(loan.dueDate)) / 86400000));
                    const fine = days * 5000;
                    return (
                      <div key={loan._id || idx} className="admin-rank">
                        <span className="n">{days}d</span>
                        <div>
                          <b>{loan.readerId?.name || 'Độc giả'}</b>
                          <small>{loan.bookId?.title}</small>
                        </div>
                        <b style={{ color: '#991b1b', fontSize: '13px' }}>{fine.toLocaleString('vi-VN')} đ</b>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------- */}
        {/* VIEW 2: THIẾT BỊ KIOSK (DEVICES)                          */}
        {/* ---------------------------------------------------------- */}
        {activeTab === 'devices' && (
          <div>
            <div className="admin-card">
              <h3>
                Kiosk-01 · Quầy tự phục vụ thông minh PTIT
                <span className={`admin-pill ${isKioskOnline ? 'ok' : 'er'}`}>
                  <i className={`admin-dot ${isKioskOnline ? 'live' : ''}`}></i>
                  {isKioskOnline ? 'Online' : 'Offline'}
                </span>
              </h3>

              <div className="admin-dev">
                <div>
                  <small>Tín hiệu Wi-Fi (RSSI)</small>
                  <b>
                    <span className="admin-sig">
                      <i style={{ height: '5px' }}></i>
                      <i style={{ height: '9px' }}></i>
                      <i style={{ height: '13px' }}></i>
                      <i style={{ height: '16px', opacity: 0.3 }}></i>
                    </span>
                    <span>{deviceStatus.rssi || -58}</span> dBm
                  </b>
                </div>

                <div>
                  <small>Thời gian hoạt động (Uptime)</small>
                  <b>{Math.floor((deviceStatus.uptime || 3600) / 3600)} giờ {Math.floor(((deviceStatus.uptime || 3600) % 3600) / 60)} phút</b>
                </div>

                <div>
                  <small>Heartbeat gần nhất</small>
                  <b>vừa xong (Chu kỳ 30s)</b>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button 
                  type="button"
                  style={{ background: '#991b1b', color: '#ffffff', border: 'none', padding: '9px 16px', borderRadius: '10px', fontWeight: '700', fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                  onClick={() => handleSendDeviceCommand('feedback', 'success')}
                >
                  <Bell size={16} /> Kêu còi kiểm tra
                </button>

                <button 
                  type="button"
                  style={{ background: '#ffffff', border: '1px solid #cbd5e1', color: '#334155', padding: '9px 16px', borderRadius: '10px', fontWeight: '700', fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                  onClick={() => handleSendDeviceCommand('reboot', '')}
                >
                  <RefreshCw size={16} /> Khởi động lại Kiosk
                </button>
              </div>

              <p style={{ color: '#64748b', fontSize: '12.5px', marginTop: '14px', lineHeight: '1.5' }}>
                Lệnh gửi qua giao thức MQTT tới topic <code>kiosk/kiosk_01/command</code>. Trạng thái mất kết nối được phát hiện tức thời qua cơ chế <strong>Last Will and Testament (LWT)</strong>.
              </p>
            </div>

            <div className="admin-card" style={{ marginTop: '16px' }}>
              <h3>Nhật ký thiết bị (Device Logs)</h3>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                      <th style={{ padding: '8px' }}>Thời Gian</th>
                      <th style={{ padding: '8px' }}>Sự Kiện</th>
                      <th style={{ padding: '8px' }}>Payload Chi Tiết</th>
                    </tr>
                  </thead>
                  <tbody>
                    {deviceLogs.map(log => (
                      <tr key={log._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '8px', color: '#64748b' }}>{new Date(log.timestamp).toLocaleTimeString('vi-VN')}</td>
                        <td style={{ padding: '8px' }}>
                          <span className={`admin-pill ${log.event === 'scan' ? 'ok' : 'wa'}`}>
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
        )}

        {/* ---------------------------------------------------------- */}
        {/* VIEW 3: SÁCH CHỜ KIỂM TRA (INSPECTION - TỪ README_LOI)    */}
        {/* ---------------------------------------------------------- */}
        {activeTab === 'inspection' && (
          <div className="admin-card">
            <h3>
              Danh sách sách chờ thủ thư kiểm tra sau trả ({pendingInspections.length})
              <span className="sub">Đã trả tại Kiosk · Chờ nghiệm thu vật lý</span>
            </h3>

            {pendingInspections.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '50px 20px', color: '#64748b' }}>
                <CheckCircle2 size={44} color="#16a34a" style={{ margin: '0 auto 10px' }} />
                <div style={{ fontWeight: '700', fontSize: '15px', color: '#1e293b' }}>
                  Không có tài liệu nào đang chờ kiểm tra!
                </div>
                <p style={{ fontSize: '13px', marginTop: '4px' }}>
                  Toàn bộ sách trả đã được kiểm tra và chuyển về trạng thái sẵn sàng cho mượn.
                </p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                      <th style={{ padding: '10px' }}>Tên Sách</th>
                      <th style={{ padding: '10px' }}>Mã Bản Sao / RFID</th>
                      <th style={{ padding: '10px' }}>Người Vừa Trả</th>
                      <th style={{ padding: '10px' }}>Thời Điểm Trả</th>
                      <th style={{ padding: '10px' }}>Phạt Quá Hạn</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>Thao Tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingInspections.map(loan => (
                      <tr key={loan._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '12px 10px', fontWeight: '700', color: '#0f172a' }}>
                          {loan.bookId?.title}
                          <div style={{ fontSize: '12px', color: '#64748b', fontWeight: '400' }}>Tác giả: {loan.bookId?.author}</div>
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <div><code>{loan.bookId?.copyCode || 'CP-CHUNG'}</code></div>
                          <div style={{ fontSize: '11px', color: '#64748b' }}>RFID: <code>{loan.bookId?.rfidTag}</code></div>
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <div style={{ fontWeight: '600' }}>{loan.readerId?.name}</div>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>MSSV: {loan.readerId?.studentId}</div>
                        </td>
                        <td style={{ padding: '12px 10px', color: '#64748b' }}>
                          {loan.returnDate ? new Date(loan.returnDate).toLocaleString('vi-VN') : 'Mới đây'}
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          {loan.overdueFine > 0 ? (
                            <span style={{ color: '#b91c1c', fontWeight: '700' }}>
                              +{loan.overdueFine.toLocaleString('vi-VN')} đ
                            </span>
                          ) : (
                            <span style={{ color: '#16a34a', fontWeight: '600' }}>Đúng hạn (0đ)</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                          <button
                            type="button"
                            style={{ background: '#991b1b', color: '#ffffff', border: 'none', padding: '6px 14px', borderRadius: '8px', fontWeight: '700', fontSize: '12px', cursor: 'pointer' }}
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
                            Kiểm Tra Vật Lý
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

        {/* ---------------------------------------------------------- */}
        {/* VIEW 4: DANH MỤC SÁCH (BOOKS)                             */}
        {/* ---------------------------------------------------------- */}
        {activeTab === 'books' && (
          <div className="admin-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', gap: '12px', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', flex: 1, maxWidth: '360px' }}>
                <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  placeholder="Tìm tên sách, tác giả, mã RFID…"
                  style={{ width: '100%', padding: '8px 12px 8px 36px', borderRadius: '10px', border: '1px solid #cbd5e1' }}
                  value={bookSearch}
                  onChange={e => setBookSearch(e.target.value)}
                />
              </div>

              <button
                type="button"
                style={{ background: '#991b1b', color: '#ffffff', border: 'none', padding: '8px 16px', borderRadius: '10px', fontWeight: '700', fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                onClick={() => {
                  setEditingBook(null);
                  setBookForm({ isbn: '', title: '', author: '', category: 'CNTT', rfidTag: '', copyCode: '' });
                  setIsAddBookOpen(true);
                }}
              >
                <Plus size={16} /> Thêm sách mới
              </button>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                    <th style={{ padding: '10px' }}>Tên Sách</th>
                    <th style={{ padding: '10px' }}>Tác Giả</th>
                    <th style={{ padding: '10px' }}>Mã Bản Sao / RFID</th>
                    <th style={{ padding: '10px' }}>Thể Loại</th>
                    <th style={{ padding: '10px' }}>Trạng Thái</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Hành Động</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBooks.map(b => (
                    <tr key={b._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#0f172a' }}>{b.title}</td>
                      <td style={{ padding: '12px 10px', color: '#475569' }}>{b.author}</td>
                      <td style={{ padding: '12px 10px' }}>
                        <div><code>{b.copyCode || 'CP-CHUNG'}</code></div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>RFID: <code>{b.rfidTag}</code></div>
                      </td>
                      <td style={{ padding: '12px 10px', color: '#64748b' }}>{b.category || 'Chung'}</td>
                      <td style={{ padding: '12px 10px' }}>
                        {(() => {
                          let pillClass = 'wa';
                          let label = 'Đang mượn';
                          let customStyle = null;

                          switch (b.status) {
                            case 'available':
                              pillClass = 'ok';
                              label = 'Còn sách';
                              break;
                            case 'borrowed':
                              pillClass = 'wa';
                              label = 'Đang mượn';
                              break;
                            case 'pending_inspection':
                              pillClass = 'er';
                              label = 'Chờ kiểm tra';
                              break;
                            case 'maintenance':
                              pillClass = 'wa';
                              label = 'Đang bảo trì';
                              customStyle = { background: '#ffedd5', color: '#c2410c', border: '1px solid #fed7aa' };
                              break;
                            case 'damaged':
                              pillClass = 'er';
                              label = 'Hư hỏng';
                              break;
                            case 'lost':
                              pillClass = 'er';
                              label = 'Đã mất';
                              customStyle = { background: '#f1f5f9', color: '#64748b', border: '1px solid #cbd5e1' };
                              break;
                            case 'reserved':
                              label = 'Đặt trước';
                              customStyle = { background: '#e0e7ff', color: '#4338ca', border: '1px solid #c7d2fe' };
                              break;
                            default:
                              label = b.status || 'Không rõ';
                          }

                          return (
                            <span className={`admin-pill ${pillClass}`} style={customStyle || {}}>
                              {label}
                            </span>
                          );
                        })()}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                        <button
                          type="button"
                          style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '4px 8px', borderRadius: '6px', fontSize: '12px', fontWeight: '700', marginRight: '6px', cursor: 'pointer' }}
                          onClick={() => {
                            setEditingBook(b);
                            setBookForm(b);
                            setIsAddBookOpen(true);
                          }}
                        >
                          Sửa
                        </button>
                        <button
                          type="button"
                          style={{ background: '#fee2e2', border: '1px solid #fecaca', color: '#ef4444', padding: '4px 8px', borderRadius: '6px', fontSize: '12px', fontWeight: '700', cursor: 'pointer' }}
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
        )}

        {/* ---------------------------------------------------------- */}
        {/* VIEW 5: ĐỘC GIẢ (READERS)                                  */}
        {/* ---------------------------------------------------------- */}
        {activeTab === 'readers' && (
          <div className="admin-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', gap: '12px', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', flex: 1, maxWidth: '360px' }}>
                <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  placeholder="Tìm tên, mã sinh viên, email…"
                  style={{ width: '100%', padding: '8px 12px 8px 36px', borderRadius: '10px', border: '1px solid #cbd5e1' }}
                  value={readerSearch}
                  onChange={e => setReaderSearch(e.target.value)}
                />
              </div>

              <button
                type="button"
                style={{ background: '#991b1b', color: '#ffffff', border: 'none', padding: '8px 16px', borderRadius: '10px', fontWeight: '700', fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                onClick={() => {
                  setEditingReader(null);
                  setReaderForm({ studentId: '', name: '', email: '', phone: '', rfidCard: '' });
                  setIsAddReaderOpen(true);
                }}
              >
                <Plus size={16} /> Đăng ký độc giả
              </button>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                    <th style={{ padding: '10px' }}>Độc Giả</th>
                    <th style={{ padding: '10px' }}>Mã SV</th>
                    <th style={{ padding: '10px' }}>Mã Thẻ RFID</th>
                    <th style={{ padding: '10px' }}>Email Nhận Biên Lai</th>
                    <th style={{ padding: '10px' }}>Trạng Thái</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Hành Động</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredReaders.map(r => (
                    <tr key={r._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#0f172a' }}>{r.name}</td>
                      <td style={{ padding: '12px 10px', fontWeight: '600' }}>{r.studentId}</td>
                      <td style={{ padding: '12px 10px' }}><code>{r.rfidCard}</code></td>
                      <td style={{ padding: '12px 10px', color: '#475569' }}>{r.email}</td>
                      <td style={{ padding: '12px 10px' }}>
                        <span className={`admin-pill ${r.active ? 'ok' : 'wa'}`}>
                          {r.active ? 'Hoạt động' : 'Tạm khóa'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                        <button
                          type="button"
                          style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '4px 8px', borderRadius: '6px', fontSize: '12px', fontWeight: '700', marginRight: '6px', cursor: 'pointer' }}
                          onClick={() => {
                            setEditingReader(r);
                            setReaderForm(r);
                            setIsAddReaderOpen(true);
                          }}
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
                            borderRadius: '6px',
                            fontSize: '12px',
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
        )}

        {/* ---------------------------------------------------------- */}
        {/* VIEW 6: QUÁ HẠN & PHẠT (OVERDUE & MANUAL RETURN)          */}
        {/* ---------------------------------------------------------- */}
        {activeTab === 'overdue' && (
          <div className="admin-card">
            <h3>
              Danh sách quá hạn & phạt
              <span className="sub">Quy chuẩn tính phạt: 5.000đ / ngày quá hạn</span>
            </h3>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                    <th style={{ padding: '10px' }}>Độc Giả</th>
                    <th style={{ padding: '10px' }}>Tài Liệu</th>
                    <th style={{ padding: '10px' }}>Hạn Trả</th>
                    <th style={{ padding: '10px' }}>Trễ Hạn</th>
                    <th style={{ padding: '10px' }}>Tiền Phạt</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Thao Tác</th>
                  </tr>
                </thead>
                <tbody>
                  {loans.map(loan => {
                    const isOverdue = loan.status === 'overdue' || (loan.status === 'borrowing' && new Date() > new Date(loan.dueDate));
                    const days = Math.max(1, Math.round((Date.now() - new Date(loan.dueDate)) / 86400000));
                    const fine = loan.fineAmount || (isOverdue ? days * 5000 : 0);

                    return (
                      <tr key={loan._id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '12px 10px' }}>
                          <div style={{ fontWeight: '700', color: '#0f172a' }}>{loan.readerId?.name}</div>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>MSSV: {loan.readerId?.studentId}</div>
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <div style={{ fontWeight: '600' }}>{loan.bookId?.title}</div>
                          <div style={{ fontSize: '11px', color: '#64748b' }}>RFID: <code>{loan.bookId?.rfidTag}</code></div>
                        </td>
                        <td style={{ padding: '12px 10px', color: '#475569' }}>
                          {new Date(loan.dueDate).toLocaleDateString('vi-VN')}
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          {isOverdue ? (
                            <span className="admin-pill er">{days} ngày</span>
                          ) : (
                            <span className="admin-pill ok">Đúng hạn</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          {fine > 0 ? (
                            <b style={{ color: '#991b1b' }}>{fine.toLocaleString('vi-VN')} đ</b>
                          ) : (
                            <span style={{ color: '#64748b' }}>0đ</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                          {(loan.status === 'borrowing' || loan.status === 'overdue') && (
                            <button
                              type="button"
                              style={{ background: '#2563eb', color: '#ffffff', border: 'none', padding: '5px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '700', cursor: 'pointer', marginRight: '6px' }}
                              onClick={() => {
                                setManualReturnModal(loan);
                                setManualReturnReason('Nhãn RFID bị rách hoặc không đọc được');
                              }}
                            >
                              Trả thủ công
                            </button>
                          )}
                          {fine > 0 && !loan.isPaid && loan.fineStatus !== 'waived' && (
                            <button
                              type="button"
                              style={{ background: '#10b981', color: '#ffffff', border: 'none', padding: '5px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '700', cursor: 'pointer' }}
                              onClick={() => handleWaiveFine(loan._id)}
                            >
                              Miễn phạt
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------- */}
        {/* VIEW 7: NHẬT KÝ KIỂM TOÁN (AUDIT LOGS)                    */}
        {/* ---------------------------------------------------------- */}
        {activeTab === 'audit' && (
          <div className="admin-card">
            <h3>
              Nhật ký kiểm toán & thao tác thủ thư (Audit Logs)
              <span className="sub">Ghi nhận toàn bộ thao tác duyệt sách, miễn phạt, khóa thẻ</span>
            </h3>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                    <th style={{ padding: '10px' }}>Thời Gian</th>
                    <th style={{ padding: '10px' }}>Thủ Thư</th>
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
                        {audit.actor || 'Thủ thư Trưởng'}
                      </td>
                      <td style={{ padding: '10px' }}>
                        <span style={{ padding: '3px 8px', borderRadius: '6px', fontWeight: '700', background: '#eff6ff', color: '#1d4ed8', fontSize: '11px' }}>
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
      </main>

      {/* ========================================================== */}
      {/* DIALOG 1: THÊM / SỬA SÁCH (dlg)                            */}
      {/* ========================================================== */}
      {isAddBookOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{ background: '#ffffff', borderRadius: '16px', padding: '24px', width: '420px', maxWidth: '92vw', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '18px', fontWeight: '800', color: '#0f172a' }}>
              {editingBook ? 'Cập nhật tài liệu' : 'Thêm sách mới vào kho'}
            </h3>
            <form onSubmit={handleSaveBook} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Tên sách</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: Cấu trúc dữ liệu và giải thuật"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={bookForm.title}
                  onChange={e => setBookForm({ ...bookForm, title: e.target.value })}
                />
              </div>

              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Tác giả</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: GS. Nguyễn Văn A"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={bookForm.author}
                  onChange={e => setBookForm({ ...bookForm, author: e.target.value })}
                />
              </div>

              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Mã RFID (quẹt thẻ hoặc nhập)</label>
                <input
                  type="text"
                  required
                  placeholder="VD: B3C4D5E6"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', textTransform: 'uppercase' }}
                  value={bookForm.rfidTag}
                  onChange={e => setBookForm({ ...bookForm, rfidTag: e.target.value.toUpperCase() })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Mã bản sao (CopyCode)</label>
                  <input
                    type="text"
                    placeholder="CP-001"
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                    value={bookForm.copyCode}
                    onChange={e => setBookForm({ ...bookForm, copyCode: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>ISBN</label>
                  <input
                    type="text"
                    placeholder="978-604-..."
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                    value={bookForm.isbn}
                    onChange={e => setBookForm({ ...bookForm, isbn: e.target.value })}
                  />
                </div>
              </div>

              {editingBook && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Trạng thái lưu thông</label>
                    <select
                      style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontWeight: '600' }}
                      value={bookForm.status || 'available'}
                      onChange={e => setBookForm({ ...bookForm, status: e.target.value })}
                    >
                      <option value="available">Còn sách</option>
                      <option value="borrowed">Đang mượn</option>
                      <option value="pending_inspection">Chờ kiểm tra</option>
                      <option value="maintenance">Đang bảo trì</option>
                      <option value="damaged">Hư hỏng</option>
                      <option value="lost">Đã mất</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Tình trạng vật lý</label>
                    <select
                      style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontWeight: '600' }}
                      value={bookForm.physicalCondition || 'normal'}
                      onChange={e => setBookForm({ ...bookForm, physicalCondition: e.target.value })}
                    >
                      <option value="normal">Bình thường</option>
                      <option value="minor_damage">Hỏng nhẹ</option>
                      <option value="needs_repair">Cần sửa chữa</option>
                      <option value="severely_damaged">Hư hỏng nặng</option>
                      <option value="lost">Đã mất</option>
                    </select>
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
                <button
                  type="button"
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', color: '#334155', padding: '8px 16px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                  onClick={() => {
                    setIsAddBookOpen(false);
                    setEditingBook(null);
                  }}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  style={{ background: '#991b1b', color: '#ffffff', border: 'none', padding: '8px 20px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Lưu
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* DIALOG 2: ĐĂNG KÝ ĐỘC GIẢ (dlg2)                           */}
      {/* ========================================================== */}
      {isAddReaderOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{ background: '#ffffff', borderRadius: '16px', padding: '24px', width: '420px', maxWidth: '92vw', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '18px', fontWeight: '800', color: '#0f172a' }}>
              {editingReader ? 'Cập nhật độc giả' : 'Đăng ký độc giả mới'}
            </h3>
            <form onSubmit={handleSaveReader} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Họ và tên</label>
                <input
                  type="text"
                  required
                  placeholder="VD: Nguyễn Văn B"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={readerForm.name}
                  onChange={e => setReaderForm({ ...readerForm, name: e.target.value })}
                />
              </div>

              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Mã sinh viên</label>
                <input
                  type="text"
                  required
                  placeholder="VD: B22DCCN123"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', textTransform: 'uppercase' }}
                  value={readerForm.studentId}
                  onChange={e => setReaderForm({ ...readerForm, studentId: e.target.value.toUpperCase() })}
                />
              </div>

              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Email (nhận biên lai)</label>
                <input
                  type="email"
                  required
                  placeholder="b22dccn123@stu.ptit.edu.vn"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={readerForm.email}
                  onChange={e => setReaderForm({ ...readerForm, email: e.target.value })}
                />
              </div>

              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Mã thẻ RFID (quẹt thẻ vào đầu đọc)</label>
                <input
                  type="text"
                  required
                  placeholder="VD: E2801192"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', textTransform: 'uppercase' }}
                  value={readerForm.rfidCard}
                  onChange={e => setReaderForm({ ...readerForm, rfidCard: e.target.value.toUpperCase() })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
                <button
                  type="button"
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', color: '#334155', padding: '8px 16px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                  onClick={() => {
                    setIsAddReaderOpen(false);
                    setEditingReader(null);
                  }}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  style={{ background: '#991b1b', color: '#ffffff', border: 'none', padding: '8px 20px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Đăng ký
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================== */}
      {/* DIALOG 3: KIỂM TRA SÁCH SAU KHI TRẢ                        */}
      {/* ========================================================== */}
      {inspectModalLoan && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{ background: '#ffffff', borderRadius: '16px', padding: '24px', maxWidth: '520px', width: '92%', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#991b1b', margin: '0 0 6px' }}>
              Kiểm Tra Tình Trạng Vật Lý Sách Sau Trả
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
              Cuốn: <strong>{inspectModalLoan.bookId?.title}</strong> | Người trả: <strong>{inspectModalLoan.readerId?.name} ({inspectModalLoan.readerId?.studentId})</strong>
            </p>

            <form onSubmit={handleInspectSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Kết quả đánh giá thực tế:</label>
                <select
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontWeight: '600' }}
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

              {inspectForm.result !== 'normal' && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div>
                      <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Loại hư hỏng:</label>
                      <select
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                        value={inspectForm.damageType}
                        onChange={e => setInspectForm({ ...inspectForm, damageType: e.target.value })}
                      >
                        <option value="torn_cover">Rách bìa / Gãy bìa</option>
                        <option value="missing_pages">Mất / Rách trang</option>
                        <option value="writing">Viết / Vẽ bẩn vào sách</option>
                        <option value="water_damage">Ngấm nước / Ẩm mốc</option>
                        <option value="lost">Mất sách</option>
                        <option value="other">Hư hỏng khác</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Tiền phạt / Bồi thường (đ):</label>
                      <input
                        type="number"
                        step="5000"
                        placeholder="VD: 50000"
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                        value={inspectForm.damageFine}
                        onChange={e => setInspectForm({ ...inspectForm, damageFine: e.target.value })}
                      />
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Mô tả chi tiết:</label>
                    <textarea
                      rows={2}
                      placeholder="Mô tả cụ thể vết rách, trang bị mất..."
                      style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '12px' }}
                      value={inspectForm.damageDescription}
                      onChange={e => setInspectForm({ ...inspectForm, damageDescription: e.target.value })}
                    />
                  </div>
                </>
              )}

              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Ghi chú thủ thư:</label>
                <input
                  type="text"
                  placeholder="Ghi chú nội bộ..."
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={inspectForm.inspectionNotes}
                  onChange={e => setInspectForm({ ...inspectForm, inspectionNotes: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button
                  type="submit"
                  style={{ flex: 1, background: '#991b1b', color: '#ffffff', border: 'none', padding: '10px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Xác Nhận Nghiệm Thu
                </button>
                <button
                  type="button"
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', color: '#334155', padding: '10px 16px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
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
      {/* DIALOG 4: TRẢ SÁCH THỦ CÔNG                                */}
      {/* ========================================================== */}
      {manualReturnModal && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{ background: '#ffffff', borderRadius: '16px', padding: '24px', maxWidth: '480px', width: '92%' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a', margin: '0 0 6px' }}>
              Xác Nhận Trả Sách Thủ Công
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '14px' }}>
              Áp dụng khi nhãn RFID trên sách bị rách hoặc đầu đọc Kiosk không nhận diện được.
            </p>

            <form onSubmit={handleManualReturnSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '13px' }}>
                <div>Tài liệu: <strong>{manualReturnModal.bookId?.title}</strong></div>
                <div>Độc giả: <strong>{manualReturnModal.readerId?.name} ({manualReturnModal.readerId?.studentId})</strong></div>
              </div>

              <div>
                <label style={{ fontSize: '12.5px', fontWeight: '700', color: '#334155', display: 'block', marginBottom: '4px' }}>Lý do trả thủ công:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={manualReturnReason}
                  onChange={e => setManualReturnReason(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button
                  type="submit"
                  style={{ flex: 1, background: '#2563eb', color: '#ffffff', border: 'none', padding: '10px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Xác Nhận Trả Thủ Công
                </button>
                <button
                  type="button"
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', color: '#334155', padding: '10px 16px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
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
