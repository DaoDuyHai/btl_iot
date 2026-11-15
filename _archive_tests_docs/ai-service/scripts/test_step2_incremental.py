import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.query_understanding import QueryAnalyzer

df = pd.read_csv('ai-service/dataset/books_enriched.csv')
analyzer = QueryAnalyzer(catalog_df=df)

test_queries = [
    # Nhóm 1: Câu cảm xúc người dùng (User câu hỏi)
    ("Câu hỏi thực tế người dùng", "giờ tôi đang rất buồn, tôi cần 1 cuốn sách giúp tôi giải trí vui vẻ hơn"),
    # Nhóm 2: Câu mệt mỏi + phủ định kỹ thuật
    ("Cảm xúc + Phủ định", "Đầu óc đang rất mỏi mệt, đừng gợi ý sách kỹ thuật hay tính toán gì nhé"),
    # Nhóm 3: Đọc cho con
    ("Ngữ cảnh gia đình", "tôi muốn tìm sách đọc cho con gái 5 tuổi trước giờ đi ngủ"),
    # Nhóm 4: Mất ngủ đêm khuya
    ("Ngữ cảnh mất ngủ", "Đêm khuya trằn trọc mất ngủ, muốn một cuốn sách nhẹ nhàng để dễ chìm vào giấc ngủ"),
    # Nhóm 5: Tên sách chính xác
    ("Tên sách đích danh", "Người Đàn Ông Mang Tên Ove"),
    # Nhóm 6: Tác giả cụ thể
    ("Tác giả cụ thể", "Sách của nhà văn Nguyễn Nhật Ánh"),
    # Nhóm 7: Tiếng Việt không dấu
    ("Không dấu", "tim sach giup toi thu gian dau oc"),
    # Nhóm 8: Hỏi vị trí và còn sách
    ("Vị trí & tình trạng kho", "cuốn Nhà Giả Kim còn trên kệ tầng mấy"),
    # Nhóm 9: Chủ đề chuyên môn
    ("Chủ đề kỹ thuật", "Giáo trình cấu trúc dữ liệu và giải thuật bằng C++"),
    # Nhóm 10: Ngoài phạm vi thư viện
    ("Ngoài phạm vi (OOD)", "thời tiết hôm nay thế nào quán cafe nào gần đây")
]

print("=" * 80)
print("TEST THỰC TẾ BƯỚC 2: KIỂM THỬ QUERY UNDERSTANDING (10 TRƯỜNG HỢP)")
print("=" * 80)

for idx, (label, q) in enumerate(test_queries, 1):
    res = analyzer.analyze(q)
    print(f"\n[{idx}] [{label}]: \"{q}\"")
    print(f"    • Intent           : {res['intent']}")
    print(f"    • Giải thích       : {res['explanation']}")
    if res['filters']:
        print(f"    • Filters bóc tách : {res['filters']}")
    if res['target_moods']:
        print(f"    • Target Moods      : {res['target_moods']}")
    if res['preferred_categories']:
        print(f"    • Thể loại ưu tiên : {res['preferred_categories']}")
    if res['avoid_keywords']:
        print(f"    • Từ khóa CẦN TRÁNH : {res['avoid_keywords']}")
    if res['expanded_queries']:
        print(f"    • Truy vấn mở rộng : {res['expanded_queries']}")
