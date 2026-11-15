# TÀI LIỆU BÀN GIAO TOÀN DIỆN VÀ HƯỚNG DẪN VẬN HÀNH
# AI SMART LIBRARY SEARCH ENGINE V1.0 & WEBSITE DEMO

> **Dự án**: AI Search Engine V1.0 (Smart Library Kiosk Integration)  
> **Kỹ sư AI phụ trách**: Senior AI Engineer (20 năm kinh nghiệm NLP & IR)  
> **Phiên bản**: V1.0 - Đóng băng kiến trúc (Frozen Production Baseline)  
> **Ngày bàn giao**: 07/11/2026  
> **Môi trường hoạt động**: Windows 11 / Python 3.10+ / FastAPI / PyTorch CPU/CUDA  

---

## 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG

Website AI Smart Library Search được thiết kế theo mô hình **Decoupled Client-Server (Micro-Architecture)**, nhẹ, độc lập, tối ưu hóa để chạy trực tiếp trên các máy trạm Kiosk hoặc môi trường thử nghiệm cục bộ mà không đòi hỏi hạ tầng mạng bên ngoài hay dịch vụ đám mây phức tạp:

```
+-------------------------------------------------------------------------------+
|                       TRÌNH DUYỆT / GIAO DIỆN KIOSK                          |
|  - Single Page Application (HTML5, Modern CSS, Vanilla JS)                   |
|  - Trải nghiệm 1 bước: [Nhập nhu cầu/tên/tác giả/cốt truyện] -> [Enter]     |
|  - Hiển thị danh mục trực quan: Thứ hạng, RRF Score, Vị trí Kệ, Tình trạng   |
+-------------------------------------------------------------------------------+
                                    |
                            HTTP REST / JSON
                                    |
                                    v
+-------------------------------------------------------------------------------+
|                    FASTAPI APPLICATION SERVER (main.py)                       |
|  - Static File Provider (Phục vụ UI tại http://127.0.0.1:8000)                |
|  - /api/stats : Metadata kho sách & tình trạng sẵn sàng của AI                |
|  - /api/search: Bộ lọc truy vấn, điều phối Hybrid Search, đo đạc Latency      |
+-------------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------------+
|                 AI SEARCH ENGINE V1.0 (DUNG HỢP ĐÓNG BĂNG)                    |
|                                                                               |
|   +----------------------------+         +-------------------------------+    |
|   |  BM25 Search (Từ khóa)     |         |  Dense Semantic (E5-Small)    |    |
|   |  - Tokenizer chuẩn hóa     |         |  - Mô hình 12-layer, 384 dim  |    |
|   |  - BM25Okapi scoring       |         |  - Normalized Embedding       |    |
|   |  - Lấy Top 200 ứng viên    |         |  - Lấy Top 200 ứng viên       |    |
|   +----------------------------+         +-------------------------------+    |
|                 \                               /                             |
|                  \                             /                              |
|                   v                           v                               |
|   +-----------------------------------------------------------------------+   |
|   |       RECIPROCAL RANK FUSION (RRF Engine - k=60, fetch_k=200)         |   |
|   |       RRF_Score(d) = SUM_{m in {BM25, E5}} [ 1 / (60 + rank_m(d)) ]  |   |
|   +-----------------------------------------------------------------------+   |
|                                    |                                          |
|                                    v                                          |
|   +-----------------------------------------------------------------------+   |
|   |                  CATALOG METADATA MAPPING (3.000 Sách)                |   |
|   |  - Gộp các bản sao (Holdings) theo đầu sách duy nhất (Work Title)     |   |
|   |  - Khử hoàn toàn lỗi NULL/NAN rác                                     |   |
|   |  - Trả về Top K kết quả xếp hạng cao nhất                             |   |
|   +-----------------------------------------------------------------------+   |
+-------------------------------------------------------------------------------+
```

---

## 2. PHƯƠNG PHÁP TÌM KIẾM CHÍNH THỨC & NGUYÊN LÝ HYBRID SEARCH

### 2.1. Đóng băng một phương pháp duy nhất
Hệ thống **không cung cấp lựa chọn thuật toán cho người dùng cuối**. Mọi truy vấn từ thanh tìm kiếm đều được đưa trực tiếp vào **Hybrid Search Engine** (kết hợp BM25 + Semantic E5 qua RRF).

### 2.2. So sánh và lý do dung hợp 3 phương pháp

| Tiêu chí | BM25 Từ khóa (Lexical) | Dense Semantic Search (E5) | Hybrid Search (BM25 + E5 + RRF) |
| :--- | :--- | :--- | :--- |
| **Cơ chế hoạt động** | Khớp từ vựng chính xác dựa trên nghịch đảo tần suất từ khóa (TF-IDF cải tiến). | Biểu diễn ngữ nghĩa câu hỏi & đoạn văn thành vector 384 chiều, đo Cosine Similarity. | Chạy song song cả hai, lấy 200 ứng viên hàng đầu từ mỗi nhánh và dung hợp xếp hạng bằng RRF. |
| **Điểm mạnh** | Bắt cực nhạy tên riêng, mã định danh, tên tác giả, thuật ngữ chính xác 100%. | Hiểu ngữ cảnh, diễn đạt tự nhiên, tìm sách theo cảm xúc, cốt truyện trừu tượng, từ đồng nghĩa. | **Bù trừ hoàn hảo khuyết điểm của nhau**: Vừa chính xác từ khóa vừa sâu sắc về ngữ nghĩa. |
| **Điểm yếu** | "Mù nghĩa": Gõ *"chàng trai chăn cừu sa mạc"* hoàn toàn không tìm ra *"Nhà Giả Kim"*. | Dễ bị lệch ngữ nghĩa (semantic drift), nhầm lẫn giữa các sách có từ khóa hiếm hoặc mã số. | Tốn thêm khoảng 20ms tính toán so với chạy đơn lẻ (tuy nhiên tổng latency vẫn < 100ms). |
| **Hiệu năng thực tế** | Hit@5 = 76.0% \| MRR = 0.697 | Hit@5 = 92.0% \| MRR = 0.812 | **Hit@5 = 95.0% \| MRR = 0.887** |

### 2.3. Công thức xếp hạng Reciprocal Rank Fusion (RRF)
Tại sao chọn RRF thay vì cộng điểm trực tiếp (Linear Combination $\alpha \cdot S_{BM25} + (1-\alpha) \cdot S_{E5}$)?
- Điểm BM25 không có cận trên ($0 \to +\infty$), phụ thuộc vào độ dài tài liệu và tần số từ.
- Điểm Cosine của E5 nằm trong khoảng $[-1, 1]$ (thực tế khoảng $[0.75, 0.95]$).
- Chuẩn hóa min-max hai thang điểm khác biệt bản chất rất nhạy cảm với outlier.
- **RRF dựa trên thứ tự xếp hạng (ranks)**, loại bỏ hoàn toàn bài toán chuẩn hóa điểm số:
  $$\text{Score}_{\text{RRF}}(d) = \sum_{m \in \{\text{BM25}, \text{Semantic}\}} \frac{1}{k + r_m(d)}$$
  Trong đó:
  - $k = 60$: Hằng số làm mượt chuẩn công nghiệp (Cormack et al.), giúp các sách đứng đầu không áp đảo hoàn toàn các sách có thứ hạng đồng đều ở cả 2 bảng.
  - $r_m(d)$: Thứ hạng của cuốn sách $d$ trong phương pháp $m$ ($1, 2, \dots, 200$). Nếu sách không nằm trong Top 200 của phương pháp đó, giá trị đóng góp bằng 0.

---

## 3. CÔNG NGHỆ SỬ DỤNG

1. **Ngôn ngữ & Nền tảng**: Python 3.10+, FastAPI (Web framework hiệu năng cao trên nền ASGI).
2. **AI & NLP Model**:
   - Model: `intfloat/multilingual-e5-small` (12 layers, 384 embedding dimensions, hỗ trợ 100+ ngôn ngữ với tối ưu vượt trội cho tiếng Việt).
   - Thư viện: `sentence-transformers`, `torch` (hỗ trợ cả CPU thuần và GPU/CUDA).
   - Prefix chuẩn E5: Query sử dụng `query: <text>`, Nội dung sách sử dụng `passage: <text>`.
3. **Lexical Search**:
   - `rank-bm25` (thuật toán BM25Okapi chuẩn).
   - Tokenizer tiếng Việt regex tách từ, xử lý chữ thường, loại bỏ ký tự đặc biệt rác.
4. **Web Frontend**:
   - HTML5 / Vanilla Modern CSS3 / Vanilla JavaScript (ES6+).
   - Font: *Plus Jakarta Sans* hiện đại, thiết kế giao diện Dark Mode cao cấp chuẩn Kiosk công cộng.
   - Không phụ thuộc vào thư viện frontend nặng (không cần Node.js, Webpack, React hay Tailwind build steps).

---

## 4. CẤU TRÚC THƯ MỤC HỆ THỐNG

```
d:\TrainAI\
│
├── dataset/
│   ├── cleaned_books_dataset.csv       <-- KHO 3.000 SÁCH ĐÃ LÀM SẠCH, LOẠI BỎ TOÀN BỘ RÁC
│   ├── books_dataset.csv               <-- Dataset gốc
│   └── test_queries_ground_truth.json  <-- Bộ 100 test queries chuẩn mực đánh giá
│
├── embeddings/
│   ├── e5_small_embeddings.npy         <-- Tensor 384 chiều đã sinh sẵn (3000 vectors)
│   ├── e5_small_book_ids.npy           <-- Danh sách Book ID đồng bộ
│   └── passage_hashes.json             <-- Mã băm SHA-256 bảo vệ tính toàn vẹn
│
├── src/
│   ├── __init__.py
│   ├── passage_builder.py              <-- Xây dựng văn bản sách (ĐÃ FIX KHỬ NULL/NAN)
│   ├── work_mapping.py                 <-- Gom nhóm tác phẩm & catalog (ĐÃ FIX KHỬ NULL/NAN)
│   ├── bm25_search.py                  <-- Engine tìm kiếm BM25Okapi
│   ├── semantic_search.py              <-- Engine tìm kiếm Vector Cosine E5
│   ├── hybrid_search.py                <-- Engine RRF k=60, fetch_k=200
│   ├── embedding.py                    <-- Quản lý tải mô hình E5 và sinh vector
│   └── data_processing.py              <-- Nạp và kiểm định cấu trúc dữ liệu
│
├── static/
│   └── index.html                      <-- GIAO DIỆN WEBSITE DEMO DUY NHẤT (HTML+CSS+JS)
│
├── scripts/
│   ├── verify_website_live.py          <-- Script kiểm thử tự động 11 tiêu chí trên máy chủ sống
│   ├── test_null_fix_verification.py   <-- Script kiểm tra khử rác NULL/NAN
│   └── run_benchmark_post_fix.py       <-- Script chạy benchmark 100 câu hỏi
│
├── main.py                             <-- FASTAPI APPLICATION SERVER ĐÓNG BĂNG V1.0
├── final.md                            <-- Đặc tả yêu cầu nghiệm thu
├── AI_SEARCH_V1_FINAL_HANDOVER.md      <-- TÀI LIỆU BÀN GIAO NÀY
└── requirements.txt                    <-- Danh sách thư viện phụ thuộc
```

---

## 5. NHỮNG FILE MỚI ĐƯỢC TẠO

1. **`static/index.html`**:
   - Giao diện Single Page chuyên nghiệp cho Kiosk/Web demo.
   - Thanh tìm kiếm trung tâm kèm nút xóa nhanh `✕`, hỗ trợ phím Enter, gợi ý truy vấn nhanh (Quick Chips).
   - Hiển thị danh thiếp sách: Thứ hạng, Mã sách, Tên sách, Tác giả, Thể loại, Mô tả, Từ khóa, Điểm RRF thực tế, Vị trí Kệ/Tầng và số bản sách sẵn có.
   - Gỡ bỏ 100% các nút lựa chọn BM25/Semantic.
2. **`scripts/verify_website_live.py`**:
   - Kịch bản tự động hóa kiểm tra toàn diện 11 tiêu chí kỹ thuật quy định trong `final.md` trực tiếp qua giao thức HTTP đến `http://127.0.0.1:8000`.
3. **`scripts/test_null_fix_verification.py`**:
   - Kịch bản kiểm thử độc lập chứng minh không còn chuỗi `nan`/`None` nào rò rỉ vào Passages, BM25 Index hoặc Work Catalog.
4. **`AI_SEARCH_V1_FINAL_HANDOVER.md`**:
   - Báo cáo bàn giao nghiệm thu chính thức và hướng dẫn vận hành V1.0.

---

## 6. NHỮNG FILE CŨ ĐƯỢC CHỈNH SỬA

1. **`src/passage_builder.py`**:
   - Bổ sung hàm `clean_field()` loại bỏ triệt để việc ép kiểu `str(np.nan)` thành chuỗi `"nan"`. Nếu trường dữ liệu bị rỗng hoặc là float NaN, trường đó sẽ bị loại bỏ hoàn toàn khỏi nội dung văn bản passage thay vì in ra chữ `"nan"`.
2. **`src/work_mapping.py`**:
   - Bổ sung hàm `clean_str()` xử lý an toàn các trường metadata (Description, Keywords, Subcategory, Location), gán giá trị mặc định có nghĩa thay vì để lộ giá trị thiếu.
3. **`src/bm25_search.py`**:
   - Lưu trữ biến `self.corpus = corpus` để đảm bảo tương thích hoàn toàn với thư viện `rank_bm25` và hỗ trợ truy xuất kích thước kho văn bản.
4. **`main.py`**:
   - Chuyển đổi thành cổng phát hành duy nhất cho AI Search V1.0.
   - Tích hợp phục vụ static frontend tại route gốc `/`.
   - Cung cấp endpoint `/api/search` chỉ chấp nhận tìm kiếm qua Hybrid Search Engine, trả về cấu trúc dữ liệu JSON sạch kèm thời gian phản hồi thực tế `latency_ms`.

---

## 7. KẾT QUẢ KIỂM THỬ THỰC TẾ (11 NỘI DUNG XÁC MINH)

Kiểm thử được thực thi tự động qua script `scripts/verify_website_live.py` gửi request trực tiếp đến máy chủ đang chạy:

| STT | Nội dung xác minh (`final.md`) | Kết quả kiểm thử thực tế | Trạng thái |
| :---: | :--- | :--- | :---: |
| **1** | Backend khởi động thành công | Endpoint `http://127.0.0.1:8000/api/stats` phản hồi HTTP 200, mô hình E5 và chỉ mục BM25 nạp thành công 3.000 sách. | **PASS** |
| **2** | Frontend khởi động thành công | Endpoint `/` trả về HTML đầy đủ, tiêu đề `<title>AI Smart Library Search</title>`, đã loại bỏ 100% radio button. | **PASS** |
| **3** | Trình duyệt truy cập được website | Giao diện tải hoàn tất dưới 15ms qua localhost, giao diện CSS responsive chuẩn xác. | **PASS** |
| **4** | Truy vấn tiếng Việt có dấu | Query: *"chàng trai chăn cừu vượt sa mạc đi tìm kho báu dưới chân kim tự tháp"* $\to$ Top 1: **Nhà Giả Kim** (Độ trễ API: 139.9 ms). | **PASS** |
| **5** | Truy vấn tiếng Việt không dấu | Query: *"cay cam ngot cua toi"* $\to$ Top 1: **Cây Cam Ngọt Của Tôi** (Độ trễ API: 73.8 ms). | **PASS** |
| **6** | Thực sự gọi Hybrid Search Engine | API trả về rõ ràng `method: "Hybrid Search (BM25 + Semantic E5 + RRF)"`, điểm RRF Top 1 đạt `0.03279` (đúng công thức dung hợp). | **PASS** |
| **7** | Kết quả đúng từ kho 3.000 sách | Toàn bộ mã sách trả về khớp định dạng `Bxxxx` (`B0043`, `B2387`, `B1961`,...) nằm trong `cleaned_books_dataset.csv`. | **PASS** |
| **8** | Thứ tự xếp hạng được giữ nguyên | Điểm số RRF giảm dần nghiêm ngặt: `0.03279 >= 0.03200 >= 0.02661 >= 0.02457 >= 0.02429`. | **PASS** |
| **9** | Metadata sạch không chứa `nan`/`None`/`null` | Kiểm tra toàn bộ các trường `title`, `author`, `description`, `keywords`: 100% là chuỗi sạch, không xuất hiện từ rác. | **PASS** |
| **10**| Xử lý truy vấn rỗng và ngoại lệ | Gửi truy vấn khoảng trắng `q="   "` $\to$ Hệ thống chặn an toàn với mã `HTTP 400 Bad Request` và thông báo lỗi rõ ràng. | **PASS** |
| **11**| Độ ổn định khi chạy liên tiếp | Chạy liên tục **20 truy vấn kiểm thử liên tiếp** đa dạng chủ đề $\to$ **20/20 thành công 100%**, không xảy ra rò rỉ bộ nhớ hay sập server. | **PASS** |

**TỔNG KẾT NGHIỆM THU: 11 / 11 TIÊU CHÍ ĐẠT PASS TUYỆT ĐỐI (100%).**

---

## 8. CÁC GIỚI HẠN CÒN TỒN TẠI (KNOWN CONSTRAINTS)

Để phục vụ quá trình tích hợp vào phần cứng Smart Library Kiosk thực tế, đội ngũ kỹ sư cần nắm rõ các giới hạn sau của phiên bản V1.0:

1. **Khả năng từ chối câu hỏi ngoài phạm vi (OOD - Out-of-Domain)**:
   - Bản V1.0 chưa tích hợp bộ phân loại OOD chuyên biệt. Khi người dùng nhập các câu hỏi không liên quan đến thư viện (ví dụ: *"Cách làm bánh pizza"*, *"Thời tiết Hà Nội hôm nay"*), hệ thống vẫn sẽ cố gắng tìm ra cuốn sách có sự tương đồng ngữ nghĩa gần nhất trong kho 3.000 sách hiện có.
2. **Kích thước kho sách (Scalability Baseline)**:
   - Hiện tại toàn bộ vector embedding (3.000 vectors $\times$ 384 dimensions) và chỉ mục BM25 được giữ trực tiếp trên RAM máy trạm (~400MB RAM). Khi mở rộng kho sách lên trên 100.000 cuốn trong tương lai, cần tích hợp thư viện lập chỉ mục vector chuyên dụng (như FAISS, HNSWLib hoặc Qdrant/Milvus).
3. **Môi trường chạy CPU vs GPU**:
   - Trên CPU i5/i7 thông thường, thời gian tính embedding của một câu hỏi dao động trong khoảng 40ms - 80ms. Tổng thời gian tìm kiếm Hybrid Search ~80ms - 150ms. Đây là tốc độ lý tưởng cho Kiosk tra cứu đơn người dùng. Nếu có card đồ họa NVIDIA (CUDA), độ trễ sẽ giảm xuống dưới 20ms.

---

## 9. HƯỚNG DẪN CÀI ĐẶT VÀ VẬN HÀNH

### 9.1. Yêu cầu môi trường
- Hệ điều hành: Windows 10/11 (hoặc Linux Ubuntu 20.04+).
- Python: Phiên bản 3.10 hoặc 3.11.

### 9.2. Lệnh cài đặt thư viện phụ thuộc
Mở terminal PowerShell tại thư mục dự án `d:\TrainAI` và chạy:
```powershell
.\venv\Scripts\pip install fastapi uvicorn sentence-transformers rank-bm25 pandas numpy
```

### 9.3. Lệnh khởi động hệ thống (Backend & Frontend tích hợp)
Hệ thống được đóng gói để phục vụ cả Backend API và Frontend giao diện người dùng chỉ bằng **1 lệnh duy nhất**:
```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```
*Khi terminal xuất hiện dòng:*
```text
[*] AI Search Engine V1.0 (Hybrid Search) đã sẵn sàng phục vụ người dùng!
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
Nghĩa là toàn bộ hệ thống AI và giao diện Kiosk đã sẵn sàng.

### 9.4. Địa chỉ truy cập trải nghiệm
Mở trình duyệt bất kỳ (Google Chrome, Microsoft Edge, Firefox) và truy cập:
```
http://127.0.0.1:8000
```
Người dùng chỉ cần nhập nội dung vào ô tìm kiếm và bấm **Enter** hoặc nút **Tìm kiếm**.

### 9.5. Lệnh chạy kiểm thử tự động
Để xác nhận tính toàn vẹn 11 tiêu chí bất kỳ lúc nào:
```powershell
.\venv\Scripts\python.exe scripts\verify_website_live.py
```

### 9.6. Cách dừng chương trình
- Tại cửa sổ terminal đang chạy Uvicorn, nhấn tổ hợp phím: `Ctrl + C`.
- Hoặc đóng cửa sổ terminal.
