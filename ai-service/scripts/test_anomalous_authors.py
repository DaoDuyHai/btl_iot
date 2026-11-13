import pandas as pd
import re

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')

GENERIC_AUTHORS = {"Nhiều tác giả", "Nhóm Tác Giả", "Alpha Books", "NXB Kim Đồng", "WeupBooks", "NXB Trẻ"}

def is_fake_author(author, title, desc, cat):
    if not isinstance(author, str) or pd.isna(author):
        return True, "Rỗng/None"
    a = author.strip()
    if a in GENERIC_AUTHORS:
        return True, "Tên chung/NXB"
    
    # Kiểm tra các tác giả bị gán hàng loạt bất thường
    title_lower = str(title).lower()
    desc_lower = str(desc).lower()
    
    if a == "Stephen Hawking":
        # Chỉ giữ nếu cuốn sách thực sự nói về Stephen Hawking hoặc do ông viết
        if "stephen hawking" in title_lower or "lược sử thời gian" in title_lower or "vũ trụ trong vỏ hạt dẻ" in title_lower or "hố đen" in title_lower:
            return False, "Hợp lệ"
        return True, "Gán hàng loạt (Khoa học)"
        
    if a == "Daniel Kahneman":
        if "daniel kahneman" in title_lower or "tư duy nhanh và chậm" in title_lower or "nhiễu" in title_lower:
            return False, "Hợp lệ"
        return True, "Gán hàng loạt (Tâm lý)"
        
    if a == "Nguyễn Hiến Lê":
        if "nguyễn hiến lê" in title_lower or "nguyen hien le" in title_lower or "nguyễn hiến lê" in desc_lower[:150]:
            return False, "Hợp lệ"
        return True, "Gán hàng loạt (Lịch sử)"
        
    return False, "Hợp lệ"

stats = {}
for idx, row in df.iterrows():
    is_fake, reason = is_fake_author(row['Author'], row['Title'], row['Description'], row['Category'])
    if is_fake:
        auth = str(row['Author']).strip()
        stats[auth] = stats.get(auth, 0) + 1

print("THỐNG KÊ TÁC GIẢ BỊ LOẠI:")
for a, c in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {a:<25}: {c:>4} cuốn")
print(f"Tổng số sách có tác giả bị loại khỏi search_text/BM25: {sum(stats.values())}")
