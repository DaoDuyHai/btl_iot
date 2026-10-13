# THIẾT KẾ GIAO DIỆN HỆ THỐNG KIOSK THƯ VIỆN

## 1. Trang Chủ (Home Screen)
* **Mục đích:** Màn hình chào mừng, hiển thị 4 nút chức năng chính cho bạn đọc lựa chọn.
* **Giao diện:**
  * **Tiêu đề:** Thư viện Số / Chào mừng bạn đọc đến với Kiosk Tự phục vụ.
  * **4 Nút chức năng chính (Kích thước lớn, dễ thao tác chạm):**
    1. 📖 **Mượn sách**
    2. 🔄 **Trả sách**
    3. ⏳ **Gia hạn**
    4. 👤 **Thông tin bạn đọc**

---

## 2. Chức Năng: Mượn Sách

### Bước 1: Yêu cầu quẹt thẻ
* **Hiển thị:** Thông báo *"Vui lòng quẹt thẻ bạn đọc của bạn"*.
* **Đồ họa:** Hiệu ứng animation minh họa hành động quẹt thẻ (thẻ đang di chuyển qua khe đọc) để thu hút và hướng dẫn người dùng trực quan.

### Bước 2: Quét thẻ thành công & Đặt tài liệu
* **Bố cục màn hình (Chia 2 phần):**
  * **1/4 Bên trái:** 
    * Hiển thị thông tin độc giả (Họ tên, Mã bạn đọc, Ảnh đại diện).
    * Animation hướng dẫn liên tục kèm dòng chữ: *"Đặt tài liệu vào khu vực đầu đọc"*.
  * **3/4 Bên phải:** 
    * Hiển thị danh sách sách đã quẹt (RFID/Barcode).
    * Các thông tin chi tiết gồm: Tiêu đề sách, Số lượng, Hạn trả dự kiến.
* **Hành động hoàn tất:**
  * Nút **"Hoàn thành"**.
  * **Hệ thống xử lý:** Sau khi bấm hoàn thành, biên lai/hóa đơn mượn sách sẽ được tự động gửi vào email của bạn đọc.

---

## 3. Chức Năng: Trả Sách

### Bước 1: Yêu cầu quẹt thẻ
* **Hiển thị:** Thông báo *"Vui lòng quẹt thẻ bạn đọc của bạn"*.
* **Đồ họa:** Hiệu ứng animation minh họa quẹt thẻ sinh động.

### Bước 2: Quét thẻ thành công & Đặt tài liệu
* **Bố cục màn hình (Chia 2 phần):**
  * **1/4 Bên trái:** 
    * Hiển thị thông tin độc giả (Họ tên, Mã bạn đọc).
    * Animation liên tục kèm dòng chữ: *"Đặt tài liệu vào khu vực đầu đọc"*.
  * **3/4 Bên phải:** 
    * Hiển thị thông tin sách được quẹt trả lên hệ thống.
    * Các thông tin chi tiết gồm: Tiêu đề sách, Số lượng sách.
* **Hành động hoàn tất:**
  * Nút **"Hoàn thành"**.
  * **Hệ thống xử lý:** Sau khi bấm hoàn thành, biên lai/hóa đơn trả sách sẽ được gửi vào email bạn đọc.

---

## 4. Chức Năng: Gia Hạn Sách

### Bước 1: Yêu cầu quẹt thẻ
* **Hiển thị:** Thông báo *"Vui lòng quẹt thẻ bạn đọc của bạn"*.
* **Đồ họa:** Hiệu ứng animation quẹt thẻ trực quan.

### Bước 2: Hiển thị danh sách sách đang mượn
* **Giao diện:** 
  * Danh sách các cuốn sách đang mượn kèm theo: Tiêu đề, Hạn trả hiện tại.
  * Có ô checkbox (tích chọn) ở mỗi dòng để bạn đọc chọn cuốn sách cần gia hạn.
* **Thao tác & Hoàn tất:**
  * Nút **"Gia hạn"** ở cuối danh sách. Khi bấm vào đây, các cuốn sách đã được tích chọn sẽ được hệ thống cập nhật lại thời gian hạn trả mới.
  * Nút **"Hoàn thành"**: Sau khi xác nhận, thông tin chi tiết về việc gia hạn sách sẽ được gửi thông báo về email của bạn đọc.

---

## 5. Chức Năng: Thông Tin Bạn Đọc

### Bước 1: Yêu cầu quẹt thẻ
* **Hiển thị:** Thông báo *"Vui lòng quẹt thẻ bạn đọc của bạn"*.
* **Đồ họa:** Hiệu ứng animation quẹt thẻ sống động.

### Bước 2: Hiển thị thông tin tổng quan của bạn đọc
* **Giao diện Dashboard cá nhân:**
  * **Thông tin tài khoản:** Họ tên, Mã thẻ, Lớp/Đơn vị công tác, Email.
  * **Danh sách sách đang mượn:** Tiêu đề, ngày mượn, hạn trả.
  * **Cảnh báo quá hạn:** Hiển thị nổi bật nếu có sách bị quá hạn.
  * **Khoản phạt (nếu có):** Chi tiết tiền phạt hoặc trạng thái vi phạm nội quy thư viện.