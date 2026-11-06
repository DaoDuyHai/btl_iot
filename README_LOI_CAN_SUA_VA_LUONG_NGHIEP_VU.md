# README – Lỗi cần sửa và luồng nghiệp vụ hệ thống thư viện IoT

## 1. Mục tiêu hệ thống

Hệ thống sử dụng ESP32, đầu đọc RC522 và RFID để hỗ trợ độc giả tự mượn, trả sách. RFID chỉ nhận diện thẻ độc giả và từng cuốn sách; hệ thống không thể tự phát hiện sách bị rách, ướt, mất trang hoặc hỏng bìa. Việc đánh giá tình trạng vật lý của sách phải do thủ thư thực hiện sau khi sách được trả.

## 2. Các lỗi và chức năng cần sửa

### 2.1. Nhóm bắt buộc sửa

| STT | Hiện trạng                                                                                | Yêu cầu sửa                                                                              |
| --: | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
|   1 | Quét sách trả làm sách chuyển ngay sang `available`, dù chưa bấm **Hoàn thành trả sách**. | Quét chỉ thêm sách vào danh sách chờ. Chỉ cập nhật database sau khi người dùng xác nhận. |
|   2 | Sách vừa trả được coi là sẵn sàng cho người khác mượn ngay.                               | Sau khi trả, chuyển sách sang `pending_inspection` để chờ thủ thư kiểm tra.              |
|   3 | Trả sách bắt buộc quét thẻ độc giả.                                                       | Cho phép trả chỉ bằng nhãn RFID của sách; backend tự tìm lượt mượn đang hoạt động.       |
|   4 | Chưa có màn hình xử lý sách sau khi trả.                                                  | Thêm mục **Sách chờ kiểm tra** cho thủ thư.                                              |
|   5 | Chưa xử lý sách rách, hỏng, mất hoặc cần sửa.                                             | Thêm các kết quả kiểm tra: bình thường, cần sửa, hỏng nặng và mất.                       |
|   6 | Không hoàn tất trả sách khi chưa thanh toán phạt.                                         | Vẫn tiếp nhận sách; khoản phạt được lưu thành công nợ và độc giả bị chặn mượn tiếp.      |
|   7 | LED xanh có thể sáng ngay khi ESP32 gửi sự kiện, trước khi backend xác nhận.              | Chỉ bật LED xanh/còi thành công sau khi backend xử lý thành công.                        |
|   8 | Mượn hoặc trả nhiều sách chưa được bảo vệ bằng database transaction.                      | Toàn bộ giao dịch phải cùng thành công hoặc cùng thất bại.                               |

### 2.2. Nhóm nên bổ sung

| STT | Thiếu sót                                          | Yêu cầu bổ sung                                                                 |
| --: | -------------------------------------------------- | ------------------------------------------------------------------------------- |
|   1 | Trang quản trị chưa có đăng nhập.                  | Xác thực thủ thư trước khi cho phép quản lý dữ liệu và thiết bị.                |
|   2 | Chưa sửa/khóa độc giả hoặc đổi UID thẻ.            | Thêm sửa thông tin, khóa tài khoản và cấp lại thẻ RFID.                         |
|   3 | Chưa sửa thông tin hoặc thay RFID cho sách.        | Thêm chức năng cập nhật sách và gắn UID nhãn mới.                               |
|   4 | Chưa có trả sách thủ công.                         | Cho phép thủ thư tìm cuốn sách và xác nhận trả khi nhãn RFID bị hỏng hoặc mất.  |
|   6 | Chưa có nhật ký thao tác.                          | Ghi người sửa dữ liệu, kiểm tra sách, tạo/hủy/miễn phạt và thời gian thực hiện. |
|   7 | Xóa sách có thể ảnh hưởng lịch sử mượn.            | Dùng xóa mềm hoặc trạng thái ngừng sử dụng thay vì xóa cứng.                    |
|   8 | ISBN chưa phân biệt đầu sách với từng bản sao.     | Mỗi bản sao vật lý cần có `copyCode` và RFID riêng.                             |
|   9 | MQTT công khai và topic dễ đoán.                   | Sử dụng xác thực, topic riêng hoặc broker riêng.                                |
|  10 | Một số đoạn `catch (_err)` lại sử dụng biến `err`. | Thống nhất tên biến để xử lý lỗi không phát sinh thêm lỗi.                      |

## 3. Luồng mượn sách

1. Độc giả chọn chức năng **Mượn sách**.
2. Độc giả quét thẻ RFID cá nhân.
3. Backend kiểm tra:
   - Thẻ tồn tại và độc giả đang hoạt động.
   - Độc giả không bị khóa.
   - Không có sách quá hạn.
   - Không có khoản nợ đang ngăn quyền mượn.
   - Chưa vượt quá số sách được phép mượn.
4. Độc giả quét từng cuốn sách.
5. Hệ thống kiểm tra sách tồn tại và đang ở trạng thái `available`.
6. Sách chỉ được thêm vào danh sách chờ mượn, chưa cập nhật database.
7. Người dùng có thể bỏ cuốn sách bị quét nhầm khỏi danh sách.
8. Người dùng bấm **Xác nhận mượn**.
9. Backend thực hiện toàn bộ lượt mượn trong một transaction:
   - Tạo các bản ghi mượn.
   - Lưu ngày mượn và hạn trả.
   - Chuyển sách từ `available` sang `borrowed`.
10. Khi backend xác nhận thành công, ESP32 bật LED xanh và còi báo.
11. Nếu giao dịch thất bại, không cuốn nào bị cập nhật và ESP32 bật LED đỏ.

## 4. Luồng trả sách tự động

### 4.1. Người đọc trả sách tại kiosk

1. Người dùng chọn chức năng **Trả sách**.
2. Không bắt buộc quét thẻ độc giả.
3. Người dùng quét nhãn RFID của từng cuốn sách.
4. Backend tìm lượt mượn đang hoạt động của cuốn sách.
5. Sách được thêm vào danh sách chờ trả, chưa cập nhật database.
6. Nếu quét nhầm, người dùng có thể loại bỏ sách khỏi danh sách.
7. Người dùng bấm **Hoàn thành trả sách**.
8. Backend xử lý toàn bộ danh sách trong một transaction:
   - Ghi nhận thời gian trả thực tế.
   - Kết thúc lượt mượn.
   - Dừng tính ngày quá hạn tại đúng thời điểm trả.
   - Tạo khoản phạt quá hạn nếu có.
   - Chuyển sách từ `borrowed` sang `pending_inspection`.
9. Màn hình thông báo: **Đã tiếp nhận sách – chờ thủ thư kiểm tra**.
10. ESP32 bật LED xanh và còi sau khi backend xác nhận thành công.

Việc thủ thư kiểm tra muộn không làm tăng số ngày quá hạn vì thời gian trả đã được ghi nhận tại kiosk.

### 4.2. Trường hợp trả thất bại

Hệ thống từ chối và bật LED đỏ khi:

- RFID không thuộc cuốn sách nào.
- Sách không có lượt mượn đang hoạt động.
- Sách đã được ghi nhận trả trước đó.
- Database hoặc backend gặp lỗi.

Không được cập nhật một phần giao dịch khi người dùng trả nhiều cuốn sách.

## 5. Luồng thủ thư kiểm tra sách sau khi trả

Trang quản trị cần có mục **Sách chờ kiểm tra**, hiển thị:

- Tên sách và mã bản sao.
- Người vừa mượn/trả.
- Thời điểm mượn, hạn trả và thời điểm trả.
- Tiền phạt quá hạn, nếu có.
- Tình trạng sách lúc cho mượn hoặc ghi chú cũ, nếu có.

Thủ thư kiểm tra thực tế và chọn một kết quả:

| Kết quả                         | Trạng thái mới của sách | Xử lý                                                          |
| ------------------------------- | ----------------------- | -------------------------------------------------------------- |
| Bình thường                     | `available`             | Cho phép mượn tiếp, không tạo thêm khoản phạt.                 |
| Hỏng nhẹ nhưng vẫn sử dụng được | `available`             | Có thể tạo khoản phạt hư hỏng và ghi chú tình trạng.           |
| Cần sửa chữa                    | `maintenance`           | Tạm ngừng cho mượn; có thể tạo khoản phạt.                     |
| Hư hỏng nặng                    | `damaged`               | Không cho mượn; tạo khoản bồi thường nếu xác định trách nhiệm. |
| Mất sách                        | `lost`                  | Tạo khoản bồi thường và giữ sách ở trạng thái mất.             |
| Chưa xác định được trách nhiệm  | `maintenance`           | Chờ quản lý xử lý, chưa tự động phạt độc giả.                  |

Nếu tạo khoản phạt hư hỏng, thủ thư nhập:

- Loại hư hỏng: rách bìa, mất trang, viết/vẽ, ngấm nước hoặc loại khác.
- Mô tả chi tiết.
- Số tiền phạt/bồi thường.
- Ảnh minh chứng nếu hệ thống hỗ trợ.
- Người kiểm tra và thời gian kiểm tra.

## 6. Nghiệp vụ tiền phạt

### 6.1. Các loại tiền phạt

| Loại     | Người/hệ thống quyết định | Cách xử lý                                           |
| -------- | ------------------------- | ---------------------------------------------------- |
| Quá hạn  | Hệ thống tự tính          | Tính từ hạn trả đến thời điểm kiosk ghi nhận đã trả. |
| Hư hỏng  | Thủ thư xác nhận          | Nhập loại hỏng, mô tả và số tiền.                    |
| Mất sách | Thủ thư xác nhận          | Nhập mức bồi thường theo giá/quy định của thư viện.  |

Tiền phạt tổng có thể gồm:

```text
Tổng tiền phạt = Phạt quá hạn + Phạt hư hỏng + Bồi thường mất sách
```

### 6.2. Trạng thái khoản phạt

- `pending`: mới tạo, chờ xử lý.
- `unpaid`: đã xác nhận và chưa thanh toán.
- `paid`: đã thanh toán.
- `waived`: được thủ thư/quản lý miễn.
- `disputed`: độc giả đang khiếu nại.
- `cancelled`: khoản phạt được tạo nhầm và đã hủy.

### 6.3. Quy tắc quan trọng

- Sách vẫn được ghi nhận đã trả dù độc giả chưa thanh toán phạt.
- Không tiếp tục tính quá hạn sau thời điểm kiosk tiếp nhận sách.
- Độc giả còn khoản nợ có thể bị chặn mượn mới.
- RFID không thể kết luận sách bị hỏng; phạt hư hỏng phải do thủ thư xác nhận.
- Không tự động quy trách nhiệm nếu không có căn cứ về tình trạng sách trước khi cho mượn.
- Nếu độc giả khiếu nại, chuyển khoản phạt sang `disputed` thay vì xóa lịch sử.

## 7. Các trạng thái dữ liệu đề xuất

### 7.1. Trạng thái sách

```text
available           Sẵn sàng cho mượn
borrowed            Đang được mượn
pending_inspection  Đã trả, chờ thủ thư kiểm tra
maintenance         Đang sửa chữa hoặc chờ xử lý
damaged             Hư hỏng nặng, không được mượn
lost                Đã ghi nhận mất
inactive            Ngừng sử dụng
```

### 7.2. Trạng thái lượt mượn

```text
borrowing  Đang mượn
returned   Đã trả
overdue    Đang mượn và đã quá hạn
```

Lượt mượn và tình trạng vật lý của sách phải được quản lý riêng. Khi kiosk nhận lại sách, lượt mượn có thể chuyển thành `returned`, còn sách chuyển thành `pending_inspection`.

## 8. Trả sách thủ công

Khi nhãn RFID bị rách, mất hoặc không đọc được:

1. Thủ thư tìm sách theo tên, ISBN, mã bản sao hoặc người đang mượn.
2. Chọn đúng lượt mượn đang hoạt động.
3. Bấm **Trả sách thủ công**.
4. Hệ thống ghi thời điểm trả, tính phạt quá hạn và chuyển sách sang `pending_inspection`.
5. Thao tác phải được ghi vào nhật ký cùng tài khoản thủ thư thực hiện.

## 9. Xử lý thông báo cho độc giả

Sau khi thủ thư phát hiện sách hỏng và tạo khoản phạt:

- Khoản phạt xuất hiện trong tài khoản/lịch sử độc giả.
- Gửi email nếu dịch vụ email đã được cấu hình.
- Nếu chưa cấu hình email, giao diện phải thông báo rõ thay vì báo gửi thành công.
- Lần tiếp theo độc giả quét thẻ, kiosk hiển thị khoản nợ và lý do bị chặn mượn.
- Độc giả có thể yêu cầu thủ thư xem lại hoặc chuyển khoản phạt sang trạng thái `disputed`.

## 10. Thứ tự ưu tiên triển khai

Trong thời gian còn lại, nên thực hiện theo thứ tự:

1. Sửa việc quét sách trả làm cập nhật database ngay.
2. Thêm trạng thái `pending_inspection`.
3. Cho trả sách không cần quét thẻ độc giả.
4. Thêm màn hình **Sách chờ kiểm tra**.
5. Thêm các nút **Bình thường**, **Cần sửa**, **Hư hỏng nặng**.
6. Thêm form tạo khoản phạt hư hỏng.
7. Tách việc nhận lại sách khỏi việc thanh toán phạt.
8. Thêm trả sách thủ công.
9. Bổ sung transaction cho mượn/trả nhiều sách.
10. Sau đó mới hoàn thiện đăng nhập quản trị, nhật ký và bảo mật MQTT.

## 11. Kết luận

Luồng nghiệp vụ cốt lõi của hệ thống gồm ba giai đoạn riêng:

1. **Mượn sách:** xác thực độc giả, quét sách và xác nhận giao dịch.
2. **Trả sách tự động:** kiosk tiếp nhận, kết thúc tính quá hạn và chuyển sách sang chờ kiểm tra.
3. **Kiểm tra sau trả:** thủ thư xác nhận tình trạng vật lý, đưa sách trở lại kho hoặc tạo yêu cầu sửa chữa/bồi thường.

Cách tổ chức này vẫn giữ được tính tự phục vụ của hệ thống IoT, đồng thời xử lý đúng các trường hợp sách rách, hỏng hoặc mất mà RFID không thể tự phát hiện.
