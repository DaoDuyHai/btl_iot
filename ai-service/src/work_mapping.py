import re
import unicodedata
import pandas as pd

def clean_str(val, default: str = "") -> str:
    """Làm sạch chuỗi, tránh ép None/NaN thành chuỗi 'nan' hoặc 'None'."""
    if val is None or pd.isna(val):
        return default
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null"):
        return default
    return s

def extract_base_title(title: str) -> str:
    """Chuẩn hóa tiêu đề sách để gộp các bản sao (copies) nếu có."""
    t = clean_str(title, "")
    # Loại bỏ các hậu tố giả tạo nếu có
    suffix_pattern = r' - (Chuyên Khảo Chuyên Sâu|Phân Tích Ứng Dụng|Góc Nhìn Mới|Thực Hành Toàn Diện|Nghiên Cứu Đột Phá|Tập 2: Mở Rộng|Tập 3: Nâng Cao|Ấn Bản Đặc Biệt)$'
    t = re.sub(suffix_pattern, '', t)
    return t.strip()

def strip_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt chuẩn Unicode phục vụ tìm kiếm không dấu."""
    text = clean_str(text, "")
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text.lower().strip()

def get_work_catalog(df: pd.DataFrame) -> dict:
    """
    Tạo catalog sách cấp độ tác phẩm (Work level).
    Gộp các bản copy cùng tên vào chung một thẻ sách, hiển thị danh sách vị trí trên kệ.
    Đảm bảo không rò rỉ giá trị 'nan' hoặc 'None' khi dữ liệu khuyết thiếu.
    """
    df_copy = df.copy()
    df_copy['base_title'] = df_copy['Title'].apply(extract_base_title)
    
    unique_titles = df_copy['base_title'].unique()
    work_mapping = {}
    for i, t in enumerate(unique_titles, 1):
        wid = f"W{i:04d}"
        sub = df_copy[df_copy['base_title'] == t]
        first_row = sub.iloc[0]
        
        all_copies = []
        for _, r in sub.iterrows():
            pos = clean_str(r.get('Position', ''), 'A1-01')
            shelf = clean_str(r.get('Shelf', ''), 'A')
            floor = int(r.get('Floor', 1)) if pd.notna(r.get('Floor')) else 1
            avail = int(r.get('Available_Copies', 0)) if pd.notna(r.get('Available_Copies')) else 0
            total = int(r.get('Total_Copies', 0)) if pd.notna(r.get('Total_Copies')) else 0
            
            all_copies.append({
                "book_id": clean_str(r['Book_ID']),
                "position": pos,
                "floor": floor,
                "shelf": shelf,
                "available": avail,
                "total": total
            })
            
        work_mapping[wid] = {
            "work_id": wid,
            "base_title": clean_str(t, "Không có tiêu đề"),
            "author": clean_str(first_row.get('Author'), "Không rõ tác giả"),
            "category": clean_str(first_row.get('Category'), "Chưa phân loại"),
            "subcategory": clean_str(first_row.get('Subcategory'), ""),
            "description": clean_str(first_row.get('Description'), ""),
            "keywords": clean_str(first_row.get('Keywords'), ""),
            "publisher": clean_str(first_row.get('Publisher'), ""),
            "publication_year": int(first_row.get('Publication_Year', 2023)) if pd.notna(first_row.get('Publication_Year')) else 2023,
            "total_records": len(sub),
            "copies": all_copies
        }
    return work_mapping
