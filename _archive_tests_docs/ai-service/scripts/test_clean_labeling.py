import re
import pandas as pd
from collections import Counter

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')

# Test filtering and labeling logic
GENERIC_AUTHORS = {"Nhiều tác giả", "Nhóm Tác Giả", "Alpha Books", "NXB Kim Đồng", "WeupBooks", "NXB Trẻ"}

def is_anomalous_author(author, title, desc):
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

# Từ điển nội dung thật sự
KW_RELAX = ["thư giãn", "thảnh thơi", "nghỉ ngơi", "nhâm nhi", "cuối tuần", "thư thái", "an yên", "bình thản", "thanh thản", "nhẹ nhõm", "tô màu cho bé", "giải trí nhẹ nhàng"]
KW_GENTLE = ["nhẹ nhàng", "êm đềm", "ấm áp", "dịu dàng", "trong trẻo", "mộc mạc", "chậm rãi", "bình yên", "tuổi thơ", "hoài niệm", "dành cho bé", "truyện ngắn ấm áp"]
KW_HEALING = ["chữa lành", "tổn thương", "vết thương lòng", "xoa dịu", "vỗ về", "trầm cảm", "nỗi đau", "an ủi", "vượt qua tổn thương", "tự chữa", "bình an nội tâm"]
KW_SUSPENSE = ["trinh thám", "án mạng", "hung thủ", "sát nhân", "vụ án", "kỳ bí", "bí ẩn", "nguy hiểm", "rượt đuổi", "ly kỳ", "gay cấn", "tội ác", "kinh dị", "căng thẳng"]
KW_HUMOR = ["hài hước", "dí dỏm", "hóm hỉnh", "tiếu lâm", "châm biếm", "buồn cười", "tiếng cười", "vui nhộn", "nghịch ngợm", "hồn nhiên", "ngộ nghĩnh"]
KW_MOVING = ["nước mắt", "rơi lệ", "xúc động", "nghẹn ngào", "tình mẫu tử", "tình cha", "hy sinh", "chia ly", "mồ côi", "cảm động", "lòng trắc ẩn", "thương tâm"]
KW_INSPIRING = ["truyền cảm hứng", "động lực", "vươn lên", "ước mơ", "khát vọng", "nghị lực", "thành công", "vượt khó", "thắp sáng", "dấn thân", "bứt phá", "nỗ lực"]
KW_HARD = ["thuật toán", "cấu trúc dữ liệu", "học máy", "trí tuệ nhân tạo", "toán cao cấp", "kinh tế lượng", "lập trình nhúng", "mật mã học", "vi tích phân", "hàn lâm"]

def get_book_labels(row, clean_text):
    title = str(row['Title']).strip()
    cat = str(row['Category']).strip()
    subcat = str(row['Subcategory']).strip()
    full_text = f"{title} {subcat} {clean_text}".lower()
    
    # 1. MOOD TAGS
    moods = []
    
    # Kiểm tra điều kiện cấm cho thư giãn / nhẹ nhàng
    # Không gắn cho Kinh tế, Lịch sử, hoặc sách kỹ thuật CNTT/Khoa học (trừ sách thiếu nhi / tô màu)
    is_children = (cat == "Thiếu nhi") or any(w in full_text for w in ["cho bé", "mầm non", "tô màu", "tranh truyện"])
    is_forbidden_relax = (cat in ["Kinh tế – Kinh doanh", "Lịch sử – Văn hóa"]) or \
                         (cat in ["Công nghệ thông tin", "Khoa học – Công nghệ"] and not is_children)
    
    # Kiểm tra thư giãn / nhẹ nhàng
    has_relax = any(w in full_text for w in KW_RELAX)
    has_gentle = any(w in full_text for w in KW_GENTLE)
    
    if not is_forbidden_relax:
        if has_relax:
            moods.append("thư giãn")
        if has_gentle:
            moods.append("nhẹ nhàng")
        # Subcategory tản văn / thơ nếu có từ gợi cảm xúc nhẹ nhàng
        if ("tản văn" in subcat.lower() or "thơ" in subcat.lower()) and ("nhẹ nhàng" not in moods) and ("thư giãn" not in moods):
            moods.append("nhẹ nhàng")
        if is_children and ("truyện tranh" in subcat.lower() or "thiếu nhi" in subcat.lower()):
            if "nhẹ nhàng" not in moods:
                moods.append("nhẹ nhàng")
                
    # Chữa lành: Chỉ gắn khi có căn cứ rõ
    if any(w in full_text for w in KW_HEALING) and cat not in ["Kinh tế – Kinh doanh", "Công nghệ thông tin", "Lịch sử – Văn hóa"]:
        moods.append("chữa lành")
        
    # Hồi hộp: Trinh thám, án mạng, ly kỳ
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
        
    # Nếu chưa có nhãn nào -> Gán nhãn trung tính chuẩn xác
    if not moods:
        if cat in ["Công nghệ thông tin", "Giáo dục – Ngoại ngữ", "Kinh tế – Kinh doanh"]:
            moods.append("nghiêm túc")
        elif cat in ["Văn học – Tiểu thuyết", "Tâm lý học", "Lịch sử – Văn hóa"]:
            moods.append("suy ngẫm")
        elif cat == "Khoa học – Công nghệ":
            moods.append("nghiêm túc")
        else:
            moods.append("suy ngẫm")
            
    # Bổ sung nghiêm túc hoặc suy ngẫm nếu là chuyên môn mà chưa có
    if cat in ["Công nghệ thông tin", "Giáo dục – Ngoại ngữ"] and "nghiêm túc" not in moods and "nặng đầu" not in moods:
        moods.append("nghiêm túc")
        
    # Giới hạn tối đa 3 mood tags
    mood_tags = ", ".join(moods[:3])
    
    # 2. READING EFFORT
    # Quy tắc: Sách CNTT/Kinh tế/Giáo trình kỹ thuật KHÔNG ĐƯỢC là "nhẹ"!
    if cat in ["Công nghệ thông tin", "Kinh tế – Kinh doanh"]:
        if any(w in full_text for w in KW_HARD) or "giáo trình" in full_text or "lập trình" in full_text or "tài chính" in full_text:
            effort = "nặng"
        else:
            effort = "vừa"
    elif cat == "Giáo dục – Ngoại ngữ":
        if "giáo trình" in full_text or "ielts" in full_text or "hsk" in full_text:
            effort = "nặng"
        else:
            effort = "vừa"
    elif is_children or "tản văn" in subcat.lower() or "thơ" in subcat.lower():
        effort = "nhẹ"
    elif any(w in full_text for w in KW_HARD) or "giáo trình" in full_text:
        effort = "nặng"
    else:
        effort = "vừa"
        
    return mood_tags, effort

relax_books = []
healing_books = []
mood_counts = Counter()
effort_counts = Counter()

for idx, row in df.iterrows():
    c_desc = clean_desc_text(row['Description'])
    mood_str, effort = get_book_labels(row, c_desc)
    effort_counts[effort] += 1
    
    tags = [t.strip() for t in mood_str.split(',')]
    for t in tags:
        mood_counts[t] += 1
        
    if "thư giãn" in tags:
        relax_books.append((row['Book_ID'], row['Title'], row['Category'], mood_str))
    if "chữa lành" in tags:
        healing_books.append((row['Book_ID'], row['Title'], row['Category'], mood_str))

print("THỐNG KÊ MOOD:")
for m, c in mood_counts.most_common():
    print(f"  - {m:<18}: {c:>4} cuốn")

print("\nTHỐNG KÊ EFFORT:")
for e, c in effort_counts.most_common():
    print(f"  - {e:<18}: {c:>4} cuốn")

print(f"\nSố sách mang nhãn 'thư giãn': {len(relax_books)}")
print(f"Số sách mang nhãn 'chữa lành': {len(healing_books)}")
