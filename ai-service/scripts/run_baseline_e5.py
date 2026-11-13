import os
import sys
import json
import time
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("CHẠY ĐÁNH GIÁ BASELINE E5 THUẦN (intfloat/multilingual-e5-small)")
print("=" * 80)

# Paths
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'cleaned_books_dataset.csv')
EMB_PATH = os.path.join(os.path.dirname(__file__), '..', 'embeddings', 'embeddings.npy')
IDS_PATH = os.path.join(os.path.dirname(__file__), '..', 'embeddings', 'book_ids.json')
OUT_JSON = os.path.join(os.path.dirname(__file__), '..', 'baseline_results.json')

# Load dataset
df = pd.read_csv(DATASET_PATH)
df['Book_ID'] = df['Book_ID'].astype(str)
book_dict = df.set_index('Book_ID').to_dict(orient='index')

# Load cached book embeddings
print(f"[*] Đang tải embeddings từ {EMB_PATH}...")
book_embeddings = np.load(EMB_PATH)
with open(IDS_PATH, 'r', encoding='utf-8') as f:
    book_ids = json.load(f)

print(f"[+] Đã tải embeddings: shape={book_embeddings.shape}, tổng số sách: {len(book_ids)}")

# Load E5 Model for encoding queries
MODEL_NAME = "intfloat/multilingual-e5-small"
print(f"[*] Đang tải model {MODEL_NAME}...")
t0 = time.time()
model = SentenceTransformer(MODEL_NAME)
print(f"[+] Model tải xong trong {round(time.time() - t0, 2)}s")

# 20 specific queries
specific_queries = [
    "Người Đàn Ông Mang Tên Ove",
    "Nhà Giả Kim",
    "Cây Cam Ngọt Của Tôi",
    "Mắt Biếc",
    "Nỗi Buồn Chiến Tranh Bảo Ninh",
    "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông",
    "Không Gia Đình Hector Malot",
    "Totto-chan Bên Cửa Sổ",
    "Thiên Tài Bên Trái Kẻ Điên Bên Phải",
    "Đắc Nhân Tâm Dale Carnegie",
    "Lược Sử Thời Gian Stephen Hawking",
    "Tư Duy Nhanh Và Chậm Daniel Kahneman",
    "Sách của nhà văn Nguyễn Nhật Ánh",
    "Tiểu thuyết trinh thám của Agatha Christie",
    "Giáo trình cấu trúc dữ liệu và giải thuật bằng C++",
    "Sách học lập trình mạng máy tính và an toàn thông tin",
    "Tài liệu luyện thi tiếng Anh IELTS Academic",
    "Giáo trình kinh tế vi mô và kinh tế lượng cơ bản",
    "Sách lịch sử Việt Nam thời kỳ nhà Trần",
    "Sách hướng dẫn quản trị cơ sở dữ liệu SQL Server"
]

# 20 ambiguous / emotional / context queries
ambiguous_queries = [
    "Hôm nay tôi đang rất mệt, tôi muốn có cuốn sách giúp tôi thư giãn",
    "Tôi đang bị stress nặng vì áp lực deadline công việc, cần đọc gì cho nhẹ đầu",
    "Vừa chia tay người yêu, tâm trạng rất buồn và trống rỗng",
    "Cảm thấy mất phương hướng, không biết tương lai đi về đâu",
    "Đêm khuya trằn trọc mất ngủ, muốn một cuốn sách nhẹ nhàng để dễ chìm vào giấc ngủ",
    "Một buổi chiều mưa chủ nhật muốn ngồi nhâm nhi tách trà đọc sách yên bình",
    "Dạo này đầu óc rối bời và quá tải, cần tìm lại sự bình yên trong tâm hồn",
    "Tôi muốn tìm sách đọc cho con gái 5 tuổi trước giờ đi ngủ",
    "Mới bắt đầu tập đọc sách, chưa quen đọc nhiều chữ thì nên chọn cuốn nào",
    "Cuối tuần rảnh rỗi muốn tìm gì đó vui vẻ hài hước để xả stress cười sảng khoái",
    "Cảm thấy kiệt sức và mất hết động lực làm việc sau thời gian dài cày cuốc",
    "Tôi muốn một cuốn sách sưởi ấm tâm hồn và khiến tôi rơi nước mắt vì cảm động",
    "Muốn đọc gì đó ly kỳ hồi hộp nghẹt thở để tỉnh cả ngủ",
    "Cuộc sống bận rộn hối hả quá, muốn chậm lại một chút để lắng nghe bản thân",
    "Muốn tìm cảm hứng sống tích cực để bắt đầu một ngày mới tràn đầy năng lượng",
    "Cảm thấy cô đơn lạc lõng giữa thành phố đông đúc",
    "Đầu óc đang rất mỏi mệt, đừng gợi ý sách kỹ thuật hay tính toán gì nhé",
    "Tìm sách đọc giải trí trên chuyến xe bus đi làm mỗi ngày",
    "Tôi đang giận dữ và bực bội, cần gì đó giúp tôi bình tĩnh lại",
    "Muốn tìm một câu chuyện nhẹ nhàng ấm áp về tình bạn và gia đình"
]

all_queries = [("specific", q) for q in specific_queries] + [("ambiguous", q) for q in ambiguous_queries]

# Format with query: prefix
formatted_queries = [f"query: {q}" for _, q in all_queries]

print(f"[*] Đang encode {len(formatted_queries)} queries bằng E5 (normalize_embeddings=True)...")
t0 = time.time()
query_embeddings = model.encode(formatted_queries, normalize_embeddings=True)
print(f"[+] Encode xong trong {round(time.time() - t0, 2)}s")

results = []

print("\n" + "=" * 80)
print("KẾT QUẢ TOP 5 BASELINE E5 CHO TỪNG CÂU HỎI")
print("=" * 80)

for idx, ((q_type, q_text), q_emb) in enumerate(zip(all_queries, query_embeddings), 1):
    sims = cosine_similarity([q_emb], book_embeddings)[0]
    top_indices = np.argsort(sims)[::-1][:5]
    
    top_5 = []
    for rank, b_idx in enumerate(top_indices, 1):
        bid = book_ids[b_idx]
        b_info = book_dict.get(bid, {})
        top_5.append({
            "rank": rank,
            "book_id": bid,
            "title": b_info.get("Title", ""),
            "author": b_info.get("Author", ""),
            "category": b_info.get("Category", ""),
            "subcategory": b_info.get("Subcategory", ""),
            "score": round(float(sims[b_idx]), 4)
        })
    
    results.append({
        "id": idx,
        "type": q_type,
        "query": q_text,
        "top_5": top_5
    })
    
    prefix = "[CỤ THỂ]" if q_type == "specific" else "[MƠ HỒ/CẢM XÚC]"
    print(f"\n{idx:02d}. {prefix} \"{q_text}\"")
    for b in top_5:
        print(f"    Top {b['rank']}: [{b['book_id']}] {b['title']} - {b['author']} ({b['category']}) [Score: {b['score']}]")

with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print(f"[+] Đã lưu toàn bộ kết quả vào {OUT_JSON}")
print("=" * 80)
