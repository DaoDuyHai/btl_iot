import React from 'react';
import { MapPin, Navigation, Compass, X, CheckCircle2, Footprints } from 'lucide-react';

export default function ShelfLocatorModal({ book, onClose }) {
  if (!book) return null;

  const targetShelf = (book.shelf || 'A').toUpperCase();
  const targetFloor = book.floor || 1;
  const targetPosition = book.position || `${targetShelf}1-01`;

  // Danh sách các dãy kệ mô phỏng trong Thư viện PTIT
  const shelvesRow1 = ['A', 'B', 'C'];
  const shelvesRow2 = ['D', 'E', 'F'];

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px'
    }}>
      <div style={{
        background: '#ffffff',
        width: '100%',
        maxWidth: '780px',
        borderRadius: '24px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.35)',
        overflow: 'hidden',
        border: '1px solid #e2e8f0',
        animation: 'modalSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)'
      }}>
        {/* Header Modal */}
        <div style={{
          background: 'linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%)',
          padding: '20px 24px',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.18)',
              padding: '10px',
              borderRadius: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Compass size={24} color="#fef08a" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '800', letterSpacing: '-0.3px' }}>
                ĐỊNH VỊ KỆ SÁCH VẬT LÝ THƯ VIỆN PTIT
              </h3>
              <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#fecaca' }}>
                Chỉ dẫn đường đi thực tế từ trạm Kiosk tới vị trí sách
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.15)',
              border: 'none',
              color: '#ffffff',
              cursor: 'pointer',
              padding: '8px',
              borderRadius: '9999px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Nội dung chính */}
        <div style={{ padding: '24px' }}>
          {/* Card tóm tắt sách & Tọa độ nổi bật */}
          <div style={{
            background: '#f8fafc',
            border: '1.5px solid #e2e8f0',
            borderRadius: '16px',
            padding: '16px 20px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>
                Tài liệu cần tìm
              </div>
              <div style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', marginTop: '2px' }}>
                {book.title}
              </div>
              <div style={{ fontSize: '13px', color: '#475569' }}>
                Tác giả: <strong>{book.author}</strong> • Thể loại: {book.category}
              </div>
            </div>

            {/* Badge tọa độ to rõ */}
            <div style={{
              background: '#fee2e2',
              border: '1.5px solid #fca5a5',
              padding: '10px 18px',
              borderRadius: '12px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '11px', fontWeight: '800', color: '#991b1b', textTransform: 'uppercase' }}>
                Tọa độ chính xác
              </div>
              <div style={{ fontSize: '20px', fontWeight: '900', color: '#991b1b' }}>
                Tầng {targetFloor} • Kệ {targetShelf}
              </div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#b91c1c' }}>
                Ô vị trí: {targetPosition}
              </div>
            </div>
          </div>

          {/* Sơ đồ mặt bằng thu nhỏ (Floor Map Simulation) */}
          <div style={{
            border: '2px dashed #cbd5e1',
            borderRadius: '18px',
            padding: '20px',
            background: '#fdfdfd',
            position: 'relative',
            marginBottom: '20px'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px',
              fontSize: '12px',
              fontWeight: '700',
              color: '#64748b'
            }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Navigation size={15} color="#991b1b" /> Mặt bằng Tầng {targetFloor} - Khu Lưu Trữ Sách Mở
              </span>
              <span style={{
                background: '#dcfce7',
                color: '#15803d',
                padding: '3px 10px',
                borderRadius: '9999px',
                fontSize: '11px'
              }}>
                🟢 Trạng thái: Đang mở cửa
              </span>
            </div>

            {/* Dãy kệ 1 */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', marginBottom: '14px' }}>
              {shelvesRow1.map(shelf => {
                const isTarget = shelf === targetShelf;
                return (
                  <div
                    key={shelf}
                    style={{
                      padding: '16px',
                      borderRadius: '12px',
                      textAlign: 'center',
                      border: isTarget ? '2px solid #b91c1c' : '1.5px solid #e2e8f0',
                      background: isTarget ? '#fee2e2' : '#ffffff',
                      boxShadow: isTarget ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'none',
                      position: 'relative',
                      transition: 'all 0.3s'
                    }}
                  >
                    {isTarget && (
                      <span style={{
                        position: 'absolute',
                        top: '-10px',
                        right: '10px',
                        background: '#991b1b',
                        color: '#ffffff',
                        fontSize: '10px',
                        fontWeight: '800',
                        padding: '2px 8px',
                        borderRadius: '9999px',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                      }}>
                        ĐÍCH ĐẾN
                      </span>
                    )}
                    <div style={{ fontSize: '18px', fontWeight: '900', color: isTarget ? '#991b1b' : '#334155' }}>
                      📚 DÃY KỆ {shelf}
                    </div>
                    <div style={{ fontSize: '11px', color: isTarget ? '#7f1d1d' : '#64748b', marginTop: '4px' }}>
                      {isTarget ? `Chứa sách ở ô: ${targetPosition}` : `Khu vực sách tổng hợp`}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Dãy kệ 2 */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
              {shelvesRow2.map(shelf => {
                const isTarget = shelf === targetShelf;
                return (
                  <div
                    key={shelf}
                    style={{
                      padding: '16px',
                      borderRadius: '12px',
                      textAlign: 'center',
                      border: isTarget ? '2px solid #b91c1c' : '1.5px solid #e2e8f0',
                      background: isTarget ? '#fee2e2' : '#ffffff',
                      boxShadow: isTarget ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'none',
                      position: 'relative',
                      transition: 'all 0.3s'
                    }}
                  >
                    {isTarget && (
                      <span style={{
                        position: 'absolute',
                        top: '-10px',
                        right: '10px',
                        background: '#991b1b',
                        color: '#ffffff',
                        fontSize: '10px',
                        fontWeight: '800',
                        padding: '2px 8px',
                        borderRadius: '9999px'
                      }}>
                        ĐÍCH ĐẾN
                      </span>
                    )}
                    <div style={{ fontSize: '18px', fontWeight: '900', color: isTarget ? '#991b1b' : '#334155' }}>
                      📚 DÃY KỆ {shelf}
                    </div>
                    <div style={{ fontSize: '11px', color: isTarget ? '#7f1d1d' : '#64748b', marginTop: '4px' }}>
                      {isTarget ? `Chứa sách ở ô: ${targetPosition}` : `Khu vực sách tổng hợp`}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Vị trí Kiosk hiện tại ở dưới cùng */}
            <div style={{
              marginTop: '18px',
              padding: '10px 16px',
              borderRadius: '10px',
              background: '#f1f5f9',
              border: '1px solid #cbd5e1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '12.5px',
              color: '#334155'
            }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700' }}>
                <MapPin size={16} color="#0284c7" /> Vị trí hiện tại của bạn: Trạm Kiosk Tự Phục Vụ PTIT-01
              </span>
              <span style={{ color: '#0284c7', fontWeight: '700' }}>
                Khoảng cách: ~15 mét
              </span>
            </div>
          </div>

          {/* 4 Bước hướng dẫn thực tế */}
          <div style={{
            background: '#fffbeb',
            border: '1px solid #fef3c7',
            borderRadius: '14px',
            padding: '14px 18px',
            marginBottom: '20px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '800', color: '#92400e', fontSize: '13.5px', marginBottom: '8px' }}>
              <Footprints size={17} /> HƯỚNG DẪN 3 BƯỚC ĐẾN LẤY SÁCH VÀ MƯỢN TÀI LIỆU:
            </div>
            <ol style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#78350f', lineHeight: 1.6 }}>
              <li>Di chuyển lên <strong>Tầng {targetFloor}</strong>, tìm đến <strong>Dãy Kệ {targetShelf}</strong> theo sơ đồ bên trên.</li>
              <li>Tìm cuốn sách mang mã <strong>{book.book_id || book._id}</strong> ở ô <strong>{targetPosition}</strong>.</li>
              <li>Lấy sách mang về trạm Kiosk này, chọn chức năng <strong>"Mượn tài liệu"</strong> và đặt sách lên bàn đọc RFID RC522 để hoàn tất!</li>
            </ol>
          </div>

          {/* Nút đóng */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button
              onClick={onClose}
              style={{
                background: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
                border: 'none',
                color: '#ffffff',
                padding: '12px 28px',
                borderRadius: '12px',
                fontSize: '14px',
                fontWeight: '800',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 12px rgba(153, 27, 27, 0.35)',
                transition: 'all 0.2s'
              }}
            >
              <CheckCircle2 size={18} />
              <span>Đã hiểu, tôi sẽ đi lấy sách</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
