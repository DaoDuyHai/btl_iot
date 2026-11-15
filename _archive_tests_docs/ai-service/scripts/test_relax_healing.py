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

def extract_first_meaningful_sentence(clean_text, title=""):
    if not clean_text:
        return ""
    sentences = [s.strip() for s in re.split(r'[\.\?!]\s+', clean_text) if len(s.strip()) > 15]
    for s in sentences:
        s_clean = re.sub(r'^\s*(\d+[\.\:\-]\s*)+', '', s).strip()
        if len(s_clean) >= 20 and not any(kw in s_clean.lower() for kw in ["đặt mua ngay", "freeship", "giá ưu đãi", "mã giảm giá"]):
            if not s_clean.endswith('.'):
                s_clean += '.'
            return s_clean
    return clean_text[:150] + ("." if not clean_text.endswith(".") else "")

# Từ khóa căn cứ rõ ràng
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
    "chữa lành", "tổn thương", "vết thương lòng", "xoa dịu", "vỗ về", "trầm cảm", 
    "nỗi đau", "an ủi", "vượt qua tổn thương", "tự chữa lành", "bình an nội tâm",
    "ôm lấy", "xoa dịu tâm hồn", "vết thương tâm hồn"
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

def analyze_candidate(row, c_desc):
    title = str(row['Title']).strip()
    cat = str(row['Category']).strip()
    subcat = str(row['Subcategory']).strip()
    full_text = f"{title} {subcat} {c_desc}".lower()
    
    is_children = (cat == "Thiếu nhi") or any(w in full_text for w in ["cho bé", "mầm non", "tô màu", "tranh truyện"])
    # Cấm gán thư giãn / nhẹ nhàng cho Kinh tế, Lịch sử, hoặc sách kỹ thuật CNTT/Khoa học
    is_forbidden_relax = (cat in ["Kinh tế – Kinh doanh", "Lịch sử – Văn hóa"]) or \
                         (cat in ["Công nghệ thông tin", "Khoa học – Công nghệ"] and not is_children)
                         
    moods = []
    
    # Thư giãn / Nhẹ nhàng
    if not is_forbidden_relax:
        if any(w in full_text for w in KW_RELAX):
            moods.append("thư giãn")
        if any(w in full_text for w in KW_GENTLE):
            moods.append("nhẹ nhàng")
        # Tản văn / Thơ ca / Truyện tranh thiếu nhi nếu có chất liệu nhẹ nhàng
        if "thơ" in subcat.lower() and "nhẹ nhàng" not in moods and "thư giãn" not in moods:
            moods.append("nhẹ nhàng")
            
    # Chữa lành: Chỉ gắn khi có căn cứ rõ
    if any(w in full_text for w in KW_HEALING) and cat not in ["Kinh tế – Kinh doanh", "Công nghệ thông tin", "Lịch sử – Văn hóa"]:
        moods.append("chữa lành")
        
    # Hồi hộp
    if any(w in full_text for w in KW_SUSPENSE) or "trinh thám" in subcat.lower() or "kiếm hiệp" in subcat.lower():
        moods.append("hồi hộp")
        
    # Hài hước / Vui vẻ
    if any(w in full_text for w in KW_HUMOR):
        moods.append("hài hước")
        if "vui vẻ" not in moods:
            moods.append("vui vẻ")
    elif is_children:
        moods.append("vui vẻ")
        
    # Cảm động
    if any(w in full_text for w in KW_MOVING):
        moods.append("cảm động")
        
    # Truyền cảm hứng
    if any(w in full_text for w in KW_INSPIRING) or "động lực" in subcat.lower() or "tư duy tích cực" in subcat.lower():
        moods.append("truyền cảm hứng")
        
    # Nặng đầu
    if any(w in full_text for w in KW_HARD) and cat in ["Công nghệ thông tin", "Khoa học – Công nghệ", "Kinh tế – Kinh doanh"]:
        moods.append("nặng đầu")
        
    # Trung tính nếu chưa có
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
        
    return moods[:3]

relax_list = []
healing_list = []

for idx, row in df.iterrows():
    c_desc = clean_desc_text(row['Description'])
    moods = analyze_candidate(row, c_desc)
    bid = row['Book_ID']
    title = row['Title']
    cat = row['Category']
    one_sent = extract_first_meaningful_sentence(c_desc, title)
    
    if "thư giãn" in moods:
        relax_list.append((bid, title, cat, ", ".join(moods), one_sent))
    if "chữa lành" in moods:
        healing_list.append((bid, title, cat, ", ".join(moods), one_sent))

print(f"Tổng số sách mang nhãn THƯ GIÃN: {len(relax_list)}")
print(f"Tổng số sách mang nhãn CHỮA LÀNH: {len(healing_list)}")

print("\n--- 5 SÁCH THƯ GIÃN ĐẦU TIÊN ---")
for b in relax_list[:5]:
    print(f"[{b[0]}] {b[1]} ({b[2]}) -> Moods: {b[3]}\n   1st sent: {b[4]}\n")

print("\n--- 5 SÁCH CHỮA LÀNH ĐẦU TIÊN ---")
for b in healing_list[:5]:
    print(f"[{b[0]}] {b[1]} ({b[2]}) -> Moods: {b[3]}\n   1st sent: {b[4]}\n")
