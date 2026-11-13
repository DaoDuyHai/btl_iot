# NHIỆM VỤ CUỐI CÙNG: ĐÓNG BĂNG AI SEARCH V1.0 VÀ XÂY DỰNG WEBSITE DEMO

Bạn đang làm việc trực tiếp trên source code dự án AI Search. Hãy khảo sát toàn bộ cấu trúc mã nguồn, dataset, cấu hình và các báo cáo kiểm thử hiện có trước khi thực hiện.

Mục tiêu là hoàn thiện một website demo độc lập để tôi trực tiếp trải nghiệm và đánh giá AI Search trước khi tích hợp vào dự án Smart Library Kiosk.

Đây là nhiệm vụ bàn giao cuối cùng của AI Search V1.0. Ưu tiên tính ổn định, đơn giản và hoạt động thực tế.

---

## 1. ĐÓNG BĂNG AI SEARCH ENGINE V1.0

Sử dụng phiên bản source code hiện tại, bao gồm các thay đổi đã khắc phục lỗi NULL/NAN.

Phương pháp tìm kiếm chính thức duy nhất phục vụ người dùng là:

**HYBRID SEARCH = BM25 + SEMANTIC E5 + RRF**

Cấu hình hiện tại phải được giữ nguyên:

- BM25Okapi: tìm kiếm dựa trên từ khóa.
- Semantic Search: sử dụng `intfloat/multilingual-e5-small`.
- RRF: kết hợp kết quả BM25 và Semantic.
- RRF k = 60.
- fetch_k = 200.
- Giữ nguyên cách tiền xử lý truy vấn, chuẩn hóa dữ liệu và tạo embedding hiện tại.

BM25 và Semantic E5 là hai thành phần nội bộ của Hybrid Search, không phải hai phương pháp riêng để khách hàng lựa chọn.

Yêu cầu:

- Không thay đổi thuật toán tìm kiếm.
- Không thay đổi mô hình embedding.
- Không tiếp tục thử nghiệm hyperparameter.
- Không thay đổi dataset 3.000 sách.
- Không chỉnh sửa Ground Truth.
- Không tự ý viết lại hoặc thay thế AI Search Engine hiện tại.
- Không tiếp tục tối ưu chỉ số benchmark nếu không có lỗi nghiêm trọng được xác minh.

Nếu phát hiện lỗi nghiêm trọng ảnh hưởng đến khả năng hoạt động, hãy báo cáo rõ nguyên nhân và phạm vi trước khi sửa.

## 2. XÂY DỰNG WEBSITE DEMO ĐỘC LẬP

Tạo một website demo để người dùng có thể trực tiếp sử dụng AI Search.

Website chỉ cần một phương pháp tìm kiếm duy nhất là Hybrid Search.

Không hiển thị lựa chọn BM25, Semantic hoặc Hybrid trên giao diện.

### 2.1. Giao diện tìm kiếm

Thiết kế giao diện đơn giản, hiện đại, dễ sử dụng, phù hợp với hệ thống tìm kiếm sách.

Trang chính cần có:

- Tên hệ thống: AI Smart Library Search.
- Một ô nhập nội dung tìm kiếm.
- Nút Tìm kiếm.
- Có thể nhấn Enter để thực hiện truy vấn.
- Có nút xóa nội dung tìm kiếm.
- Có trạng thái đang tìm kiếm.
- Không cho phép truy vấn rỗng.

Người dùng không cần hiểu thuật toán bên trong. Trải nghiệm phải đơn giản:

**Nhập nội dung → Tìm kiếm → Nhận kết quả.**

### 2.2. Kết quả tìm kiếm

Khi người dùng thực hiện truy vấn, website gọi trực tiếp Hybrid Search Engine hiện tại và hiển thị danh sách kết quả.

Mỗi kết quả sách hiển thị các thông tin có sẵn trong dataset:

- Tên sách.
- Tác giả.
- Thể loại.
- Thể loại con.
- Mô tả sách nếu có.
- Từ khóa nếu có.
- Mã sách phù hợp với cấu trúc dữ liệu hiện tại.
- Thứ hạng trong danh sách kết quả.

Sắp xếp theo đúng thứ tự mà Hybrid Search Engine trả về.

Không tự tạo thông tin sách hoặc tự ý thay đổi điểm xếp hạng.

Nếu metadata bị thiếu, hiển thị giá trị mặc định phù hợp, không để xuất hiện `nan`, `None`, `null`.

### 2.3. Thông tin tìm kiếm

Sau mỗi truy vấn, có thể hiển thị:

- Phương pháp: Hybrid Search.
- Tổng số kết quả trả về.
- Thời gian xử lý truy vấn (ms).
- Danh sách kết quả theo thứ hạng.

Nếu engine có sẵn RRF score thì hiển thị điểm đó. Không tự tính hoặc tạo ra điểm số giả.

### 2.4. Trải nghiệm người dùng

- Giao diện responsive cơ bản.
- Có trạng thái không tìm thấy kết quả.
- Có thông báo lỗi thân thiện nếu backend gặp sự cố.
- Cho phép thực hiện truy vấn mới nhanh chóng.
- Không cần đăng nhập, đăng ký hoặc phân quyền.
- Không cần chức năng quản lý sách.
- Không cần chức năng mượn/trả sách.
- Không cần các chức năng thuộc hệ thống Smart Library Kiosk lớn hơn.

## 3. YÊU CẦU KỸ THUẬT

- Website hoạt động độc lập với dự án Smart Library Kiosk.
- Tận dụng trực tiếp AI Search Engine hiện tại.
- Không sao chép hoặc viết lại thuật toán tìm kiếm.
- Nếu cần backend API, hãy xây dựng một lớp API mỏng để frontend gọi Hybrid Search Engine.
- Không sử dụng dữ liệu giả hoặc kết quả hardcode.
- Không yêu cầu MongoDB hoặc cơ sở dữ liệu mới nếu không thực sự cần thiết.
- Tận dụng các thư viện và framework đã có trong dự án.
- Chỉ cài đặt thêm những thư viện thực sự cần thiết.

Website cần chạy được trên máy tính Windows 11.

## 4. KIỂM THỬ WEBSITE

Sau khi hoàn thành, hãy trực tiếp chạy thử website và xác minh các nội dung sau:

1. Backend khởi động thành công.
2. Frontend khởi động thành công.
3. Trình duyệt truy cập được website.
4. Người dùng nhập truy vấn tiếng Việt có dấu và tìm kiếm thành công.
5. Người dùng nhập truy vấn không dấu và tìm kiếm thành công.
6. Website thực sự gọi Hybrid Search Engine hiện tại.
7. Kết quả trả về đúng dữ liệu từ kho 3.000 sách.
8. Thứ tự xếp hạng được giữ nguyên từ engine.
9. Metadata không xuất hiện `nan`, `None`, `null`.
10. Truy vấn rỗng và truy vấn không có kết quả được xử lý hợp lý.
11. Không xảy ra lỗi nghiêm trọng khi thực hiện nhiều truy vấn liên tiếp.

Không được chỉ kiểm tra bằng cách đọc code. Hãy chạy chương trình thực tế trong khả năng môi trường hiện tại.

Không tự nhận PASS nếu chưa thực sự kiểm thử được.

## 5. BÀN GIAO VÀ HƯỚNG DẪN SỬ DỤNG

Sau khi hoàn thành, tạo file:

`AI_SEARCH_V1_FINAL_HANDOVER.md`

Nội dung gồm:

1. Kiến trúc tổng thể website.
2. Phương pháp tìm kiếm chính thức và cách Hybrid Search hoạt động.
3. Công nghệ sử dụng.
4. Cấu trúc thư mục.
5. Những file mới được tạo.
6. Những file cũ được chỉnh sửa.
7. Kết quả kiểm thử thực tế.
8. Các giới hạn còn tồn tại.
9. Hướng dẫn cài đặt và chạy website.

Đặc biệt, cung cấp chính xác các lệnh cần chạy:

- Cài đặt thư viện.
- Khởi động backend.
- Khởi động frontend.
- Địa chỉ localhost để truy cập website.
- Cách dừng chương trình.

Tôi muốn có thể mở VS Code, chạy theo hướng dẫn và trực tiếp sử dụng website trên trình duyệt Windows 11.

## 6. GIỚI HẠN PHẠM VI

Đây là nhiệm vụ bàn giao cuối cùng.

Không mở rộng thêm tính năng ngoài yêu cầu.

Không phát triển lại thuật toán tìm kiếm.

Không thêm lựa chọn phương pháp tìm kiếm cho người dùng.

Không tiếp tục tối ưu benchmark.

Không tích hợp vào Smart Library Kiosk ở giai đoạn này.

Không triển khai hosting hoặc đưa website lên Internet nếu chưa được yêu cầu.

Không tạo thêm các báo cáo kiểm toán không cần thiết.

Ưu tiên hoàn thành website demo hoạt động ổn định.

## 7. ĐIỀU KIỆN HOÀN THÀNH

Nhiệm vụ được xem là hoàn thành khi:

- AI Search Engine V1.0 được giữ nguyên.
- Website chạy độc lập trên máy tính.
- Website chỉ sử dụng Hybrid Search.
- Người dùng có thể nhập truy vấn tiếng Việt.
- Hệ thống trả về danh sách sách thực tế từ dataset.
- Kết quả được hiển thị rõ ràng, đúng thứ hạng.
- Có hướng dẫn chạy cụ thể.
- Có file bàn giao cuối cùng.

**Hãy thực hiện trực tiếp trên source code hiện tại. Không chỉ đưa ra kế hoạch hoặc ví dụ minh họa. Hãy hoàn thành, chạy thử và bàn giao một website demo có thể sử dụng thực tế.**
