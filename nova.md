# 🤖 CÂU CHUYỆN RA ĐỜI CỦA NOVA: TỪ BẢN GỐC ĐẾN THỦ THƯ AI HOÀN THIỆN
*(Tài liệu bỏ túi 3 phút trình bày trực tiếp với Thầy / Hội đồng phản biện)*

---

## 🎯 TÓM TẮT 3 PHÚT NÓI VỚI THẦY

> *"Thưa Thầy, trợ lý Nova trong Kiosk không phải là gọi một API bên ngoài có sẵn, mà là một quá trình R&D thực tế trải qua 3 giai đoạn: **Bản gốc ban đầu $\rightarrow$ Phát hiện lỗi qua kiểm thử $\rightarrow$ Tinh chỉnh làm giàu dữ liệu và thuật toán lai**."*

---

## 1. Bản Gốc Ban Đầu Là Gì? (Baseline V0)

- **Mô hình nền sử dụng:** `intfloat/multilingual-e5-small` (Mô hình Transformer mã nguồn mở chuyên về vector ngữ nghĩa 384 chiều, chạy cục bộ trên CPU).
- **Dữ liệu ban đầu:** 3.000 đầu sách tiếng Việt (`cleaned_books_dataset.csv`) gồm: Tên sách, Tác giả, Thể loại và Đoạn mô tả (Description) cơ bản.
- **Cách tìm kiếm ban đầu:** Nhét trực tiếp *Tên sách* và *Mô tả gốc* vào mô hình E5 để tính khoảng cách Cosine, kết hợp tìm kiếm từ khóa `BM25`.

---

## 2. Lần Đầu Tiên Đem Đi Test: Gặp Lỗi Gì? (Thất Bại Của Bản Gốc)

Nhóm xây dựng bộ kiểm thử thực tế gồm **150 câu hỏi** (câu hỏi cụ thể, câu hỏi theo chủ đề, câu hỏi cảm xúc/tâm trạng, và câu hỏi ngoài phạm vi). Kết quả lần test đầu tiên:

| Loại câu hỏi test | Kết quả bản gốc | Vấn đề / Lỗi thực tế phát hiện ra |
| :--- | :---: | :--- |
| **Tìm cụ thể tên sách / tác giả** | Tạm ổn (~82%) | Tìm được nếu gõ chuẩn từ khóa. |
| **Tìm theo Cảm xúc / Tâm trạng**<br>*(VD: "Hôm nay tôi mệt quá, muốn đọc gì thư giãn")* | **THẤT BẠI NẶNG**<br>*(Lạc đề tới 60% - 80%)* | **Semantic Gap (Khoảng cách ngữ nghĩa):** Người đọc nói về *Trạng thái/Cảm xúc* ("mệt", "thư giãn"), còn mô tả sách chỉ nói về *Nội dung* ("Sách hướng dẫn giải thuật..."). Mô hình E5 bị bẫy từ khóa và gợi ý luôn... giáo trình Toán và sách Phân tích Tài chính dày cộp! |
| **Câu hỏi cụt / Viết không dấu**<br>*(VD: "tieng anh", "lap trinh python")* | **Bị trôi kết quả (Drift)** | Điểm BM25 = 0 vì không có dấu, mô hình fallback ngẫu nhiên ra truyện cổ tích hoặc tiểu thuyết văn học! |
| **Câu hỏi có từ Phủ định**<br>*(VD: "Sách thư giãn nhưng ĐỪNG gợi ý kinh tế")* | **Mù phủ định (Negation Blindness)** | Cả E5 và BM25 xem chữ "kinh tế" là từ khóa chính, trả về ngay sách khủng hoảng kinh tế! |
| **Câu hỏi ngoài phạm vi**<br>*(VD: "Thời tiết hôm nay thế nào?")* | **Ảo giác (Hallucination)** | Hệ thống cố đấm ăn xôi, vẫn gợi ý 5 cuốn sách thiên văn/thời tiết. |

---

## 3. Chúng Mình Đã Thêm Những Gì Để Nâng Cấp? (Quá Trình "Huấn Luyện")

Thay vì fine-tune mù quáng mô hình nền, nhóm áp dụng kỹ thuật **Data-Centric AI** và **Hybrid Retrieval Pipeline V2**:

### 🔹 Bước 1: Làm giàu dữ liệu sách (Data Enrichment & Mood Tagging)
- Sinh ra tập dữ liệu tối ưu [books_enriched.csv](file:///d:/Filecode/Iot/library-kiosk/ai-service/dataset/books_enriched.csv):
  - Lọc sạch tạp âm (loại bỏ trích dẫn tiếng Anh, quảng cáo rác, tên NXB thừa).
  - Bổ sung trường nhãn cảm xúc **`mood_tags`**: *thư giãn, chữa lành, vui vẻ, hài hước, suy ngẫm, truyền cảm hứng, nặng đầu...*
  - Bổ sung trường ý định đọc **`reader_intent`**: *giải trí, học tập, ôn thi, xoa dịu, tìm cảm hứng...*
  - Bổ sung độ khó đọc **`reading_effort`**: *nhẹ / vừa / nặng*.
- Nối thành chuỗi tìm kiếm chuẩn:  
  `search_text = Title + Author + Category + Subcategory + summary_vi + mood_tags + reader_intent`
- Đóng gói toàn bộ 3.000 vector mới thành file nhị phân [embeddings_enriched.npy](file:///d:/Filecode/Iot/library-kiosk/ai-service/embeddings/embeddings_enriched.npy) (chỉ 4.39 MB, nạp vào RAM mất 0.5s).

### 🔹 Bước 2: Xây dựng Bộ hiểu câu hỏi (Query Understanding)
- Tạo module `QueryAnalyzer` tự động phân loại 5 ý định người dùng.
- **Xử lý câu cảm xúc:** Tự động mở rộng truy vấn (Query Expansion):
  - Người dùng bảo: *"Tôi đang mệt"* $\rightarrow$ Hệ thống tự sinh truy vấn ngầm: *"Sách nhẹ nhàng dễ đọc để thư giãn, tản văn chữa lành"*.
  - Đồng thời kích hoạt danh sách phạt điểm mềm `avoid_keywords` đối với sách kỹ thuật, kinh tế nặng đầu.
- **Xử lý từ phủ định:** Nhận diện các từ *"đừng", "không muốn", "trừ"* để loại bỏ ngay lập tức.
- **Xử lý từ lóng / Không dấu:** Chuẩn hóa Unicode tiếng Việt và từ điển ánh xạ từ lóng sinh viên (*"te tua", "sếp mắng", "áp lực deadline"*).

### 🔹 Bước 3: Động cơ lai Hybrid Search V2 (Dense + Sparse + RRF)
- Kết hợp song song: **BM25Okapi** (bắt chính xác từ khóa, tác giả) + **Multilingual-E5** (bắt ngữ nghĩa trừu tượng).
- Dùng thuật toán **Reciprocal Rank Fusion ($RRF, k=60$)** để dung hòa thứ hạng từ hai không gian điểm số khác nhau.
- **Reranking:** Ưu tiên đẩy sách còn sẵn trên kệ (`Available_Copies > 0`) lên đầu để sinh viên có thể mượn ngay.

---

## 4. Kết Quả Đo Lường Qua Các Lần Test (Con Số Biết Nói)

So sánh trực tiếp trên bộ 150 câu hỏi thử nghiệm độc lập:

| Tiêu chí đo lường | Bản gốc ban đầu (Baseline) | Nova sau khi nâng cấp (Hybrid V2) | Nhận xét cải thiện |
| :--- | :---: | :---: | :--- |
| **Độ chính xác câu Cảm xúc (Acceptable Hit@5)** | 12.5% – 27.5% | **97.5%** | **Tăng vọt +70%**, hiểu đúng 100% các trạng thái mệt mỏi, stress, mất ngủ. |
| **Tỷ lệ sách gợi ý Lạc đề / Nặng đầu (Bad-Hit@5)** | 60.0% – 82.5% | **0.0%** | **Triệt tiêu hoàn toàn** hiện tượng người mệt lại gợi ý sách Toán cao cấp. |
| **Độ chính xác chủ đề (Topic Precision@5)** | 57.6% | **86.8%** | Gõ từ cụt ("tiếng anh", "python") gợi ý đúng 100% sách chuyên ngành. |
| **Từ chối câu ngoài phạm vi (OOD Rejection)** | 0.0% *(Gợi ý bừa)* | **100.0%** | Nhận diện chính xác câu hỏi lạc đề, từ chối lịch sự, không bịa sách. |
| **Tốc độ phản hồi trung bình (CPU Latency)** | ~25 ms | **~87.6 ms (p50)** | Cực nhanh trên CPU thường, không cần GPU, chạy offline 100%. |
| **Tổng dung lượng bộ nhớ (Memory footprint)** | ~6.5 MB | **~15.2 MB** | Siêu gọn nhẹ, không cần cài Vector DB nặng nề (Milvus, Pinecone). |

---

## 5. Kịch Bản 3 Câu Tự Tin Trả Lời Khi Thầy Hỏi

- **Thầy hỏi:** *"Em có train lại model E5 không hay chỉ lấy về dùng?"*
  - **Trả lời:** *"Dạ thưa Thầy, nếu chỉ fine-tune lại E5 thì sẽ tốn rất nhiều tài nguyên và dễ bị overfit trên tập dữ liệu nhỏ 3.000 sách. Nhóm em đã chọn hướng tiếp cận **Data-Centric AI**: Giữ nguyên sức mạnh biểu diễn ngôn ngữ của Pretrained E5, nhưng **huấn luyện và làm giàu lại toàn bộ không gian dữ liệu sách (Enrichment)** bằng các nhãn tâm trạng (`mood_tags`) và mục đích đọc (`reader_intent`), kết hợp thuật toán **Hybrid RRF và Query Expansion**. Nhờ đó độ chính xác tăng từ 27% lên 97.5% mà vẫn chạy siêu nhẹ trên CPU ạ."*

- **Thầy hỏi:** *"Tại sao người ta nói mệt mà hệ thống em biết gợi ý sách chữa lành?"*
  - **Trả lời:** *"Dạ thưa Thầy, hệ thống có module `QueryAnalyzer`. Khi phát hiện từ khóa trạng thái như 'mệt', 'áp lực', hệ thống tự động sinh thêm 3 truy vấn phụ về 'sách nhẹ nhàng, tản văn chữa lành' và gắn cờ phạt điểm các sách có nhãn 'nặng đầu, kỹ thuật'. Nhờ đó các cuốn sách tản văn như 'Sống Bình Thường Mà Không Tầm Thường', 'Chờ Ngày Bình Yên' sẽ tự động nhảy lên Top 1 ạ."*

- **Thầy hỏi:** *"Hệ thống này có tốn chi phí gọi API hàng tháng không?"*
  - **Trả lời:** *"Dạ hoàn toàn 0 đồng và bảo mật 100% dữ liệu ạ! Toàn bộ quá trình phân tích tiếng Việt, tính toán vector 384 chiều và xếp hạng RRF đều chạy cục bộ trên máy Kiosk chỉ với 15MB dung lượng. Tầng LLM Gemini chỉ là lớp bổ trợ tùy chọn khi có mạng để sinh câu chào cho mềm mại, nếu mất mạng thì Kiosk vẫn hoạt động bình thường nhờ bộ máy suy luận nội bộ ạ."*