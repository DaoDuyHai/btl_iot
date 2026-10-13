import React, { useState, useEffect } from 'react';
import { apiService } from '../../api/apiService.js';
import { socket } from '../../socket/socketClient.js';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('DASHBOARD'); // 'DASHBOARD' | 'BOOKS' | 'READERS' | 'LOANS'
  const [books, setBooks] = useState([]);
  const [readers, setReaders] = useState([]);
  const [loans, setLoans] = useState([]);
  const [deviceLogs, setDeviceLogs] = useState([]);
  const [newBook, setNewBook] = useState({ isbn: '', title: '', author: '', category: 'CNTT', rfidTag: '' });
  const [newReader, setNewReader] = useState({ studentId: '', name: '', email: '', rfidCard: '' });
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    loadAllData();

    // Lắng nghe cập nhật mượn trả realtime
    socket.on('loans:changed', () => {
      loadAllData();
    });

    return () => socket.off('loans:changed');
  }, []);

  async function loadAllData() {
    try {
      const [b, r, l, d] = await Promise.all([
        apiService.getBooks(),
        apiService.getReaders(),
        apiService.getLoanHistory(30),
        apiService.getDeviceLogs(20)
      ]);
      setBooks(b);
      setReaders(r);
      setLoans(l);
      setDeviceLogs(d);
    } catch (err) {
      console.error('Lỗi tải dữ liệu admin:', err);
    }
  }

  function showToast(text) {
    setMsg(text);
    setTimeout(() => setMsg(null), 3000);
  }

  async function handleAddBook(e) {
    e.preventDefault();
    try {
      await apiService.createBook(newBook);
      showToast('✅ Đã thêm sách mới vào kho thành công!');
      setNewBook({ isbn: '', title: '', author: '', category: 'CNTT', rfidTag: '' });
      const updated = await apiService.getBooks();
      setBooks(updated);
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  async function handleAddReader(e) {
    e.preventDefault();
    try {
      await apiService.createReader(newReader);
      showToast('✅ Đã thêm độc giả mới thành công!');
      setNewReader({ studentId: '', name: '', email: '', rfidCard: '' });
      const updated = await apiService.getReaders();
      setReaders(updated);
    } catch (err) {
      alert(err.response?.data?.message || err.message);
    }
  }

  async function handleTestFeedback(status) {
    try {
      await apiService.sendDeviceCommand('kiosk_01', 'feedback', status);
      showToast(`Đã gửi lệnh test còi & đèn (${status}) tới Kiosk!`);
    } catch (err) {
      alert('Lỗi gửi lệnh tới Kiosk');
    }
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '30px auto', padding: '0 20px' }}>
      {/* Toast */}
      {msg && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          background: '#0f172a',
          color: '#ffffff',
          padding: '12px 24px',
          borderRadius: '10px',
          zIndex: 99,
          fontWeight: '600'
        }}>
          {msg}
        </div>
      )}

      {/* Header & Tabs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: '800', color: '#0f172a' }}>
            HỆ THỐNG QUẢN TRỊ THƯ VIỆN
          </h2>
          <p style={{ color: '#64748b', fontSize: '14px' }}>Giám sát Kiosk IoT, Kho Sách, Độc Giả và Giao Dịch</p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {[
            { id: 'DASHBOARD', label: '📊 Giám Sát IoT' },
            { id: 'BOOKS', label: '📚 Kho Sách' },
            { id: 'READERS', label: '🎓 Độc Giả' },
            { id: 'LOANS', label: '📜 Lịch Sử Mượn' }
          ].map(tab => (
            <button
              key={tab.id}
              className="btn"
              style={{
                background: activeTab === tab.id ? '#2563eb' : '#ffffff',
                color: activeTab === tab.id ? '#ffffff' : '#475569',
                border: '1px solid #e2e8f0',
                padding: '8px 16px',
                fontSize: '14px'
              }}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab 1: DASHBOARD & GIÁM SÁT IOT */}
      {activeTab === 'DASHBOARD' && (
        <div>
          {/* 4 Cards thống kê */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <div className="card">
              <span style={{ fontSize: '13px', color: '#64748b' }}>Tổng đầu sách</span>
              <div style={{ fontSize: '28px', fontWeight: '800', color: '#2563eb', marginTop: '6px' }}>{books.length}</div>
            </div>
            <div className="card">
              <span style={{ fontSize: '13px', color: '#64748b' }}>Sách đang được mượn</span>
              <div style={{ fontSize: '28px', fontWeight: '800', color: '#d97706', marginTop: '6px' }}>
                {books.filter(b => b.status === 'borrowed').length}
              </div>
            </div>
            <div className="card">
              <span style={{ fontSize: '13px', color: '#64748b' }}>Tổng số độc giả</span>
              <div style={{ fontSize: '28px', fontWeight: '800', color: '#16a34a', marginTop: '6px' }}>{readers.length}</div>
            </div>
            <div className="card">
              <span style={{ fontSize: '13px', color: '#64748b' }}>Giao dịch mượn/trả</span>
              <div style={{ fontSize: '28px', fontWeight: '800', color: '#7c3aed', marginTop: '6px' }}>{loans.length}</div>
            </div>
          </div>

          {/* Điều khiển từ xa & Nhật ký thiết bị */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
            <div className="card">
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>
                🎮 Điều Khiển Trạm Kiosk Từ Xa
              </h3>
              <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
                Bắn lệnh MQTT trực tiếp từ Server xuống ESP32 để kiểm tra còi chip và đèn LED.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <button className="btn btn-success" onClick={() => handleTestFeedback('success')}>
                  🔊 Kêu Bíp + Nháy LED Xanh (Thành công)
                </button>
                <button className="btn btn-danger" onClick={() => handleTestFeedback('error')}>
                  🚨 Kêu Bíp Bíp + Nháy LED Đỏ (Lỗi)
                </button>
              </div>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>
                📡 Nhật Ký Hoạt Động Kiosk (Realtime Logs)
              </h3>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Thời Gian</th>
                        <th>Sự Kiện</th>
                        <th>Chi Tiết</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deviceLogs.map(log => (
                        <tr key={log._id}>
                          <td>{new Date(log.timestamp).toLocaleTimeString('vi-VN')}</td>
                          <td>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: '700',
                              background: log.event === 'scan' ? '#eff6ff' : '#f0fdf4',
                              color: log.event === 'scan' ? '#2563eb' : '#16a34a'
                            }}>
                              {log.event.toUpperCase()}
                            </span>
                          </td>
                          <td><code>{JSON.stringify(log.payload || {})}</code></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: KHO SÁCH */}
      {activeTab === 'BOOKS' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
          {/* Form thêm sách */}
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Thêm Sách Mới</h3>
            <form onSubmit={handleAddBook} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600' }}>Tên Sách:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={newBook.title}
                  onChange={e => setNewBook({ ...newBook, title: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600' }}>Tác Giả:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={newBook.author}
                  onChange={e => setNewBook({ ...newBook, author: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600' }}>Mã Thẻ RFID (Dán vào sách):</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: A1B2C3D4"
                  style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={newBook.rfidTag}
                  onChange={e => setNewBook({ ...newBook, rfidTag: e.target.value.toUpperCase() })}
                />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600' }}>ISBN / Mã Sách:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={newBook.isbn}
                  onChange={e => setNewBook({ ...newBook, isbn: e.target.value })}
                />
              </div>
              <button type="submit" className="btn btn-primary" style={{ marginTop: '10px' }}>
                ➕ Lưu Sách Vào Kho
              </button>
            </form>
          </div>

          {/* Bảng danh sách sách */}
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Danh Mục Sách</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Tên Sách</th>
                    <th>Tác Giả</th>
                    <th>Mã RFID</th>
                    <th>Trạng Thái</th>
                  </tr>
                </thead>
                <tbody>
                  {books.map(b => (
                    <tr key={b._id}>
                      <td style={{ fontWeight: '600' }}>{b.title}</td>
                      <td>{b.author}</td>
                      <td><code>{b.rfidTag}</code></td>
                      <td>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: '600',
                          background: b.status === 'available' ? '#dcfce7' : '#fef3c7',
                          color: b.status === 'available' ? '#15803d' : '#b45309'
                        }}>
                          {b.status === 'available' ? 'Sẵn sàng' : 'Đang mượn'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: ĐỘC GIẢ */}
      {activeTab === 'READERS' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Thêm Độc Giả</h3>
            <form onSubmit={handleAddReader} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600' }}>Mã Sinh Viên (MSSV):</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={newReader.studentId}
                  onChange={e => setNewReader({ ...newReader, studentId: e.target.value.toUpperCase() })}
                />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600' }}>Họ Và Tên:</label>
                <input
                  type="text"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={newReader.name}
                  onChange={e => setNewReader({ ...newReader, name: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600' }}>Email:</label>
                <input
                  type="email"
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={newReader.email}
                  onChange={e => setNewReader({ ...newReader, email: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600' }}>Mã Thẻ RFID (Thẻ Sinh Viên):</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: E2801192"
                  style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                  value={newReader.rfidCard}
                  onChange={e => setNewReader({ ...newReader, rfidCard: e.target.value.toUpperCase() })}
                />
              </div>
              <button type="submit" className="btn btn-primary" style={{ marginTop: '10px' }}>
                ➕ Lưu Độc Giả
              </button>
            </form>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Danh Sách Độc Giả</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>MSSV</th>
                    <th>Họ Tên</th>
                    <th>Mã Thẻ RFID</th>
                    <th>Email</th>
                  </tr>
                </thead>
                <tbody>
                  {readers.map(r => (
                    <tr key={r._id}>
                      <td style={{ fontWeight: '700' }}>{r.studentId}</td>
                      <td>{r.name}</td>
                      <td><code>{r.rfidCard}</code></td>
                      <td>{r.email}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: LỊCH SỬ MƯỢN */}
      {activeTab === 'LOANS' && (
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Lịch Sử Giao Dịch Toàn Hệ Thống</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Độc Giả</th>
                  <th>Cuốn Sách</th>
                  <th>Ngày Mượn</th>
                  <th>Hạn Trả</th>
                  <th>Trạng Thái</th>
                </tr>
              </thead>
              <tbody>
                {loans.map(l => (
                  <tr key={l._id}>
                    <td style={{ fontWeight: '600' }}>{l.readerId?.name} ({l.readerId?.studentId})</td>
                    <td>{l.bookId?.title}</td>
                    <td>{new Date(l.borrowDate).toLocaleDateString('vi-VN')}</td>
                    <td>{new Date(l.dueDate).toLocaleDateString('vi-VN')}</td>
                    <td>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600',
                        background: l.status === 'returned' ? '#dcfce7' : l.status === 'overdue' ? '#fee2e2' : '#eff6ff',
                        color: l.status === 'returned' ? '#15803d' : l.status === 'overdue' ? '#dc2626' : '#2563eb'
                      }}>
                        {l.status === 'returned' ? 'Đã trả' : l.status === 'overdue' ? 'Quá hạn' : 'Đang mượn'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

