import os
import sys
import re
import json
import random
import pandas as pd
from collections import Counter

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("CHẠY LẠI BƯỚC 1: LÀM GIÀU DỮ LIỆU SÁCH V2 (CHUẨN HÓA THEO YÊU CẦU)")
print("=" * 80)

DATASET_IN = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'cleaned_books_dataset.csv')
DATASET_OUT = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'books_enriched.csv')
STATS_OUT = os.path.join(os.path.dirname(__file__), '..', 'enrichment_stats_v2.json')
SAMPLES_OUT = os.path.join(os.path.dirname(__file__), '..', 'samples_30_v2.json')
RELAX_HEALING_OUT = os.path.join(os.path.dirname(__file__), '..', 'relax_healing_full.json')

df = pd.read_csv(DATASET_IN)
print(f"[+] Đã tải {len(df)} cuốn sách từ {DATASET_IN}")

# -----------------------------------------------------------------------------
# 1. PHÁT HIỆN VÀ LOẠI BỎ TÁC GIẢ BẤT THƯỜNG / TÁC GIẢ GIẢ
# -----------------------------------------------------------------------------
GENERIC_AUTHORS = {
    "Nhiều tác giả", "Nhóm Tác Giả", "Alpha Books", "NXB Kim Đồng", 
    "WeupBooks", "NXB Trẻ", "Nhiều Tác Giả"
}

def detect_valid_author(author, title, desc, cat):
    """
    Phát hiện tác giả giả mạo hoặc gán hàng loạt:
    - Stephen Hawking: 300 sách Khoa học (chỉ giữ nếu sách thực sự của Stephen Hawking)
    - Daniel Kahneman: 100 sách Tâm lý (chỉ giữ nếu sách thực sự của Daniel Kahneman)
    - Nguyễn Hiến Lê: 150 sách Lịch sử (chỉ giữ nếu sách thực sự của Nguyễn Hiến Lê)
    - Alpha Books, NXB Kim Đồng, WeupBooks: Tên NXB gán vào Author
    - Nhiều tác giả, Nhóm Tác Giả: Tên chung chung
    Trả về: (valid_author: str, is_anomalous: bool, reason: str)
    """
    if not isinstance(author, str) or pd.isna(author):
        return "", True, "Rỗng/None"
    a = author.strip()
    if a in GENERIC_AUTHORS:
        return "", True, "Tên chung hoặc NXB"
        
    t_lower = str(title).lower()
    d_lower = str(desc).lower()
    
    if a == "Stephen Hawking":
        if "stephen hawking" in t_lower or "lược sử thời gian" in t_lower or "vũ trụ trong vỏ hạt dẻ" in t_lower or "bản thiết kế vĩ đại" in t_lower:
            return a, False, "Hợp lệ"
        return "", True, "Stephen Hawking (Gán hàng loạt Khoa học)"
        
    if a == "Daniel Kahneman":
        if "daniel kahneman" in t_lower or "tư duy nhanh và chậm" in t_lower or "nhiễu" in t_lower:
            return a, False, "Hợp lệ"
        return "", True, "Daniel Kahneman (Gán hàng loạt Tâm lý)"
        
    if a == "Nguyễn Hiến Lê":
        if "nguyễn hiến lê" in t_lower or "nguyen hien le" in t_lower or "nguyễn hiến lê" in d_lower[:150]:
            return a, False, "Hợp lệ"
        return "", True, "Nguyễn Hiến Lê (Gán hàng loạt Lịch sử)"
        
    return a, False, "Hợp lệ"

# -----------------------------------------------------------------------------
# 2. LÀM SẠCH DESCRIPTION VÀ TRÍCH XUẤT 1-2 CÂU NỘI DUNG CÓ NGHĨA THẬT
# -----------------------------------------------------------------------------
def clean_description_text(raw_text):
    if not isinstance(raw_text, str) or pd.isna(raw_text):
        return ""
    
    text = raw_text.strip()
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
    """Trích xuất 1-2 câu đầu có nghĩa thật sự của clean_description."""
    if not clean_text:
        return ""
    sentences = [s.strip() for s in re.split(r'[\.\?!]\s+', clean_text) if len(s.strip()) > 15]
    meaningful = []
    for s in sentences:
        s_clean = re.sub(r'^\s*(\d+[\.\:\-]\s*)+', '', s).strip()
        if len(s_clean) >= 20 and not any(kw in s_clean.lower() for kw in ["đặt mua ngay", "freeship", "giá ưu đãi", "mã giảm giá"]):
            meaningful.append(s_clean)
            if len(meaningful) == max_sents:
                break
    if meaningful:
        out = ". ".join(meaningful)
        if not out.endswith('.'):
            out += '.'
        return out
    return clean_text[:150] + ("." if not clean_text.endswith(".") else "")

# -----------------------------------------------------------------------------
# 3. TỪ ĐIỂN VÀ NGUYÊN TẮC GẮN NHÃN TỔNG QUÁT (KHÔNG ÉP ĐOÁN)
# -----------------------------------------------------------------------------
KW_RELAX = [
    "thư giãn", "thảnh thơi", "thư thái", "thư thả", "thong dong", "an nhiên", 
    "tô màu", "xả stress", "giải trí nhẹ nhàng", "nhâm nhi", "cuối tuần thảnh thơi",
    "trước giờ đi ngủ", "chúc bé ngủ ngon", "ru ngủ", "ngủ ngon", "bình yên", 
    "bình an", "yên bình", "sống chậm", "an yên", "thanh thản", "bình dị"
]

KW_GENTLE = [
    "nhẹ nhàng", "êm đềm", "ấm áp", "dịu dàng", "trong trẻo", "mộc mạc", 
    "chậm rãi", "bình yên", "tuổi thơ", "hoài niệm", "dành cho bé", "truyện ngắn ấm áp",
    "tình bạn đẹp", "bình dị", "ngọt ngào", "yên bình"
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

def analyze_book_v2(row, clean_desc, valid_author):
    title = str(row['Title']).strip()
    cat = str(row['Category']).strip()
    subcat = str(row['Subcategory']).strip()
    full_text = f"{title} {subcat} {clean_desc}".lower()
    
    is_children = (cat == "Thiếu nhi") or any(w in full_text for w in ["cho bé", "mầm non", "tô màu", "tranh truyện"])
    is_workplace_or_finance = (cat in ["Kinh tế – Kinh doanh", "Lịch sử – Văn hóa"]) or \
                               any(w in full_text for w in ["chứng khoán", "quản trị", "lãnh đạo", "nhân sự", "đầu tư", "chiến lược", "doanh nghiệp", "thăng tiến", "nhân viên", "văn phòng", "công sở", "sếp", "đồng nghiệp"])
    is_tech = (cat in ["Công nghệ thông tin", "Khoa học – Công nghệ"]) and not is_children
    is_dark_or_suspense = any(w in full_text for w in [
        "quỷ dữ", "hồn oan", "xác quỷ", "thầy pháp", "kinh dị", "chiến khu", "chiến tranh", 
        "tiêu diệt", "tử địa", "sát nhân", "án mạng", "ngã gục", "tự tử", "dây thừng", 
        "hung thủ", "minato kanae", "keigo", "higashino keigo", "agatha christie", 
        "trinh thám", "hung ác", "tội phạm", "tội ác", "rượt đuổi", "vụ án", "ly kỳ", "gay cấn",
        "kẻ địch", "chiến đấu", "quái vật", "đối đầu", "siêu nhân", "ultraman", "vũ khí", "chuyển sinh", "cầu cứu", "slime"
    ]) or "trinh thám" in subcat.lower() or "kiếm hiệp" in subcat.lower()
    
    moods = []
    
    # --- MOOD: Thư giãn & Nhẹ nhàng ---
    # Chỉ gắn khi có căn cứ rõ trong nội dung, KHÔNG gắn cho tài chính, quản trị, khoa học, lịch sử, trinh thám, kinh dị, chiến tranh
    if not is_workplace_or_finance and not is_tech and not is_dark_or_suspense:
        if any(w in full_text for w in KW_RELAX):
            moods.append("thư giãn")
        if any(w in full_text for w in KW_GENTLE):
            moods.append("nhẹ nhàng")
        if "thơ" in subcat.lower() and "nhẹ nhàng" not in moods and "thư giãn" not in moods:
            moods.append("nhẹ nhàng")
            
    # --- MOOD: Chữa lành ---
    # Phải có căn cứ nội dung rõ rệt, không phải trinh thám giết người, không phải quản trị/kỹ thuật
    if not is_workplace_or_finance and not is_tech and not is_dark_or_suspense:
        if any(w in full_text for w in KW_HEALING):
            if not any(w in full_text for w in ["tâm thần phân liệt", "bệnh nhân tâm thần", "giết người"]):
                moods.append("chữa lành")
                
    # --- MOOD: Hồi hộp ---
    if is_dark_or_suspense:
        moods.append("hồi hộp")
        
    # --- MOOD: Hài hước & Vui vẻ ---
    if any(w in full_text for w in KW_HUMOR):
        moods.append("hài hước")
        if "vui vẻ" not in moods:
            moods.append("vui vẻ")
    elif is_children:
        moods.append("vui vẻ")
        
    # --- MOOD: Cảm động ---
    if any(w in full_text for w in KW_MOVING):
        moods.append("cảm động")
        
    # --- MOOD: Truyền cảm hứng ---
    if any(w in full_text for w in KW_INSPIRING) or "động lực" in subcat.lower() or "tư duy tích cực" in subcat.lower():
        moods.append("truyền cảm hứng")
        
    # --- MOOD: Nặng đầu ---
    if any(w in full_text for w in KW_HARD) and cat in ["Công nghệ thông tin", "Khoa học – Công nghệ", "Kinh tế – Kinh doanh"]:
        moods.append("nặng đầu")
        
    # --- MOOD TRUNG TÍNH (Khi chưa đủ căn cứ, không ép đoán) ---
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
    
    # --- READING EFFORT ---
    # Sách CNTT/Kinh tế/Giáo trình kỹ thuật KHÔNG ĐƯỢC là "nhẹ"!
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
        
    # --- AUDIENCE ---
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
        
    # --- INTENT ---
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
        
    # --- SUMMARY_VI: 1-2 CÂU THỰC SỰ TỪ NỘI DUNG SÁCH (CẤM CÂU KHUÔN MẪU!) ---
    summary_vi = extract_meaningful_sentences(clean_desc, max_sents=2)
    
    # --- SEARCH_TEXT: KHÔNG CÓ KHUÔN MẪU, KHÔNG CÓ TÁC GIẢ GIẢ ---
    author_str = f"của {valid_author}. " if valid_author else ""
    desc_snippet = extract_meaningful_sentences(clean_desc, max_sents=2)
    search_text = f"{title}. {author_str}Thể loại: {cat} - {subcat}. {desc_snippet} Tâm trạng: {mood_tags}. Nỗ lực đọc: {effort}. Đối tượng: {audience}."
    search_text = re.sub(r'\s+', ' ', search_text).strip()
    
    return {
        "valid_author": valid_author,
        "clean_description": clean_desc,
        "summary_vi": summary_vi,
        "mood_tags": mood_tags,
        "reader_intent": intent,
        "reading_effort": effort,
        "audience": audience,
        "search_text": search_text
    }

# -----------------------------------------------------------------------------
# 4. CHẠY LÀM GIÀU CHO TOÀN BỘ 3,000 SÁCH
# -----------------------------------------------------------------------------
enriched_rows = []
anomalous_stats = {}
relax_books = []
healing_books = []

for idx, row in df.iterrows():
    raw_desc = row.get('Description', '')
    raw_author = row.get('Author', '')
    raw_title = row.get('Title', '')
    raw_cat = row.get('Category', '')
    
    valid_author, is_anom, reason = detect_valid_author(raw_author, raw_title, raw_desc, raw_cat)
    if is_anom:
        anomalous_stats[str(raw_author).strip()] = anomalous_stats.get(str(raw_author).strip(), 0) + 1
        
    c_desc = clean_description_text(raw_desc)
    enrichment = analyze_book_v2(row, c_desc, valid_author)
    
    # Giữ nguyên toàn bộ 15 cột ban đầu + thêm các cột enriched
    merged = row.to_dict()
    merged.update(enrichment)
    enriched_rows.append(merged)
    
    # Thu thập sách thư giãn và chữa lành để phục vụ in toàn bộ
    moods_list = [m.strip() for m in enrichment['mood_tags'].split(',')]
    one_sent = extract_meaningful_sentences(c_desc, max_sents=1)
    if "thư giãn" in moods_list:
        relax_books.append({
            "book_id": row['Book_ID'],
            "title": raw_title,
            "category": raw_cat,
            "mood_tags": enrichment['mood_tags'],
            "first_sentence_clean_desc": one_sent
        })
    if "chữa lành" in moods_list:
        healing_books.append({
            "book_id": row['Book_ID'],
            "title": raw_title,
            "category": raw_cat,
            "mood_tags": enrichment['mood_tags'],
            "first_sentence_clean_desc": one_sent
        })

df_enriched = pd.DataFrame(enriched_rows)
df_enriched.to_csv(DATASET_OUT, index=False, encoding='utf-8')
print(f"[+] Đã lưu {len(df_enriched)} cuốn sách vào {DATASET_OUT}")

# -----------------------------------------------------------------------------
# 5. TÍNH TOÁN THỐNG KÊ CHI TIẾT
# -----------------------------------------------------------------------------
all_mood_tokens = []
for m_str in df_enriched['mood_tags']:
    tokens = [t.strip() for t in m_str.split(',') if t.strip()]
    all_mood_tokens.extend(tokens)
mood_counts = {k: int(v) for k, v in Counter(all_mood_tokens).items()}

effort_counts = {k: int(v) for k, v in df_enriched['reading_effort'].value_counts().items()}
audience_counts = {k: int(v) for k, v in df_enriched['audience'].value_counts().items()}
intent_counts = {k: int(v) for k, v in df_enriched['reader_intent'].value_counts().items()}

# Kiểm tra câu khuôn mẫu
template_summaries = int(df_enriched['summary_vi'].str.contains("Tác phẩm thuộc thể loại", na=False).sum())
template_search_text = int(df_enriched['search_text'].str.contains("Tác phẩm thuộc thể loại", na=False).sum())

stats = {
    "total_books": len(df_enriched),
    "anomalous_authors_count": sum(anomalous_stats.values()),
    "anomalous_authors_detail": anomalous_stats,
    "template_summaries_in_summary_vi": template_summaries,
    "template_summaries_in_search_text": template_search_text,
    "mood_counts": mood_counts,
    "reading_effort_counts": effort_counts,
    "audience_counts": audience_counts,
    "reader_intent_counts": intent_counts,
    "total_relax_books": len(relax_books),
    "total_healing_books": len(healing_books)
}

with open(STATS_OUT, 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

with open(RELAX_HEALING_OUT, 'w', encoding='utf-8') as f:
    json.dump({"relax_books": relax_books, "healing_books": healing_books}, f, ensure_ascii=False, indent=2)

# -----------------------------------------------------------------------------
# 6. TRÍCH XUẤT 30 SÁCH NGẪU NHIÊN MỚI VỚI SEED 2026
# -----------------------------------------------------------------------------
random.seed(2026)
target_per_cat = {
    "Văn học – Tiểu thuyết": 4,
    "Công nghệ thông tin": 4,
    "Kinh tế – Kinh doanh": 4,
    "Giáo dục – Ngoại ngữ": 4,
    "Kỹ năng sống – Phát triển bản thân": 3,
    "Khoa học – Công nghệ": 3,
    "Thiếu nhi": 3,
    "Lịch sử – Văn hóa": 3,
    "Tâm lý học": 2
} # Tổng 30 cuốn

samples_30_v2 = []
for cat, count in target_per_cat.items():
    cat_df = df_enriched[df_enriched['Category'] == cat]
    sampled = cat_df.sample(n=min(count, len(cat_df)), random_state=2026)
    for _, row in sampled.iterrows():
        raw_d = str(row['Description'])
        short_desc = raw_d[:120] + "..." if len(raw_d) > 120 else raw_d
        samples_30_v2.append({
            "book_id": row['Book_ID'],
            "title": row['Title'],
            "author": row['Author'],
            "valid_author": row['valid_author'],
            "category": row['Category'],
            "subcategory": row['Subcategory'],
            "raw_desc_short": short_desc,
            "summary_vi": row['summary_vi'],
            "mood_tags": row['mood_tags'],
            "reading_effort": row['reading_effort'],
            "audience": row['audience']
        })

with open(SAMPLES_OUT, 'w', encoding='utf-8') as f:
    json.dump(samples_30_v2, f, ensure_ascii=False, indent=2)

print(f"[+] Hoàn tất! Đã lưu 30 mẫu seed 2026 vào {SAMPLES_OUT}")
print(f"[+] Số câu khuôn mẫu trong summary_vi: {template_summaries}")
print(f"[+] Số câu khuôn mẫu trong search_text: {template_search_text}")
print(f"[+] Số tác giả giả/bất thường bị loại: {sum(anomalous_stats.values())}")
print(f"[+] Số sách thư giãn: {len(relax_books)}, Số sách chữa lành: {len(healing_books)}")
