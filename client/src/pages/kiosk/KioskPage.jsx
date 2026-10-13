import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import KioskHeader from '../../components/KioskHeader.jsx';
import SwipeCardModal from '../../components/SwipeCardModal.jsx';
import ReceiptModal from '../../components/ReceiptModal.jsx';
import VietQrModal from '../../components/VietQrModal.jsx';
import KioskHome from './KioskHome.jsx';
import BorrowSection from './BorrowSection.jsx';
import ReturnSection from './ReturnSection.jsx';
import RenewSection from './RenewSection.jsx';
import AccountSection from './AccountSection.jsx';
import { socket } from '../../socket/socketClient.js';
import { apiService } from '../../api/apiService.js';
import { playKioskBeep } from '../../utils/audio.js';

export default function KioskPage() {
  const [currentScreen, setCurrentScreen] = useState('HOME'); // 'HOME' | 'BORROW' | 'RETURN' | 'RENEW' | 'ACCOUNT'
  const [currentReader, setCurrentReader] = useState(null);
  const [activeLoans, setActiveLoans] = useState([]);
  const [borrowCart, setBorrowCart] = useState([]);
  const [returnedBooks, setReturnedBooks] = useState([]);

  const [isSwipeModalOpen, setIsSwipeModalOpen] = useState(false);
  const [targetFeature, setTargetFeature] = useState(null);
  const [receiptData, setReceiptData] = useState(null);
  const [qrModalData, setQrModalData] = useState(null);
  const [deviceStatus, setDeviceStatus] = useState({ status: 'offline' });
  const [timeoutCounter, setTimeoutCounter] = useState(60);
  const [toasts, setToasts] = useState([]);

  // Hàm hiển thị Toast thông báo kiểu shadcn/ui
  function showToast(type, title, message, duration = 4000) {
    const id = Date.now() + Math.random().toString(36).substring(2, 9);
    setToasts(prev => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }

  function removeToast(id) {
    setToasts(prev => prev.filter(t => t.id !== id));
  }

  // 1. Lắng nghe WebSocket Socket.IO (RFID và Trạng thái Kiosk)
  useEffect(() => {
    function handleKioskEvent(event) {
      console.log('📡 [Kiosk UI] Nhận sự kiện Socket:', event);
      const { type, data } = event;

      if (type === 'READER_AUTHENTICATED') {
        // 1. Bảo vệ phiên làm việc: Nếu đang có độc giả A mà quẹt thẻ độc giả B khác
        if (currentReader && String(currentReader._id) !== String(data.reader._id)) {
          playKioskBeep('error');
          showToast(
            'warning',
            'Đang có phiên làm việc',
            `Kiosk đang phục vụ bạn đọc ${currentReader.name} (${currentReader.studentId}). Vui lòng bấm "Kết thúc phiên" trước khi quẹt thẻ người khác!`
          );
          return;
        }

        playKioskBeep('success');
        setCurrentReader(data.reader);
        const loans = data.activeLoans || [];
        setActiveLoans(loans);
        setIsSwipeModalOpen(false);
        setTimeoutCounter(60);

        const hasOverdue = loans.some(l => new Date() > new Date(l.dueDate));
        if (hasOverdue) {
          showToast('warning', 'Cảnh báo mượn quá hạn', `Bạn đọc ${data.reader.name} đang có tài liệu quá hạn chưa trả! Vui lòng hoàn trả trước.`);
        } else {
          showToast('success', 'Xác thực thành công', `Xin chào bạn đọc ${data.reader.name} (${data.reader.studentId})`);
        }

        // Chuyển màn hình tương ứng NẾU người dùng đã chọn trước
        if (targetFeature) {
          setCurrentScreen(targetFeature);
          setTargetFeature(null);
        }
        // Nếu đang ở HOME mà quẹt thẻ: Ở NGUYÊN TẠI HOME, KHÔNG tự ý nhảy vào MƯỢN!
      } 
      else if (type === 'BOOK_SCANNED') {
        setTimeoutCounter(60);
        const book = data.book;

        if (currentScreen === 'RETURN') {
          // Xử lý trả sách
          processReturnBook(book.rfidTag);
        } else if (currentScreen === 'BORROW') {
          if (!currentReader) {
            playKioskBeep('error');
            showToast('warning', 'Chưa xác thực bạn đọc', 'Vui lòng quẹt thẻ sinh viên trước khi quét tài liệu mượn!');
            setIsSwipeModalOpen(true);
            setTargetFeature('BORROW');
            return;
          }

          // 1. Kiểm tra bạn đọc có sách quá hạn không (chặn mượn mới)
          const hasOverdue = activeLoans.some(l => new Date() > new Date(l.dueDate));
          if (hasOverdue) {
            playKioskBeep('error');
            showToast('error', 'Chặn quyền mượn sách', 'Bạn đang có tài liệu quá hạn chưa trả! Thư viện tạm dừng cho mượn mới đến khi hoàn tất trả sách & nộp phạt.');
            return;
          }

          // 2. Kiểm tra sách trùng trong giỏ
          if (borrowCart.some(b => b._id === book._id)) {
            playKioskBeep('error');
            showToast('warning', 'Sách đã có trong giỏ', `Cuốn sách "${book.title}" đã được thêm vào giỏ mượn.`);
            return;
          }

          // 3. Kiểm tra hạn mức mượn tối đa 5 cuốn
          if (activeLoans.length + borrowCart.length >= 5) {
            playKioskBeep('error');
            showToast('error', 'Vượt quá hạn mức mượn', `Bạn chỉ được mượn tối đa 5 cuốn (Hiện đang mượn ${activeLoans.length}, giỏ có ${borrowCart.length}).`);
            return;
          }

          // 4. KIỂM TRA TOÀN VẸN: Sách có đang khả dụng không?
          // Nếu sách có status !== 'available' hoặc data.isAvailable === false
          if (book.status !== 'available' || data.isAvailable === false) {
            playKioskBeep('error');
            showToast('error', 'Tài liệu không khả dụng', `Cuốn sách "${book.title}" hiện đang được bạn đọc khác mượn hoặc chưa hoàn trả vào kho!`);
            return;
          }

          // Hợp lệ -> Thêm vào giỏ
          playKioskBeep('success');
          setBorrowCart(prev => [...prev, book]);
          showToast('success', 'Đã thêm tài liệu', `"${book.title}" đã được thêm vào giỏ mượn.`);
        } else {
          // Khi đang ở HOME hoặc chức năng khác
          playKioskBeep('error');
          showToast('info', 'Nhận diện tài liệu', `Đã quét sách "${book.title}". Vui lòng chọn chức năng Mượn hoặc Trả tài liệu trên màn hình.`);
        }
      } 
      else if (type === 'UNKNOWN_CARD') {
        playKioskBeep('error');
        showToast('error', 'Thẻ không hợp lệ', 'Thẻ RFID chưa được đăng ký trong hệ thống Thư viện PTIT!');
      }
    }

    function handleDeviceStatus(status) {
      setDeviceStatus(status);
    }

    socket.on('kiosk:event', handleKioskEvent);
    socket.on('device:status', handleDeviceStatus);

    return () => {
      socket.off('kiosk:event', handleKioskEvent);
      socket.off('device:status', handleDeviceStatus);
    };
  }, [currentScreen, targetFeature, currentReader, activeLoans, borrowCart]);

  // 2. Bộ đếm thời gian tự động trở về Trang Chủ khi người dùng bỏ đi (Auto-timeout)
  useEffect(() => {
    if (currentScreen === 'HOME') return;

    const timer = setInterval(() => {
      setTimeoutCounter(prev => {
        if (prev <= 1) {
          handleResetSession();
          return 60;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentScreen]);

  // Điều hướng khi bấm 4 nút chính ở trang chủ
  function handleSelectFeature(feature) {
    if (currentReader) {
      setCurrentScreen(feature);
    } else {
      setTargetFeature(feature);
      setIsSwipeModalOpen(true);
    }
  }

  // Kết thúc phiên làm việc
  function handleResetSession() {
    setCurrentScreen('HOME');
    setCurrentReader(null);
    setBorrowCart([]);
    setReturnedBooks([]);
    setActiveLoans([]);
    setIsSwipeModalOpen(false);
    setReceiptData(null);
    setQrModalData(null);
  }

  // Xử lý xác nhận mượn sách
  async function handleConfirmBorrow() {
    if (!currentReader || borrowCart.length === 0) return;

    try {
      const bookIds = borrowCart.map(b => b._id);
      await apiService.borrowBatch(currentReader._id, bookIds);
      playKioskBeep('success');

      // Hiện biên lai và thông báo đã gửi email
      setReceiptData({
        title: 'MƯỢN TÀI LIỆU THÀNH CÔNG',
        items: borrowCart,
        actionType: 'BORROW'
      });

      showToast('success', 'Mượn sách thành công', `Đã tạo giao dịch mượn ${borrowCart.length} tài liệu và gửi biên lai email.`);
      setBorrowCart([]);
      // Làm mới danh sách đang mượn
      const res = await apiService.getReaderByRfid(currentReader.rfidCard);
      setActiveLoans(res.activeLoans || []);
    } catch (err) {
      playKioskBeep('error');
      showToast('error', 'Lỗi mượn sách', err.response?.data?.message || err.message);
    }
  }

  // Xử lý trả sách
  async function processReturnBook(rfidTag) {
    try {
      const res = await apiService.returnBook(rfidTag);
      if (res.alreadyReturned) {
        playKioskBeep('error');
        showToast('info', 'Tài liệu đã ở trong thư viện', res.message || `Cuốn sách "${res.book?.title}" hiện đã có sẵn trong kho, không có phiếu mượn cần hoàn trả.`);
        return;
      }

      playKioskBeep('success');
      setReturnedBooks(prev => {
        if (prev.some(b => b.book?._id === res.book?._id)) return prev;
        return [...prev, res];
      });

      if (res.isOverdue) {
        showToast('warning', 'Tài liệu quá hạn hoàn trả', `Cuốn "${res.book?.title}" đã quá hạn! Tiền phạt: ${res.fineAmount?.toLocaleString('vi-VN')} VNĐ. Vui lòng quét VietQR nộp phạt.`);
        setQrModalData(res);
      } else {
        showToast('success', 'Trả tài liệu thành công', `Đã ghi nhận trả cuốn "${res.book?.title}".`);
      }

      if (currentReader) {
        const updated = await apiService.getReaderByRfid(currentReader.rfidCard);
        setActiveLoans(updated.activeLoans || []);
      }
    } catch (err) {
      playKioskBeep('error');
      showToast('error', 'Lỗi trả tài liệu', err.response?.data?.message || err.message);
    }
  }

  // Xử lý xác nhận nộp phạt tiền trễ hạn qua VietQR
  async function handleConfirmPaidFine(loanId) {
    try {
      if (!loanId && qrModalData?.loan?._id) {
        loanId = qrModalData.loan._id;
      }
      if (!loanId) {
        throw new Error('Không tìm thấy mã phiếu mượn cần nộp phạt');
      }

      const res = await apiService.payFine(loanId);
      playKioskBeep('success');

      // Cập nhật trạng thái isPaid = true cho cuốn sách tương ứng trong returnedBooks
      setReturnedBooks(prev => prev.map(item => {
        const id = item.loan?._id || item.loanId || item._id;
        if (id === loanId) {
          return { ...item, isPaid: true };
        }
        return item;
      }));

      setQrModalData(null);
      showToast('success', 'Nộp phạt thành công', res.message || 'Đã xác nhận nộp phạt trễ hạn qua VietQR thành công! Khoản nợ quá hạn đã được xóa.');

      // Làm mới danh sách đang mượn của bạn đọc ngay lập tức
      if (currentReader) {
        const updated = await apiService.getReaderByRfid(currentReader.rfidCard);
        setActiveLoans(updated.activeLoans || []);
      }
    } catch (err) {
      playKioskBeep('error');
      showToast('error', 'Lỗi xác nhận nộp phạt', err.response?.data?.message || err.message);
    }
  }

  // Xử lý gia hạn sách
  async function handleRenewLoans(loanIds) {
    try {
      await apiService.renewLoans(loanIds);
      playKioskBeep('success');

      setReceiptData({
        title: 'GIA HẠN TÀI LIỆU THÀNH CÔNG',
        items: activeLoans.filter(l => loanIds.includes(l._id)),
        actionType: 'RENEW'
      });

      showToast('success', 'Gia hạn thành công', `Đã gia hạn thành công thêm 14 ngày cho các tài liệu.`);

      const updated = await apiService.getReaderByRfid(currentReader.rfidCard);
      setActiveLoans(updated.activeLoans || []);
    } catch (err) {
      playKioskBeep('error');
      showToast('error', 'Lỗi gia hạn tài liệu', err.response?.data?.message || err.message);
    }
  }

  // Xác định tiêu đề hiển thị trên header theo từng màn hình
  const screenMeta = {
    HOME: { title: null, icon: null },
    BORROW: { title: 'Mượn tài liệu', icon: '📥' },
    RETURN: { title: 'Trả tài liệu', icon: '📤' },
    RENEW: { title: 'Gia hạn', icon: '🔄' },
    ACCOUNT: { title: 'Thông tin tài khoản', icon: '👤' }
  };

  return (
    <div className="kiosk-shell">
      {/* 1. Header xanh phong cách Lyngsoe Systems PTIT */}
      <KioskHeader
        title={screenMeta[currentScreen]?.title}
        icon={screenMeta[currentScreen]?.icon}
        onBackHome={currentScreen !== 'HOME' ? handleResetSession : null}
        deviceStatus={deviceStatus}
      />

      {/* 2. Nội dung các màn hình chức năng */}
      {currentScreen === 'HOME' && (
        <KioskHome 
          onSelectFeature={handleSelectFeature} 
          reader={currentReader}
          onLogout={handleResetSession}
        />
      )}

      {currentScreen === 'BORROW' && (
        <BorrowSection
          reader={currentReader}
          borrowCart={borrowCart}
          onRemoveBook={(idx) => setBorrowCart(borrowCart.filter((_, i) => i !== idx))}
          onConfirmBorrow={handleConfirmBorrow}
        />
      )}

      {currentScreen === 'RETURN' && (
        <ReturnSection
          reader={currentReader}
          returnedBooks={returnedBooks}
          onConfirmFinish={async () => {
            const unpaid = returnedBooks.filter(b => b.isOverdue && !b.isPaid);
            if (unpaid.length > 0) {
              playKioskBeep('error');
              showToast('error', 'Chưa hoàn tất nộp phạt', `Còn ${unpaid.length} cuốn sách quá hạn chưa thanh toán tiền phạt. Vui lòng nộp phạt trước khi hoàn tất!`);
              return;
            }

            // Gửi duy nhất 01 email biên lai tổng hợp cho toàn bộ các cuốn trả trong lượt này
            const receiptItems = returnedBooks.map(item => {
              const hasFine = item.isOverdue && item.fineAmount > 0;
              return {
                title: item.book?.title,
                author: item.book?.author,
                dueDate: item.loan?.dueDate,
                statusText: hasFine 
                  ? `Quá hạn (Đã nộp phạt: ${item.fineAmount?.toLocaleString('vi-VN')} đ)` 
                  : 'Đúng hạn (0đ)'
              };
            });

            const targetReaderId = currentReader?._id || returnedBooks[0]?.reader?._id || returnedBooks[0]?.loan?.readerId;
            if (targetReaderId) {
              apiService.finishReturn(targetReaderId, receiptItems).catch(err => {
                console.error('Lỗi gửi email biên lai trả sách:', err);
              });
            }

            setReceiptData({
              title: 'TRẢ TÀI LIỆU THÀNH CÔNG',
              items: returnedBooks,
              actionType: 'RETURN'
            });

            showToast('success', 'Giao dịch hoàn tất', `Đã ghi nhận trả ${returnedBooks.length} tài liệu và gửi 01 email biên lai tổng hợp.`);
          }}
          onOpenVietQrModal={(res) => setQrModalData(res)}
        />
      )}

      {currentScreen === 'RENEW' && (
        <RenewSection
          reader={currentReader}
          activeLoans={activeLoans}
          onRenewLoans={handleRenewLoans}
          onFinish={handleResetSession}
          onPrintReceipt={() => {
            setReceiptData({
              title: 'BIÊN LAI GIA HẠN TÀI LIỆU',
              items: activeLoans,
              actionType: 'RENEW'
            });
          }}
        />
      )}

      {currentScreen === 'ACCOUNT' && (
        <AccountSection
          reader={currentReader}
          activeLoans={activeLoans}
          onNavigate={(target) => setCurrentScreen(target)}
          onFinish={handleResetSession}
        />
      )}

      {/* 3. Modal Quẹt Thẻ Animation (khi bấm nút mà chưa quẹt thẻ) */}
      {isSwipeModalOpen && (
        <SwipeCardModal
          targetFunction={screenMeta[targetFeature]?.title}
          onClose={() => setIsSwipeModalOpen(false)}
        />
      )}

      {/* 4. Modal Biên Lai & Gửi Email Thành Công */}
      {receiptData && (
        <ReceiptModal
          title={receiptData.title}
          reader={currentReader}
          items={receiptData.items}
          actionType={receiptData.actionType}
          onClose={handleResetSession}
        />
      )}

      {/* 5. Modal Nộp Phạt Quá Hạn VietQR */}
      {qrModalData && (
        <VietQrModal
          data={qrModalData}
          onClose={() => setQrModalData(null)}
          onConfirmPaid={handleConfirmPaidFine}
        />
      )}

      {/* 6. Hộp Thông Báo Nổi Shadcn/UI (Toast Notifications) */}
      <div className="kiosk-toast-container">
        {toasts.map(toast => {
          const isError = toast.type === 'error';
          const isWarning = toast.type === 'warning';
          const isSuccess = toast.type === 'success';

          return (
            <div key={toast.id} className={`kiosk-toast kiosk-toast-${toast.type}`}>
              <div style={{ flexShrink: 0, marginTop: '2px' }}>
                {isError && <XCircle size={20} color="#dc2626" />}
                {isWarning && <AlertTriangle size={20} color="#d97706" />}
                {isSuccess && <CheckCircle2 size={20} color="#16a34a" />}
                {!isError && !isWarning && !isSuccess && <Info size={20} color="#2563eb" />}
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '700', color: '#0f172a' }}>{toast.title}</h4>
                <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#475569', lineHeight: 1.4 }}>{toast.message}</p>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '2px', display: 'flex', alignItems: 'center' }}
                aria-label="Đóng"
              >
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
