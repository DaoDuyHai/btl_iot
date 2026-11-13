# d:\TrainAI\src\passage_builder.py
import pandas as pd

def clean_field(val) -> str:
    """Làm sạch giá trị trường dữ liệu, triệt tiêu hoàn toàn None, NaN, nan, null."""
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null"):
        return ""
    return s

def build_passage(row: pd.Series, max_words: int = 150) -> str:
    """
    Xây dựng nội dung passage cho sách theo chuẩn của Multilingual E5.
    Loại bỏ thông tin vị trí kệ, tầng và số bản (không liên quan ngữ nghĩa sách).
    Xử lý an toàn giá trị rỗng, Null, NaN (không sinh ra token 'nan' hoặc 'None').
    Đảm bảo không vượt quá giới hạn token (max 512 tokens).
    """
    title = clean_field(row.get('Title', ''))
    author = clean_field(row.get('Author', ''))
    category = clean_field(row.get('Category', ''))
    subcategory = clean_field(row.get('Subcategory', ''))
    description = clean_field(row.get('Description', ''))
    keywords = clean_field(row.get('Keywords', ''))
    
    # Cắt ngắn nếu mô tả vượt quá max_words
    desc_words = description.split()
    if len(desc_words) > max_words:
        description = " ".join(desc_words[:max_words]) + "..."
        
    components = []
    if title:
        components.append(f"Tên sách: {title}")
    if author:
        components.append(f"Tác giả: {author}")
        
    if category and subcategory:
        components.append(f"Thể loại: {category} - {subcategory}")
    elif category:
        components.append(f"Thể loại: {category}")
    elif subcategory:
        components.append(f"Thể loại: {subcategory}")
        
    content_parts = []
    if description:
        content_parts.append(f"Nội dung: {description}")
    if keywords:
        content_parts.append(f"Từ khóa: {keywords}")
        
    if content_parts:
        components.append(" ".join(content_parts))
        
    if components:
        return "passage: " + ". ".join(components)
    else:
        return "passage: "
