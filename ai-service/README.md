# Smart Library Kiosk - AI Semantic Book Search

Hệ thống tìm kiếm sách thông minh bằng tiếng Việt cho Smart Library Kiosk (tích hợp RFID / IoT / AI).

## Tính năng chính
1. **Kho sách thực tế:** 3.000 đầu sách độc bản tiếng Việt đa dạng thể loại (Văn học, CNTT, Kinh tế, Ngoại ngữ, Kỹ năng, Khoa học, Thiếu nhi, Lịch sử, Tâm lý).
2. **Semantic Search:** Sử dụng mô hình pretrained `intfloat/multilingual-e5-small` chuẩn hóa vector 384 chiều, tìm kiếm theo cốt truyện, nội dung và ý niệm tự nhiên.
3. **BM25 Search:** Thuật toán BM25Okapi hỗ trợ cả tiếng Việt có dấu và không dấu (unaccented normalization).
4. **Hybrid Search (RRF):** Kết hợp kết quả BM25 và Semantic bằng thuật toán Reciprocal Rank Fusion ($k=60$), đạt **Hit@1 = 93.33%, Hit@5 = 96.67%, MRR = 0.9500**.
5. **Độ trễ thời gian thực:** Trung bình **~75ms/truy vấn** trên CPU.
6. **Web Kiosk & RESTful API:** FastAPI phục vụ giao diện màn hình cảm ứng, hiển thị mã kệ (`Shelf`), tầng (`Floor`), vị trí chi tiết (`Position`) và số lượng sách sẵn có (`Available/Total Copies`).

## Cấu trúc thư mục
```
TrainAI/
├── dataset/
│   ├── books_dataset.csv          # File dataset gốc do người dùng cung cấp (3.000 sách)
│   └── cleaned_books_dataset.csv  # Dataset đã được làm sạch chuẩn (3.000 sách thật)
├── embeddings/                    # Cache vector 384 chiều (embeddings.npy, book_ids.json, metadata.json)
├── static/                        # Giao diện Web Kiosk (index.html, styles)
├── tests/                         # Bộ benchmark test cases, metrics.json, results_raw.json
├── src/                           # Mã nguồn lõi (Data processing, Embedding, BM25, Semantic, Hybrid)
├── scripts/                       # Các script bảo trì, làm sạch và đánh giá hiệu năng
├── archive_legacy_eval/           # Thư mục lưu trữ các file đánh giá thử nghiệm của dataset cũ
├── main.py                        # FastAPI web server phục vụ Kiosk UI & Search API
└── requirements.txt
```

## Hướng dẫn khởi chạy
1. Khởi chạy Web Server:
```powershell
.\venv\Scripts\python.exe main.py
```
2. Mở trình duyệt tại: `http://127.0.0.1:8000`
