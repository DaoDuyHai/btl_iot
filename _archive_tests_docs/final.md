# VAI TRÒ VÀ MỤC TIÊU

Bạn là kỹ sư AI. Nâng cấp module AI Search (dạng RAG) của Smart Library Kiosk để gợi ý
sách chính xác cho CẢ câu hỏi cụ thể LẪN câu mơ hồ/cảm xúc/ngữ cảnh bằng tiếng Việt.
Ví dụ phải làm tốt: "Hôm nay tôi đang rất mệt, tôi muốn có cuốn sách giúp tôi thư giãn".
Làm từ đầu đến cuối, tự kiểm chứng bằng số liệu thật, không báo "xong" khi chưa chạy kiểm tra.

# BỐI CẢNH VÀ RÀNG BUỘC

- Dataset: cleaned_books_dataset.csv, 3000 sách tiếng Việt. Cột: Book_ID, Title, Author,
  Category (9 nhóm), Subcategory (106 nhóm), Description, Keywords, Publisher,
  Publication_Year, Language, Shelf, Floor, Position, Total_Copies, Available_Copies.
- Kiosk đã có RFID và MQTT. AI Search là module ĐỘC LẬP, không sửa, không làm hỏng chúng.
- Model nền: intfloat/multilingual-e5-small (pretrained). Bắt buộc: prefix "passage: " cho
  sách, "query: " cho câu hỏi, normalize_embeddings=True, cache embedding ra file,
  cosine similarity. Không cần vector DB (3000 sách dùng numpy/FAISS-flat là đủ), không cần
  knowledge graph, không nhét cả dataset vào prompt.
- Kiến trúc là RAG: câu hỏi -> tìm Top 10 sách thật -> (tùy chọn) LLM chỉ được dựa vào 10 sách
  đó để viết câu trả lời. Phần tìm kiếm phải chạy offline, không phụ thuộc LLM; LLM chỉ là
  lớp tùy chọn.
- Tôi đã train/fine-tune dở và kết quả chưa tốt: câu cụ thể trả lời được, câu mơ hồ thì không.
  Nguyên nhân gốc: câu hỏi nói về TRẠNG THÁI người đọc, Description sách nói về NỘI DUNG,
  hai bên không có từ chung; Description lẫn trích dẫn/quảng cáo; Keywords có từ rác.
  Không giải quyết bằng cách train thêm trước.

# BƯỚC 0 - ĐỌC HIỆN TRẠNG

Đọc code AI Search, code train dở, cache, test set (nếu có). Không xóa code train cũ,
chuyển vào thư mục experimental/. Chạy baseline E5 thuần với 20 câu mơ hồ + 20 câu cụ thể,
lưu kết quả để so sánh. Báo cáo ngắn: đang có gì, lỗi ở đâu.

# BƯỚC 1 - LÀM GIÀU DỮ LIỆU SÁCH (chạy 1 lần, cache)

Tạo books_enriched.csv, giữ nguyên cột cũ, thêm:

- clean_description (bỏ trích dẫn tiếng Anh, quảng cáo, tên NXB)
- summary_vi (1-2 câu "Sách nói về ..., phù hợp với ...", chỉ dựa trên dữ liệu, không bịa)
- mood_tags (từ danh sách cố định: thư giãn, nhẹ nhàng, chữa lành, vui vẻ, hài hước, cảm động,
  hồi hộp, suy ngẫm, truyền cảm hứng, nghiêm túc, nặng đầu...)
- reader_intent (giải trí, học tập, nâng cao kỹ năng, tìm cảm hứng, đọc cùng con, ôn thi, tra cứu)
- reading_effort (nhẹ / vừa / nặng), audience (trẻ em, học sinh, sinh viên, người đi làm, mọi người)
- search_text = Title + Author + Category + Subcategory + summary_vi + mood_tags + reader_intent
  Ưu tiên rule-based (từ điển Category/Subcategory -> mood/effort/audience, bổ sung bằng từ khóa
  trong Description). Nếu có LLM API thì sinh summary_vi/mood_tags theo lô nhỏ, có cache, retry,
  kiểm tra JSON hợp lệ. Nếu không có API thì ghi rõ phần nào là rule-based, không giả vờ.
  Kiểm tra: in 30 sách ngẫu nhiên, đối chiếu nhãn với Description, báo tỷ lệ hợp lý.

# BƯỚC 2 - HIỂU CÂU HỎI

1. Phân loại intent: (a) sách cụ thể (tên/tác giả), (b) theo chủ đề, (c) theo cảm xúc/ngữ cảnh/
   mục đích (mơ hồ), (d) hỏi vị trí/tình trạng sách, (e) ngoài phạm vi.
2. Với (c): sinh 3-5 truy vấn mở rộng mô tả loại sách phù hợp, ví dụ "tôi mệt, muốn thư giãn" ->
   ["sách nhẹ nhàng dễ đọc để thư giãn", "tản văn chữa lành", "truyện ngắn ấm áp cảm động"];
   kèm danh sách "nên tránh" (sách nặng/kỹ thuật) dùng làm hệ số phạt mềm, KHÔNG loại cứng.
3. Trích bộ lọc rõ ràng nếu có (Category, năm, còn hàng, tác giả).
4. Bắt buộc có đường chạy KHÔNG cần LLM: từ điển cảm xúc/ngữ cảnh tiếng Việt (mệt, stress, buồn,
   chán, mất ngủ, rảnh cuối tuần, đọc cho con, mới bắt đầu, ôn thi, mất động lực...) ánh xạ sang
   mood_tags + reading_effort + Category ưu tiên. Chịu được không dấu, viết tắt, sai chính tả.
   Nếu có LLM thì dùng thêm và hợp nhất với từ điển.

# BƯỚC 3 - TÌM KIẾM LAI

- E5 trên search_text + BM25 trên search_text/Title/Author.
- Câu mơ hồ: chạy từng truy vấn mở rộng, gộp bằng Reciprocal Rank Fusion.
- Rerank nhẹ: cộng điểm khi khớp mood_tags/reading_effort, trừ điểm sách "nặng" khi người dùng
  mệt, ưu tiên Available_Copies > 0 (sách hết vẫn có thể hiện nhưng xếp sau và ghi rõ hết).
- Trả Top 5/Top 10 kèm điểm, đảm bảo đa dạng (không 5 cuốn cùng tác giả/nhóm).
- Mỗi kết quả: Book_ID, Title, Author, lý do khớp, Floor/Shelf/Position, số bản còn.

# BƯỚC 4 - TRẢ LỜI

- Câu mơ hồ: LUÔN trả ngay 3-5 gợi ý tốt nhất, không trả "tôi không hiểu" thay cho kết quả.
  Có thể thêm đúng 1 câu hỏi làm rõ SAU danh sách.
- Mỗi gợi ý: tên, tác giả, 1-2 câu vì sao hợp với trạng thái người dùng, vị trí, tình trạng.
- Chỉ nói "thư viện chưa có sách phù hợp" khi điểm tìm kiếm thật sự thấp (hiệu chỉnh ngưỡng bằng
  test set) hoặc câu ngoài phạm vi. Tuyệt đối không bịa sách ngoài dữ liệu.

# BƯỚC 5 - SINH DỮ LIỆU TEST/HUẤN LUYỆN (QUY TẮC CHỐNG TRÙNG LẶP)

CẤM: dùng vòng lặp/template nhân bản câu hỏi (ghép "Tôi muốn tìm sách {category}" rồi lặp),
cấm copy một câu rồi chỉ đổi tên sách/thể loại, cấm báo số lượng chung chung.
CÁCH SINH:

- Sinh theo TỪNG SÁCH: chọn ngẫu nhiên có phân tầng, phủ đủ 9 Category và >= 60% Subcategory;
  mỗi sách được chọn viết 1-3 câu hỏi dựa trên Description/mood_tags của chính sách đó.
- Mỗi câu gắn nhãn "kiểu hỏi" (tên sách, tác giả, chủ đề, cảm xúc, mục đích, hoàn cảnh,
  so sánh "giống cuốn X", có điều kiện, câu cụt/không dấu, câu dài kể lể, sai chính tả) và
  "vai" (học sinh, sinh viên, người đi làm bận, phụ huynh, người lớn tuổi, người mới đọc,
  người mất ngủ...), phân bố không lệch quá 20%.
- Sinh theo lô 10-15 sách; mỗi lô đưa 30 câu gần nhất vào và yêu cầu không lặp/không diễn đạt lại.
- Câu cảm xúc phải có >= 8 cách diễn đạt khác nhau ("đầu óc rối", "chán đời", "áp lực deadline",
  "muốn trốn khỏi thực tại"...).
- Làm thử 100 câu trước, qua kiểm tra mới nhân lên.
  KIỂM TRA (viết script, in kết quả; thất bại thì sinh lại phần lỗi):
- Câu duy nhất = 100% sau chuẩn hóa; loại cặp gần trùng (cosine E5 "query:" > 0.92);
  sau khi loại phải còn >= 90% mục tiêu.
- Không quá 3% câu bắt đầu bằng cùng 3 từ đầu; độ dài phân bố rộng (3 đến 30 từ).
- Mỗi Book_ID làm đáp án tối đa 3 lần, phủ >= 800 sách khác nhau.
- In 30 câu ngẫu nhiên + bảng phân bố theo kiểu hỏi/vai/Category để tôi đọc.
- Tách train/validation/test theo Book_ID, không câu nào xuất hiện ở hai tập.

# BƯỚC 6 - ĐÁNH GIÁ

Test set riêng, tối thiểu 150 câu, không dùng lại câu đã dùng khi viết từ điển/nhãn:
50 câu cụ thể (có Book_ID đúng), 50 câu chủ đề, 40 câu mơ hồ/cảm xúc/ngữ cảnh,
10+ câu ngoài phạm vi/không có đáp án.
Câu mơ hồ không có "một đáp án đúng": ghi nhãn tập Category/mood_tags chấp nhận được và tập
KHÔNG phù hợp.
Chỉ số: Recall@5, Recall@10, MRR (câu cụ thể/chủ đề); Acceptable-Hit@5 và Bad-Hit@5
(câu mơ hồ, ví dụ gợi ý sách lập trình cho người đang mệt là lỗi); tỷ lệ từ chối đúng
(câu ngoài phạm vi); thời gian phản hồi trung bình và p95.
So sánh 4 cấu hình: E5 thuần / BM25 / hybrid / hybrid + enrichment + query understanding.
Viết AI_SEARCH_REPORT.md: bảng số liệu, 15 ví dụ thất bại và nguyên nhân,
dung lượng cache, hướng dẫn chạy lại.


# BƯỚC 7 - CHỈ FINE-TUNE NẾU CẦN

Chỉ khi cấu hình đầy đủ ở Bước 6 vẫn chưa đạt. Tạo cặp (câu hỏi -> sách) từ dữ liệu đã làm giàu
và đã qua kiểm tra chống trùng, tách train/val theo sách, so sánh trên cùng test set với bản
chưa fine-tune; chỉ dùng bản fine-tune nếu thắng rõ ràng, ngược lại giữ pretrained và giải thích.

# TIÊU CHÍ HOÀN THÀNH

- Câu "Hôm nay tôi đang rất mệt, tôi muốn có cuốn sách giúp tôi thư giãn" trả 5 sách nhẹ nhàng/
  thư giãn/chữa lành, không có sách kỹ thuật nặng, kèm vị trí kệ và tình trạng.
- Acceptable-Hit@5 (câu mơ hồ) >= 80%, Bad-Hit@5 <= 5%, Recall@5 câu cụ thể không giảm so
  với baseline.
- Module độc lập, RFID/MQTT không bị ảnh hưởng, chạy lại được, không hardcode đáp án theo test set.
- Báo cáo trung thực, kể cả khi số liệu chưa đạt.

# CÁCH LÀM VIỆC

Làm tuần tự, cuối mỗi bước in kết quả kiểm tra thật. Gặp điểm chưa chắc thì chọn phương án
đơn giản nhất, ghi giả định vào báo cáo. Chỉ hỏi lại tôi khi bị chặn hoàn toàn.
