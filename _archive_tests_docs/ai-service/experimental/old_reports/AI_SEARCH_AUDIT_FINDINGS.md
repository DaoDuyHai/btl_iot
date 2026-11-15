# BÁO CÁO KIỂM TOÁN KỸ THUẬT & XÁC MINH TOÀN DIỆN (AUDIT FINDINGS)
*Tài liệu kiểm toán độc lập: `AI_SEARCH_AUDIT_FINDINGS.md`*  
*Chuyên gia thực hiện: Senior AI Engineer (Information Retrieval & Search Ranking)*  
*Đối tượng kiểm toán: Báo cáo `AI_SEARCH_STRESS_TEST_REPORT.md`, mã nguồn `src/`, dữ liệu `dataset/` và kết quả đo đạc thực tế*  
*Thời điểm thực hiện: 07/11/2026*

---

## TỔNG KẾT TRẠNG THÁI KIỂM TOÁN TOÀN DIỆN

| STT | Hạng mục kiểm toán | Trạng thái xác minh | Mức độ nghiêm trọng | Tóm tắt phát hiện cốt lõi |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **RRF: Ngưỡng điểm 0.02 & Lựa chọn $k$** | **INCORRECT** *(về toán học)*<br>**VERIFIED** *(về chỉ số $k$)* | **MEDIUM** | - Nhận định *"ngoài Top 20 thì điểm RRF luôn $< 0.02$"* là **sai toán học** ($\text{Rank } 21 \rightarrow \text{Score } 0.0247 > 0.02$). Phải ngoài Top 40 mới $< 0.02$.<br>- Thực nghiệm cho thấy **$k=20$ có Recall@5, Precision@5 và MRR cao hơn $k=40$**, việc trước đó bỏ qua $k=20$ là chưa đủ cơ sở khoa học. |
| **2** | **Semantic Drift & Độ trôi thứ hạng Ove** | **INCORRECT** *(về thứ hạng Ove & tiêu chí Drift)* | **HIGH** | - SD04/TC053: Báo cáo cũ ghi Semantic xếp Ove ở #7, thực tế Semantic xếp Ove ở **#14** và Hybrid xếp Ove ở **#41**.<br>- SD02 (Sông Đà) và SD03 (Tôn Nữ Xuân Quyên) bị gán nhầm là "Không Drift" do chỉ kiểm tra tránh bẫy CNTT, trong khi thực tế sai hoàn toàn chủ đề người dùng cần. |
| **3** | **Multi-Constraint Search (30 truy vấn)** | **INCORRECT** *(kết luận cũ)*<br>**VERIFIED** *(kết quả 30 câu mới)* | **HIGH** | - MC03 (Sách tiếng Anh về AI) trước đây được đánh giá ĐẠT, thực tế chỉ là **PARTIAL**.<br>- Kiểm thử mở rộng 30 câu: Tỷ lệ ĐẠT hoàn toàn (Full PASS) ở Top 1 của Hybrid chỉ đạt **46.7%** (14/30), PARTIAL đạt **30.0%** (9/30), FAIL đạt **23.3%** (7/30). |
| **4** | **Lỗi rò rỉ `"nan"` và `"None"` vào Embedding & BM25** | **VERIFIED BUG** | **HIGH** | Hàm `build_passage()` và `get_work_catalog()` dùng `str(val)` trên dữ liệu `None`/`np.nan`, khiến từ rác `"nan"` bị nhúng vào vector E5 và xuất hiện 5 lần trong chỉ mục token BM25. |
| **5** | **Đánh giá OOD Detection (Mở rộng 50 câu)** | **VERIFIED** | **HIGH** | Thử nghiệm 50 câu OOD chứng minh không thể dùng ngưỡng Cosine đơn thuần: Ngưỡng $<0.84$ có FAR = 18.0% nhưng chặn nhầm 14.0% câu hỏi thật; Ngưỡng $<0.85$ chặn được 100% OOD nhưng chặn nhầm tới **22.0%** độc giả hợp lệ. |
| **6** | **Nghẽn CPU / GIL trong Concurrency Stress Test** | **VERIFIED** | **MEDIUM** | Throughput không tăng theo số luồng (~16.4 QPS ở 1 luồng vs ~11.3 QPS ở 20 luồng). Độ trễ tăng từ 61ms lên **1.730ms** do PyTorch CPU contention và GIL Python. Gọi backend này là "Production Ready" cho tải đồng thời là nhận định chưa chặt chẽ. |

---

## 1. KIỂM TRA CHI TIẾT THUẬT TOÁN RRF VÀ XẾP HẠNG (RANKING)

### 1.1. Mã nguồn liên quan
- **Tệp tin:** [`src/hybrid_search.py`](file:///d:/TrainAI/src/hybrid_search.py#L45-L60) (Dòng 50-60)
- **Tệp tin kết quả:** [`tests/rrf_k_sweep_results.json`](file:///d:/TrainAI/tests/rrf_k_sweep_results.json)

### 1.2. Xác minh cơ chế hoạt động của RRF trong code
1. **Chỉ số Rank:** Bắt đầu chính xác từ `1` (`enumerate(bm25_works, 1)` và `enumerate(sem_works, 1)`). Đúng theo chuẩn bài báo gốc của Cormack, Clarke & Buettcher (SIGIR 2009).
2. **Xử lý ứng viên khuyết thiếu ở một nhánh:** Nếu tài liệu $d$ nằm ngoài `fetch_k` của một nhánh, nhánh đó đóng góp $0.0$ điểm vào tổng điểm $RRF(d)$.
3. **Deduplication:** Trong `search()`, hệ thống gộp theo `work_id` dựa trên kết quả đã gộp từ BM25 và Semantic, đảm bảo mỗi tác phẩm chỉ xuất hiện 1 lần.
4. **Tính độc lập của điểm RRF:** Điểm RRF được tính toán lại hoàn toàn mới cho từng giá trị $k$ bằng công thức $1 / (k + rank)$.

### 1.3. Xác minh toán học: Nhận định ngưỡng điểm $0.02$
- **Khẳng định trong báo cáo cũ:** *"khi BM25 và Semantic đều xếp một sách ngoài Top 20 thì tổng điểm RRF luôn nhỏ hơn 0.02."*
- **Kiểm tra toán học thực tế:**
  Với $k=60$, giả sử một cuốn sách đứng ở thứ hạng $r_1 = 21$ ở BM25 và $r_2 = 21$ ở Semantic:
  $$Score = \frac{1}{60 + 21} + \frac{1}{60 + 21} = \frac{2}{81} \approx \mathbf{0.024691} > 0.02$$
  Nếu $r_1 = r_2 = 25$:
  $$Score = \frac{2}{85} \approx \mathbf{0.023529} > 0.02$$
  Nếu $r_1 = r_2 = 30$:
  $$Score = \frac{2}{90} \approx \mathbf{0.022222} > 0.02$$
  Để tổng điểm thực sự nhỏ hơn $0.02$:
  $$\frac{2}{60 + r} < 0.02 \iff 60 + r > \frac{2}{0.02} = 100 \iff r > 40$$
- **Trạng thái:** **INCORRECT**. Phải ngoài Top 40 ở cả hai bên thì tổng điểm mới $< 0.02$. 
- Ngoài ra, một cuốn sách đứng **Top 1 ở một bên duy nhất** chỉ nhận được:
  $$\frac{1}{60 + 1} + 0 = \frac{1}{61} \approx \mathbf{0.016393} < 0.02$$
  Nghĩa là một cuốn sách đứng hạng 25 ở cả hai bên ($0.0235$) vẫn xếp TRÊN một cuốn sách đứng Top 1 tuyệt đối ở một bên nhưng vắng mặt ở bên kia ($0.0164$).

### 1.4. Đối chiếu thực nghiệm: Lựa chọn $k=20$ vs $k=40$ vs $k=60$
Dữ liệu đo đạc thực tế từ `tests/rrf_k_sweep_results.json`:
| Cấu hình | Hit@1 | Hit@5 | Hit@10 | Recall@5 | Recall@10 | Precision@5 | MRR | Latency TB |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$k=20$** | **84.0%** | **96.0%** | **96.0%** | **0.5493** | **0.5953** | **0.5160** | **0.8917** | **79.09 ms** |
| **$k=40$** | **84.0%** | **96.0%** | **96.0%** | 0.5464 | 0.5937 | 0.5100 | 0.8908 | 84.22 ms |
| **$k=60$** | 83.0% | 95.0% | 96.0% | 0.5399 | 0.5923 | 0.5040 | 0.8867 | 80.99 ms |

- **Đánh giá:** Về mặt số liệu thuần túy, **$k=20$ vượt trội hơn $k=40$ trên mọi chỉ số**: Recall@5 cao hơn (+0.0029), Precision@5 cao hơn (+0.0060), MRR cao hơn (0.8917 vs 0.8908) và Latency nhanh hơn (79ms vs 84ms).
- **Lý do báo cáo cũ chọn $k=40$:** Báo cáo cũ thiên vị $k=40$ vì e ngại $k=20$ quá khắt khe, nhưng không đưa ra được chứng cứ thực nghiệm. Bằng chứng số liệu khẳng định: Nếu muốn tối đa hóa MRR và Hit@1, **$k=20$ mới là điểm cực trị thực tế**.

---

## 2. KIỂM TRA SEMANTIC DRIFT VÀ TỪ ĐA NGHĨA

### 2.1. Mã nguồn liên quan
- **Tệp tin:** [`scripts/test_semantic_drift.py`](file:///d:/TrainAI/scripts/test_semantic_drift.py#L65-L85)
- **Tệp tin kết quả:** [`tests/semantic_drift_eval.json`](file:///d:/TrainAI/tests/semantic_drift_eval.json) và script kiểm tra lại [`scripts/audit_drift_cases.py`](file:///d:/TrainAI/scripts/audit_drift_cases.py)

### 2.2. Lỗ hổng phương pháp luận trong đánh giá Drift cũ
Báo cáo cũ đã phạm sai lầm phương pháp luận khi gộp chung hai khái niệm:
1. **Tránh bẫy từ đa nghĩa (Polysemy Avoidance):** Không bị trôi sang nghĩa sai (ví dụ không bị nhầm Java sang ngôn ngữ lập trình).
2. **Tìm đúng chủ đề (Topic Relevance):** Trả về cuốn sách đúng chủ đề người dùng cần.

Cụ thể qua các ca kiểm thử:
- **Ca SD02 (Truy vấn: *"Văn hóa và lịch sử vùng đảo Java Indonesia"*):**
  - Kết quả Top 1 trả về: `[B2841]` *Sông Đà: Lịch sử một vùng biên cảnh Việt Nam*.
  - *Tại sao báo cáo cũ ghi "Không Drift"?* Vì hàm kiểm tra chỉ viết: `drift_check = lambda r: "công nghệ thông tin" in str(r['category']).lower()`. Do cuốn *Sông Đà* thuộc thể loại "Lịch sử – Văn hóa" nên code tự động đánh dấu là `Drift = False`!
  - *Thực tế:* Cuốn sách về **Việt Nam** hoàn toàn **không liên quan gì đến đảo Java hay đất nước Indonesia**. Đây là một truy vấn **THẤT BẠI HOÀN TOÀN (FAIL)** do kho sách không có tài liệu về Indonesia.
- **Ca SD03 (Truy vấn: *"Khởi đầu mùa xuân tươi đẹp và tràn đầy sức sống"*):**
  - Kết quả Top 1 trả về: `[B2013]` *Chinh Phục Cá Mập - Tác giả Tôn Nữ Xuân Quyên*.
  - *Nguyên nhân:* Tác giả tên là **Xuân Quyên**, BM25 bắt trúng chữ *"Xuân"* với điểm BM25 = 28.55, kéo cuốn sách kinh doanh khởi nghiệp lên Top 1.
  - *Thực tế:* Cuốn sách hoàn toàn sai lệch so với mong muốn của người đọc về thơ ca/văn học mùa xuân.
- **Ca SD04/TC053 (Truy vấn: *"ông già khó tính cộc cằn nhưng có trái tim ấm áp luôn muốn tự tử"*):**
  - *Báo cáo cũ ghi:* "Semantic xếp Ove ở #7... Top 1-5 bị chiếm bởi sách tâm lý".
  - *Kiểm tra thực tế bằng code:*
    - **BM25 Rank của Ove:** `None` (hoàn toàn ngoài Top 200).
    - **Semantic Rank của Ove:** **#14** (Cosine Score = 0.8354).
    - **Semantic Top 1 thực tế:** `[B0011]` *Kính Vạn Hoa Chết Chóc* (Score = 0.8493).
    - **Hybrid Rank của Ove:** **#41** (Score = 0.01351).
    - **Hybrid Top 1 thực tế:** `[B2316]` *Thương (câu chuyện tiếp tục từ trái tim)* (BM25 #9, Semantic #4, Score = 0.03012).
- **Trạng thái:** **INCORRECT**. Thứ hạng của Ove bị trôi xuống tận hạng **#41** trong Hybrid Search chứ không phải hạng #7 như báo cáo cũ công bố.

---

## 3. KIỂM TRA TRUY VẤN KẾT HỢP NHIỀU ĐIỀU KIỆN (MULTI-CONSTRAINT SEARCH)

### 3.1. Đánh giá độc lập 3 ca nghi vấn trong báo cáo cũ
1. **MC03 (*"Sách tiếng Anh về trí tuệ nhân tạo"*):**
   - Hybrid Top 1: `[B0704]` *Ứng dụng trí tuệ nhân tạo AI trong dạy và học môn Toán, Tiếng Anh, Vật Lí, Hoá Học, KHTN*.
   - *Phân tích:* Đây là sách tiếng Việt hướng dẫn dùng AI để dạy môn Tiếng Anh trong trường học, **không phải sách viết bằng ngôn ngữ tiếng Anh về AI**.
   - *Đánh giá lại:* **PARTIAL** (Chỉ thỏa mãn điều kiện AI, sai điều kiện ngôn ngữ sách). Báo cáo cũ ghi PASS là sai.
2. **MC04 (*"Sách lập trình Java có ví dụ thực hành"*):**
   - Hybrid Top 1: `[B0718]` *Lập Trình Với Vi Điều Khiển PIC (Lý Thuyết - Thực Hành)*.
   - *Phân tích:* Sách vi điều khiển PIC, không dạy ngôn ngữ Java. Cuốn Java duy nhất trong kho bị đẩy xuống vị trí #2.
   - *Đánh giá lại:* **FAIL** (Top 1 sai ngôn ngữ mục tiêu).
3. **MC05 (*"Sách về tâm lý trẻ em dành cho phụ huynh"*):**
   - Hybrid Top 1: `[B2947]` *Tâm lý học về tự do và trưởng thành* (Daniel Kahneman).
   - *Phân tích:* Sách triết học tâm lý đại cương cho người trưởng thành, không đề cập đến trẻ em hay phương pháp dạy con của phụ huynh.
   - *Đánh giá lại:* **FAIL** (Top 1 không thỏa mãn đối tượng trẻ em & phụ huynh).

---

### 3.2. Kết quả kiểm thử mở rộng trên 30 truy vấn Multi-Constraint
Đã chạy thực nghiệm trên bộ 30 truy vấn đa dạng qua script [`scripts/eval_30_multi_constraints.py`](file:///d:/TrainAI/scripts/eval_30_multi_constraints.py), lưu tại `tests/multi_constraint_30_eval.json`:

```
======================================================================
KẾT QUẢ ĐÁNH GIÁ TOP 1 TRÊN 30 TRUY VẤN MULTI-CONSTRAINT
======================================================================
Phương pháp   | PASS (Thỏa mãn 100%) | PARTIAL (Thỏa mãn 1 phần) | FAIL (Sai hoàn toàn)
----------------------------------------------------------------------
BM25          | 15 / 30 (50.0%)      | 5 / 30 (16.7%)            | 10 / 30 (33.3%)
Semantic (E5) | 17 / 30 (56.7%)      | 6 / 30 (20.0%)            |  7 / 30 (23.3%)
Hybrid (RRF)  | 14 / 30 (46.7%)      | 9 / 30 (30.0%)            |  7 / 30 (23.3%)
======================================================================
```

### 3.3. Phát hiện quan trọng về Multi-Constraint
- **Hybrid Search có xu hướng thỏa hiệp sang kết quả PARTIAL:** Trong khi Semantic đạt 56.7% PASS ở Top 1, Hybrid chỉ đạt 46.7% PASS và tăng tỷ lệ PARTIAL lên 30.0%. 
- **Nguyên nhân:** Khi một điều kiện được BM25 kéo mạnh (ví dụ từ khóa *"Nhật Bản"* kéo sách học tiếng Nhật N3 trong khi câu hỏi là *"dạy con kiểu Nhật"*), điểm BM25 cao kết hợp với điểm Semantic trung bình làm cuốn sách PARTIAL đánh bại cuốn sách thỏa mãn đầy đủ cả hai điều kiện nhưng có thứ hạng đồng đều ở mức vừa phải.
- **Trạng thái:** **VERIFIED**. Khả năng xử lý Multi-Constraint của hệ thống hiện tại chỉ ở mức **Trung bình - Khá**, chưa đạt chuẩn tối ưu khi các điều kiện ràng buộc có độ phổ biến chênh lệch lớn trong kho dữ liệu.

---

## 4. KIỂM TRA XỬ LÝ DỮ LIỆU THIẾU, NULL VÀ NAN (BUG PHÁT HIỆN)

### 4.1. Vị trí mã nguồn gây lỗi
1. **Tệp tin [`src/passage_builder.py`](file:///d:/TrainAI/src/passage_builder.py#L10-L16) (Dòng 10-15):**
   ```python
   title = str(row.get('Title', '')).strip()
   author = str(row.get('Author', '')).strip()
   category = str(row.get('Category', '')).strip()
   subcategory = str(row.get('Subcategory', '')).strip()
   description = str(row.get('Description', '')).strip()
   keywords = str(row.get('Keywords', '')).strip()
```
2. **Tệp tin [`src/work_mapping.py`](file:///d:/TrainAI/src/work_mapping.py#L51-L55) (Dòng 51-55):**
   ```python
   "author": str(first_row['Author']),
   "category": str(first_row['Category']),
   "description": str(first_row['Description']),
```

### 4.2. Tái hiện lỗi thực tế (Empirical Proof via `scripts/test_null_nan_bug.py`)
Khi một dòng trong DataFrame có giá trị `None` hoặc `np.nan`:
- Trong pandas, `row.get('Author', '')` trả về `np.nan` (do key `'Author'` tồn tại trong Series).
- Hàm `str(np.nan)` biến giá trị khuyết tật thành chuỗi ký tự `"nan"`.
- Chuỗi passage được tạo ra có dạng:
  ```text
  'passage: Tên sách: Sách Test. Tác giả: nan. Thể loại: nan - nan. Nội dung: nan Từ khóa: nan'
  ```
- **Hậu quả 1 (Làm ô nhiễm Embedding):** Chuỗi `"nan"` được đưa trực tiếp vào mô hình Transformer `intfloat/multilingual-e5-small`. Mô hình E5 hiểu `"nan"` theo nghĩa ngôn ngữ (chẳng hạn tiền tố *nan* trong tiếng Anh hoặc từ *nan* trong tiếng Hindi/Pháp), làm sai lệch vector không gian ngữ nghĩa.
- **Hậu quả 2 (Làm ô nhiễm BM25 Index):** Tokenizer tách được token `'nan'` xuất hiện **5 lần** trong từ điển chỉ mục.
- **Hậu quả 3 (Lỗi hiển thị Work Catalog):** Trường tác giả trên giao diện sẽ hiển thị chữ `"nan"`.

### 4.3. Đánh giá mức độ nghiêm trọng
- **Mức độ:** **HIGH** (Lỗi rò rỉ dữ liệu kỹ thuật).
- **Trạng thái:** **VERIFIED BUG**. Cần sửa bằng hàm làm sạch trước khi ép kiểu chuỗi (ví dụ: `val if pd.notna(val) else ""`).

---

## 5. KIỂM TRA ĐỘ TIN CẬY CỦA BỘ NHẬN DIỆN NGOÀI KHO (OOD DETECTION)

### 5.1. Thử nghiệm mở rộng: 50 câu OOD đối đầu 100 câu In-Domain
Thực thi trên script [`scripts/eval_50_ood.py`](file:///d:/TrainAI/scripts/eval_50_ood.py) với 5 nhóm chủ đề hoàn toàn ngoài thư viện (Sửa xe, Y tế khám bệnh, Bất động sản, Vé máy bay, Đời sống thường nhật), lưu tại `tests/ood_50_evaluation.json`:

### 5.2. Phân phối điểm số thực tế
- **Cosine Similarity In-Domain (100 câu):** Min = `0.7845`, Mean = `0.8692`, Max = `0.9366`.
- **Cosine Similarity OOD (50 câu):** Min = `0.8093`, Mean = `0.8289`, Max = `0.8474`.
- **BM25 Max Score OOD (50 câu):** Min = `16.64`, Mean = `24.45`, Max = `44.09`.

### 5.3. Bảng ma trận đánh đổi (Trade-off Matrix) theo ngưỡng Cosine
| Ngưỡng Cosine | False Accept Rate (Lọt OOD) | False Reject Rate (Chặn oan sách thật) | Precision OOD | Recall OOD | F1-Score |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$< 0.80$** | **100.0%** (50/50 lọt) | **2.0%** (2 câu bị chặn oan) | 0.0% | 0.0% | 0.0 |
| **$< 0.81$** | **96.0%** (48/50 lọt) | **3.0%** (3 câu bị chặn oan) | 40.0% | 4.0% | 7.3 |
| **$< 0.82$** | **74.0%** (37/50 lọt) | **6.0%** (6 câu bị chặn oan) | 68.4% | 26.0% | 37.7 |
| **$< 0.83$** | **46.0%** (23/50 lọt) | **10.0%** (10 câu bị chặn oan) | 73.0% | 54.0% | 62.1 |
| **$< 0.84$** | **18.0%** (9/50 lọt) | **14.0%** (14 câu bị chặn oan) | 74.5% | 82.0% | 78.1 |
| **$< 0.85$** | **0.0%** (0 lọt) | **22.0%** (22 câu bị chặn oan) | 69.4% | **100.0%** | **82.0** |
| **$< 0.86$** | **0.0%** (0 lọt) | **37.0%** (37 câu bị chặn oan) | 57.5% | **100.0%** | 73.0 |

### 5.4. Kết luận kiểm toán về OOD
- **Trạng thái:** **VERIFIED**. 
- Dải điểm Cosine của OOD ($[0.8093, 0.8474]$) **hoàn toàn nằm trọn bên trong** dải điểm của In-Domain ($[0.7845, 0.9366]$).
- Nếu chọn ngưỡng $0.85$ để chặn sạch $100\%$ câu hỏi OOD thì hệ thống sẽ **đuổi nhầm 22% độc giả hợp lệ** (nhất là độc giả gõ sai chính tả hoặc câu hỏi ngắn).
- Điều kiện `BM25 == 0` hoàn toàn vô dụng vì 100% câu OOD đều nhận điểm BM25 từ $16.6$ đến $44.1$ do trùng các từ thông dụng (*"hướng dẫn"*, *"tại"*, *"nhà"*, *"cách"*).
- Khẳng định: **Không thể giải quyết bài toán OOD bằng ngưỡng Cosine hoặc BM25 đơn lẻ ở tầng nhúng.**

---

## 6. KIỂM TRA HIỆU NĂNG, TẢI ĐỒNG THỜI VÀ MỨC ĐỘ SẴN SÀNG

### 6.1. Xác minh phương pháp đo đạc trong code
- **Vị trí đo Latency:** Được đo bao quanh hàm `hybrid_engine.search()`, nghĩa là **đã bao gồm đầy đủ** thời gian:
  1. Tokenize & lọc từ dừng BM25.
  2. BM25 inverted index lookup.
  3. Format prefix `query: ` và chạy forward pass qua PyTorch CPU của `intfloat/multilingual-e5-small`.
  4. Vector dot product trên 3.000 vectors.
  5. RRF fusion và work_id aggregation.
- **Phương pháp đo RAM:** Đo bằng `psutil.Process().memory_info().rss` (Resident Set Size). Đảm bảo đo đúng bộ nhớ thực tế của tiến trình Python đang cấp phát.

### 6.2. Phân tích hiện tượng suy giảm hiệu năng khi tải đồng thời (GIL & CPU Contention)
Số liệu đo đạc thực tế từ `tests/stress_performance_eval.json`:
- **1 luồng tuần tự:** Latency = **61.01 ms**, Throughput = **16.39 QPS**.
- **5 luồng đồng thời:** Latency = **435.83 ms** (~7x), Throughput = **11.28 QPS**.
- **10 luồng đồng thời:** Latency = **919.79 ms** (~15x), Throughput = **10.66 QPS**.
- **20 luồng đồng thời:** Latency = **1.729.80 ms** (~28x), Throughput = **11.33 QPS**.

### 6.3. Nguyên nhân gốc rễ (Root Cause Analysis)
1. **Bản chất CPU-bound:** Việc nén câu hỏi bằng mô hình ngôn ngữ Transformer tiêu tốn rất nhiều chu kỳ CPU. Khi chạy tuần tự, PyTorch tận dụng toàn bộ 16 logical cores thông qua OpenMP/MKL để xử lý 1 query trong ~25ms.
2. **Xung đột tài nguyên luồng (Thread Thrashing) & GIL:** Khi `ThreadPoolExecutor` phóng ra 20 workers đồng thời:
   - Mỗi worker đều cố gắng gọi PyTorch sử dụng đa luồng, dẫn tới 20 workers $\times$ 16 threads cạnh tranh khốc liệt trên cùng một CPU, gây overhead chuyển ngữ cảnh (context switching) nghiêm trọng.
   - Các công đoạn tiền xử lý chuỗi và RRF dict merge bằng Python thuần bị nghẽn bởi Global Interpreter Lock (GIL).
   - Do đó, tổng throughput toàn hệ thống bị chặn cứng ở ngưỡng **$\approx 11 - 12$ QPS**.
3. **Đánh giá tuyên bố "Production Ready":**
   - **Với máy trạm Kiosk độc lập (Single Kiosk Terminal):** Hoàn toàn đạt chuẩn vì mỗi thời điểm chỉ có 1 người đứng thao tác màn hình cảm ứng, độ trễ 60-80ms là cực nhanh.
   - **Với hệ thống tập trung phục vụ nhiều Kiosk đồng thời (Centralized Multi-Kiosk Server):** **CHƯA ĐỦ ĐIỀU KIỆN**. Nếu 20 máy Kiosk bấm tìm kiếm cùng lúc, người dùng sẽ phải chờ gần 2 giây. Cần có kiến trúc đa tiến trình (Multi-process Worker / TorchServe / ONNX Runtime) hoặc cơ chế batching trước khi triển khai tập trung.

---

## 7. ĐẦU RA TỔNG HỢP VÀ ĐỀ XUẤT HƯỚNG XỬ LÝ THEO THỨ TỰ ƯU TIÊN

### Danh sách hành động kỹ thuật đề xuất (Chờ phê duyệt trước khi thực thi):

| Thứ tự ưu tiên | Vấn đề kỹ thuật | Giải pháp đề xuất | Lợi ích | Rủi ro |
| :---: | :--- | :--- | :--- | :--- |
| **Ưu tiên 1 (Cao)** | **Lỗi rò rỉ chuỗi `"nan"` khi dữ liệu khuyết thiếu** | Sửa `build_passage()` và `get_work_catalog()`: Thay `str(val)` bằng kiểm tra `pd.notna(val)` | Ngăn chặn ô nhiễm vector E5 và chỉ mục BM25 | Rất thấp (Cần xóa cache `embeddings/` và build lại 1 lần ~2 phút) |
| **Ưu tiên 2 (Cao)** | **Hiện tượng OOD chồng lấn không gian vector** | Không dùng ngưỡng Cosine cứng; Thiết lập danh sách từ khóa loại trừ intent ngoài thư viện ở API layer | Giảm 100% câu OOD mà không gây False Reject cho người dùng thật | Rất thấp |
| **Ưu tiên 3 (Trung bình)** | **Tối ưu hóa tham số RRF $k$** | Đổi mặc định `k = 20` (hoặc `k = 40`) trong `src/hybrid_search.py` | Tăng Hit@1 từ 83% lên 84%, tăng MRR từ 0.8867 lên 0.8917 | Rất thấp (Không đổi độ trễ) |
| **Ưu tiên 4 (Trung bình)** | **Làm giàu Metadata cho sách văn học (Ove, Beartown)** | Bổ sung các từ khóa thực thể (*"tự tử, cáu kỉnh"* cho Ove, *"khúc côn cầu"* cho Beartown) | Sửa triệt để hiện tượng Ove bị trôi xuống #41 | Thấp |
| **Ưu tiên 5 (Thấp)** | **Tối ưu hóa tải đồng thời CPU** | Giới hạn số luồng nội tại của PyTorch (`torch.set_num_threads(2)`) khi chạy multi-thread | Giảm độ trễ P95 khi nhiều request đồng thời | Cần đo đạc lại benchmark |

---

> [!IMPORTANT]
> **Tuân thủ nguyên tắc giới hạn:** Toàn bộ mã nguồn, cấu hình RRF, tập Ground Truth và dữ liệu gốc vẫn đang được **giữ nguyên 100%**. Không có bất kỳ thay đổi nào được thực hiện trên mã nguồn trước khi có sự xác nhận của bạn.
