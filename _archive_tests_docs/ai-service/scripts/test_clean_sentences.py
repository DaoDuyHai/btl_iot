import pandas as pd
import re

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')

def extract_meaningful_sentences(raw_desc, title=""):
    if not isinstance(raw_desc, str) or pd.isna(raw_desc):
        return ""
    
    # Làm sạch
    text = raw_desc.strip()
    text = re.sub(r'THÔNG TIN (XUẤT BẢN|CHI TIẾT)[\s\S]*?(ISBN|Barcode|Giá bìa|Trọng lượng|Số trang):.*?(?=(\n\n|\.\s|\Z))', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(ISBN|Barcode|Giá bìa|Trọng lượng|Số trang|Kích thước|Định dạng|Ngày phát hành):\s*[^\n\.]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(GIỚI THIỆU (NỘI DUNG|SÁCH|TÁC PHẨM)|NỘI DUNG CHÍNH|TỔNG QUAN)\s*(\d+[\.:])?:?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(TB (tăng giá|\d+[\.,\d]*\s*VNĐ|\d+[\.,\d]*)\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'–?\s*(Huy Hoàng Bookstore|NXB Trẻ|Alpha Books|Cẩm Phong Books|Kim Đồng|Nhã Nam|First News)[^–\.\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Một vài câu nói nổi tiếng của [^:]+:\s*“[^”]*”\s*', '', text)
    text = re.sub(r'“([A-Za-z\s,\.\?!\-]{25,})”', '', text)
    text = re.sub(r'"([A-Za-z\s,\.\?!\-]{25,})"', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^\s*[\-–\.,:;]\s*', '', text)
    
    # Tách câu
    sentences = [s.strip() for s in re.split(r'[\.\?!]\s+', text) if len(s.strip()) > 15]
    meaningful = []
    for s in sentences:
        s_clean = re.sub(r'^\s*(\d+[\.\:\-]\s*)+', '', s).strip()
        # Bỏ qua câu ngắn hoặc chỉ chứa từ rác quảng cáo
        if len(s_clean) >= 20 and not any(kw in s_clean.lower() for kw in ["đặt mua ngay", "freeship", "giá ưu đãi", "mã giảm giá"]):
            meaningful.append(s_clean)
        if len(meaningful) == 2:
            break
            
    if meaningful:
        res = ". ".join(meaningful)
        if not res.endswith('.'):
            res += '.'
        return res
    return text[:200]

with_sentences = 0
for idx, row in df.iterrows():
    s = extract_meaningful_sentences(row['Description'], row['Title'])
    if len(s) > 20:
        with_sentences += 1

print(f"Số sách trích xuất được 1-2 câu nội dung có nghĩa thật: {with_sentences} / {len(df)}")
