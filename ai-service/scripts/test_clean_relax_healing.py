import re
import pandas as pd

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')

def clean_desc_text(raw_desc):
    if not isinstance(raw_desc, str) or pd.isna(raw_desc):
        return ""
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
    return text

def extract_meaningful_sentences(clean_text, max_sents=2):
    if not clean_text:
        return ""
    sentences = [s.strip() for s in re.split(r'[\.\?!]\s+', clean_text) if len(s.strip()) > 15]
    res = []
    for s in sentences:
        s_clean = re.sub(r'^\s*(\d+[\.\:\-]\s*)+', '', s).strip()
        if len(s_clean) >= 20 and not any(kw in s_clean.lower() for kw in ["đặt mua ngay", "freeship", "giá ưu đãi", "mã giảm giá"]):
            res.append(s_clean)
            if len(res) == max_sents:
                break
    if res:
        out = ". ".join(res)
        if not out.endswith('.'):
            out += '.'
        return out
    return clean_text[:150] + ("." if not clean_text.endswith(".") else "")

KW_RELAX = [
    "thư giãn", "thảnh thơi", "thư thái", "thư thả", "thong dong", "an nhiên", 
    "tô màu", "xả stress", "giải trí nhẹ nhàng", "nhâm nhi", "cuối tuần thảnh thơi",
    "trước giờ đi ngủ", "chúc bé ngủ ngon", "ru ngủ", "ngủ ngon", "bình yên", 
    "bình an", "yên bình", "sống chậm", "an yên", "thanh thản", "bình dị"
]

KW_HEALING = [
    "chữa lành", "xoa dịu", "vỗ về", "an ủi", "vết thương lòng", "tự chữa lành", 
    "bình an nội tâm", "xoa dịu tâm hồn", "vết thương tâm hồn", "ôm lấy chính mình",
    "vượt qua tổn thương"
]

KW_SUSPENSE = [
    "trinh thám", "án mạng", "hung thủ", "sát nhân", "vụ án", "kỳ bí", "bí ẩn", 
    "nguy hiểm", "rượt đuổi", "ly kỳ", "gay cấn", "tội ác", "kinh dị", "căng thẳng",
    "giết người", "máu me"
]

KW_HUMOR = [
    "hài hước", "dí dỏm", "hóm hỉnh", "tiếu lâm", "châm biếm", "buồn cười", 
    "tiếng cười", "vui nhộn", "nghịch ngợm", "hồn nhiên", "ngộ nghĩnh", "cười ra nước mắt"
]

KW_MOVING = [
    "nước mắt", "rơi lệ", "xúc động", "nghẹn ngào", "tình mẫu tử", "tình cha", 
    "hy sinh", "chia ly", "mồ côi", "cảm động", "lòng trắc ẩn", "thương tâm", "rớt nước mắt"
]

KW_INSPIRING = [
    "truyền cảm hứng", "động lực", "vươn lên", "ước mơ", "khát vọng", "nghị lực", 
    "thành công", "vượt khó", "thắp sáng", "dấn thân", "bứt phá", "nỗ lực vươn lên"
]

KW_HARD = [
    "thuật toán", "cấu trúc dữ liệu", "học máy", "trí tuệ nhân tạo", "toán cao cấp", 
    "kinh tế lượng", "lập trình nhúng", "mật mã học", "vi tích phân", "hàn lâm", "chuyên sâu"
]

relax_records = []
healing_records = []

for idx, row in df.iterrows():
    c_desc = clean_desc_text(row['Description'])
    title = str(row['Title']).strip()
    cat = str(row['Category']).strip()
    subcat = str(row['Subcategory']).strip()
    full_text = f"{title} {subcat} {c_desc}".lower()
    
    is_children = (cat == "Thiếu nhi") or any(w in full_text for w in ["cho bé", "mầm non", "tô màu", "tranh truyện"])
    is_workplace_or_finance = (cat in ["Kinh tế – Kinh doanh", "Lịch sử – Văn hóa"]) or \
                               any(w in full_text for w in ["chứng khoán", "quản trị", "lãnh đạo", "nhân sự", "đầu tư", "chiến lược", "doanh nghiệp", "thăng tiến"])
    is_tech = (cat in ["Công nghệ thông tin", "Khoa học – Công nghệ"]) and not is_children
    is_suspense = any(w in full_text for w in KW_SUSPENSE) or "trinh thám" in subcat.lower() or "kiếm hiệp" in subcat.lower()
    
    moods = []
    
    # Thư giãn
    if not is_workplace_or_finance and not is_tech and not is_suspense:
        if any(w in full_text for w in KW_RELAX):
            moods.append("thư giãn")
        if any(w in full_text for w in ["nhẹ nhàng", "êm đềm", "ấm áp", "dịu dàng", "trong trẻo", "mộc mạc", "chậm rãi"]):
            moods.append("nhẹ nhàng")
        if "thơ" in subcat.lower() and "nhẹ nhàng" not in moods and "thư giãn" not in moods:
            moods.append("nhẹ nhàng")
            
    # Chữa lành
    if not is_workplace_or_finance and not is_tech and not is_suspense:
        if any(w in full_text for w in KW_HEALING):
            if not any(w in full_text for w in ["tâm thần phân liệt", "bệnh nhân tâm thần"]):
                moods.append("chữa lành")
                
    first_sent = extract_meaningful_sentences(c_desc, max_sents=1)
    
    if "thư giãn" in moods:
        relax_records.append({"book_id": row['Book_ID'], "title": title, "category": cat, "mood_tags": ", ".join(moods), "first_sentence": first_sent})
    if "chữa lành" in moods:
        healing_records.append({"book_id": row['Book_ID'], "title": title, "category": cat, "mood_tags": ", ".join(moods), "first_sentence": first_sent})

print(f"Tổng số sách THƯ GIÃN: {len(relax_records)}")
print(f"Tổng số sách CHỮA LÀNH: {len(healing_records)}")
