import re
import pandas as pd
from collections import Counter

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')

# 1. anomalous author detection
GENERIC_AUTHORS = {"Nhiều tác giả", "Nhóm Tác Giả", "Alpha Books", "NXB Kim Đồng", "WeupBooks", "NXB Trẻ"}

def is_fake_author(author, title, desc, cat):
    if not isinstance(author, str) or pd.isna(author):
        return True
    a = author.strip()
    if a in GENERIC_AUTHORS:
        return True
    t_lower = str(title).lower()
    d_lower = str(desc).lower()
    if a == "Stephen Hawking":
        return not ("stephen hawking" in t_lower or "lược sử thời gian" in t_lower or "vũ trụ trong vỏ hạt dẻ" in t_lower)
    if a == "Daniel Kahneman":
        return not ("daniel kahneman" in t_lower or "tư duy nhanh và chậm" in t_lower or "nhiễu" in t_lower)
    if a == "Nguyễn Hiến Lê":
        return not ("nguyễn hiến lê" in t_lower or "nguyen hien le" in t_lower or "nguyễn hiến lê" in d_lower[:150])
    return False

# 2. clean description
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

# 3. Grounded lexicons
KW_RELAX = [
    "thư giãn", "thảnh thơi", "thư thái", "thư thả", "thong dong", "an nhiên", 
    "tô màu", "xả stress", "giải trí nhẹ nhàng", "nhâm nhi", "cuối tuần thảnh thơi",
    "trước giờ đi ngủ", "chúc bé ngủ ngon", "ru ngủ", "ngủ ngon"
]

KW_GENTLE = [
    "nhẹ nhàng", "êm đềm", "ấm áp", "dịu dàng", "trong trẻo", "mộc mạc", 
    "chậm rãi", "bình yên", "tuổi thơ", "hoài niệm", "dành cho bé", "truyện ngắn ấm áp",
    "tình bạn đẹp", "bình dị", "ngọt ngào", "yên bình"
]

KW_HEALING = [
    "chữa lành", "xoa dịu", "vỗ về", "an ủi", "vết thương lòng", "tổn thương",
    "vượt qua tổn thương", "tự chữa lành", "bình an nội tâm", "xoa dịu tâm hồn", 
    "vết thương tâm hồn", "ôm lấy chính mình"
]

KW_SUSPENSE = [
    "trinh thám", "án mạng", "hung thủ", "sát nhân", "vụ án", "kỳ bí", "bí ẩn", 
    "nguy hiểm", "rượt đuổi", "ly kỳ", "gay cấn", "tội ác", "kinh dị", "căng thẳng"
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

def analyze_book_strict(row, clean_text):
    title = str(row['Title']).strip()
    cat = str(row['Category']).strip()
    subcat = str(row['Subcategory']).strip()
    full_text = f"{title} {subcat} {clean_text}".lower()
    
    is_children = (cat == "Thiếu nhi") or any(w in full_text for w in ["cho bé", "mầm non", "tô màu", "tranh truyện"])
    is_workplace_or_finance = (cat in ["Kinh tế – Kinh doanh", "Lịch sử – Văn hóa"]) or \
                               any(w in full_text for w in ["chứng khoán", "quản trị", "lãnh đạo", "nhân sự", "đầu tư", "chiến lược", "doanh nghiệp", "thăng tiến"])
    is_tech = (cat in ["Công nghệ thông tin", "Khoa học – Công nghệ"]) and not is_children
    
    moods = []
    
    # 1. Thư giãn & Nhẹ nhàng
    if not is_workplace_or_finance and not is_tech:
        if any(w in full_text for w in KW_RELAX):
            moods.append("thư giãn")
        if any(w in full_text for w in KW_GENTLE):
            moods.append("nhẹ nhàng")
        if "thơ" in subcat.lower() and "nhẹ nhàng" not in moods and "thư giãn" not in moods:
            moods.append("nhẹ nhàng")
            
    # 2. Chữa lành (Chỉ khi có căn cứ rõ và không phải sách quản trị / kỹ thuật)
    if not is_workplace_or_finance and not is_tech:
        if any(w in full_text for w in KW_HEALING):
            # Kiểm tra ngoại trừ trường hợp bệnh nhân tâm thần hoặc sách y học đơn thuần
            if not any(w in full_text for w in ["tâm thần phân liệt", "bệnh nhân tâm thần"]):
                moods.append("chữa lành")
                
    # 3. Hồi hộp
    if any(w in full_text for w in KW_SUSPENSE) or "trinh thám" in subcat.lower() or "kiếm hiệp" in subcat.lower():
        moods.append("hồi hộp")
        
    # 4. Hài hước / Vui vẻ
    if any(w in full_text for w in KW_HUMOR):
        moods.append("hài hước")
        if "vui vẻ" not in moods:
            moods.append("vui vẻ")
    elif is_children:
        moods.append("vui vẻ")
        
    # 5. Cảm động
    if any(w in full_text for w in KW_MOVING):
        moods.append("cảm động")
        
    # 6. Truyền cảm hứng
    if any(w in full_text for w in KW_INSPIRING) or "động lực" in subcat.lower() or "tư duy tích cực" in subcat.lower():
        moods.append("truyền cảm hứng")
        
    # 7. Nặng đầu
    if any(w in full_text for w in KW_HARD) and cat in ["Công nghệ thông tin", "Khoa học – Công nghệ", "Kinh tế – Kinh doanh"]:
        moods.append("nặng đầu")
        
    # 8. Trung tính (nếu chưa có mood nào)
    if not moods:
        if cat in ["Công nghệ thông tin", "Giáo dục – Ngoại ngữ", "Kinh tế – Kinh doanh"]:
            moods.append("nghiêm túc")
        elif cat in ["Văn học – Tiểu thuyết", "Tâm lý học", "Lịch sử – Văn hóa"]:
            moods.append("suy ngẫm")
        elif cat == "Khoa học – Công nghệ":
            moods.append("nghiêm túc")
        else:
            moods.append("suy ngẫm")
            
    if cat in ["Công nghệ thông tin", "Giáo dục – Ngoại ngữ"] and "nghiêm túc" not in moods and "nặng đầu" not in moods:
        moods.append("nghiêm túc")
        
    mood_tags = ", ".join(moods[:3])
    
    # 9. Reading Effort
    # Sách CNTT/Kinh tế/Giáo trình kỹ thuật KHÔNG ĐƯỢC là "nhẹ"
    if cat in ["Công nghệ thông tin", "Kinh tế – Kinh doanh"]:
        if any(w in full_text for w in KW_HARD) or "giáo trình" in full_text or "lập trình" in full_text or "tài chính" in full_text or "thuật toán" in full_text:
            effort = "nặng"
        else:
            effort = "vừa"
    elif cat == "Giáo dục – Ngoại ngữ":
        if "giáo trình" in full_text or "ielts" in full_text or "hsk" in full_text or "toeic" in full_text:
            effort = "nặng"
        else:
            effort = "vừa"
    elif is_children or "thơ" in subcat.lower() or ("tản văn" in subcat.lower() and "nhẹ nhàng" in moods):
        effort = "nhẹ"
    elif any(w in full_text for w in KW_HARD) or "giáo trình" in full_text:
        effort = "nặng"
    else:
        effort = "vừa"
        
    # 10. Audience
    if is_children:
        audience = "trẻ em"
    elif any(w in full_text for w in ["học sinh", "lớp 10", "lớp 11", "lớp 12", "thi thpt", "tuổi teen"]):
        audience = "học sinh"
    elif cat in ["Công nghệ thông tin", "Giáo dục – Ngoại ngữ"] or "giáo trình" in full_text or "đại học" in full_text:
        audience = "sinh viên"
    elif is_workplace_or_finance or cat == "Kinh tế – Kinh doanh":
        audience = "người đi làm"
    else:
        audience = "mọi người"
        
    # 11. Intent
    if "ôn thi" in full_text or any(w in full_text for w in ["ielts", "toeic", "hsk", "topik", "đề thi"]):
        intent = "ôn thi"
    elif any(w in full_text for w in ["tra cứu", "sổ tay", "từ điển", "bách khoa"]):
        intent = "tra cứu"
    elif cat in ["Công nghệ thông tin", "Giáo dục – Ngoại ngữ"] or "giáo trình" in full_text:
        intent = "học tập"
    elif is_workplace_or_finance or any(w in full_text for w in ["kỹ năng", "thực hành", "phương pháp", "bí quyết"]):
        intent = "nâng cao kỹ năng"
    elif any(w in full_text for w in ["cảm hứng", "động lực", "thức tỉnh", "vươn lên"]):
        intent = "tìm cảm hứng"
    elif is_children:
        intent = "đọc cùng con" if "cùng con" in full_text or "cho bé" in full_text else "giải trí"
    else:
        intent = "giải trí"
        
    return mood_tags, effort, audience, intent

relax_records = []
healing_records = []

for idx, row in df.iterrows():
    c_desc = clean_desc_text(row['Description'])
    moods, eff, aud, it = analyze_book_strict(row, c_desc)
    bid = row['Book_ID']
    title = row['Title']
    cat = row['Category']
    first_sent = extract_meaningful_sentences(c_desc, max_sents=1)
    
    if "thư giãn" in moods:
        relax_records.append({"book_id": bid, "title": title, "category": cat, "mood_tags": moods, "first_sentence": first_sent})
    if "chữa lành" in moods:
        healing_records.append({"book_id": bid, "title": title, "category": cat, "mood_tags": moods, "first_sentence": first_sent})

print(f"Tổng số sách THƯ GIÃN: {len(relax_records)}")
print(f"Tổng số sách CHỮA LÀNH: {len(healing_records)}")
