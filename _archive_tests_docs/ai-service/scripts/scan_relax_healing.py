import re
import pandas as pd

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')

relax_patterns = [
    r'thư giãn', r'thảnh thơi', r'thư thái', r'thư thả', r'thong dong', 
    r'tô màu', r'xả stress', r'giải trí nhẹ nhàng', r'nhâm nhi',
    r'bình yên', r'an nhiên', r'chúc bé ngủ ngon', r'ngủ ngon'
]

healing_patterns = [
    r'chữa lành', r'xoa dịu', r'vỗ về', r'an ủi', r'tự chữa lành',
    r'xoa dịu tâm hồn', r'vượt qua nỗi đau', r'ôm lấy chính mình'
]

print("TÌM KIẾM CÁC CUỐN SÁCH CÓ TỪ KHÓA THƯ GIÃN:")
print("-" * 50)
relax_found = []
for idx, row in df.iterrows():
    text = (str(row['Title']) + " " + str(row['Description']) + " " + str(row['Subcategory'])).lower()
    cat = str(row['Category'])
    # Không tính sách kinh tế / lịch sử
    if cat in ["Kinh tế – Kinh doanh", "Lịch sử – Văn hóa"]:
        continue
    # Nếu CNTT hoặc Khoa học thì chỉ lấy sách thiếu nhi / cho bé
    if cat in ["Công nghệ thông tin", "Khoa học – Công nghệ"]:
        if not ("cho bé" in text or "mầm non" in text or "tô màu" in text or "thiếu nhi" in text):
            continue
            
    matches = [p for p in relax_patterns if re.search(r'\b' + p + r'\b', text)]
    if matches:
        relax_found.append((row['Book_ID'], row['Title'], cat, matches))

print(f"Tổng số sách thư giãn tìm được: {len(relax_found)}")
for r in relax_found[:15]:
    print(f"  [{r[0]}] {r[1]} ({r[2]}) -> {r[3]}")

print("\n" + "=" * 50)
print("TÌM KIẾM CÁC CUỐN SÁCH CÓ TỪ KHÓA CHỮA LÀNH:")
print("-" * 50)
healing_found = []
for idx, row in df.iterrows():
    text = (str(row['Title']) + " " + str(row['Description']) + " " + str(row['Subcategory'])).lower()
    cat = str(row['Category'])
    if cat in ["Kinh tế – Kinh doanh", "Lịch sử – Văn hóa", "Công nghệ thông tin"]:
        continue
    matches = [p for p in healing_patterns if re.search(r'\b' + p + r'\b', text)]
    if matches:
        healing_found.append((row['Book_ID'], row['Title'], cat, matches))

print(f"Tổng số sách chữa lành tìm được: {len(healing_found)}")
for h in healing_found[:15]:
    print(f"  [{h[0]}] {h[1]} ({h[2]}) -> {h[3]}")
