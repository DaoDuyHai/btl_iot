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
print("BẮT ĐẦU BƯỚC 1: LÀM GIÀU DỮ LIỆU SÁCH (DATA ENRICHMENT)")
print("=" * 80)

DATASET_IN = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'cleaned_books_dataset.csv')
DATASET_OUT = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'books_enriched.csv')
STATS_OUT = os.path.join(os.path.dirname(__file__), '..', 'enrichment_stats.json')
SAMPLES_OUT = os.path.join(os.path.dirname(__file__), '..', 'samples_30.json')

df = pd.read_csv(DATASET_IN)
print(f"[+] Đã tải {len(df)} cuốn sách từ {DATASET_IN}")

# -----------------------------------------------------------------------------
# 1. CLEAN DESCRIPTION
# -----------------------------------------------------------------------------
def clean_description_text(raw_text, title=""):
    if not isinstance(raw_text, str) or pd.isna(raw_text):
        return ""
    
    text = raw_text.strip()
    
    # Loại bỏ metadata xuất bản (ISBN, Barcode, Giá bìa, v.v.)
    text = re.sub(r'THÔNG TIN (XUẤT BẢN|CHI TIẾT)[\s\S]*?(ISBN|Barcode|Giá bìa|Trọng lượng|Số trang):.*?(?=(\n\n|\.\s|\Z))', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(ISBN|Barcode|Giá bìa|Trọng lượng|Số trang|Kích thước|Định dạng|Ngày phát hành):\s*[^\n\.]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(GIỚI THIỆU (NỘI DUNG|SÁCH|TÁC PHẨM)|NỘI DUNG CHÍNH|TỔNG QUAN)\s*(\d+[\.:])?:?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(TB (tăng giá|\d+[\.,\d]*\s*VNĐ|\d+[\.,\d]*)\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'–?\s*(Huy Hoàng Bookstore|NXB Trẻ|Alpha Books|Cẩm Phong Books|Kim Đồng|Nhã Nam|First News)[^–\.\n]*', '', text, flags=re.IGNORECASE)
    
    # Loại bỏ trích dẫn tiếng Anh dài trong ngoặc kép hoặc sau "nổi tiếng của...:"
    text = re.sub(r'Một vài câu nói nổi tiếng của [^:]+:\s*“[^”]*”\s*', '', text)
    text = re.sub(r'“([A-Za-z\s,\.\?!\-]{25,})”', '', text)
    text = re.sub(r'"([A-Za-z\s,\.\?!\-]{25,})"', '', text)
    
    # Chuẩn hóa khoảng trắng và dấu câu
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^\s*[\-–\.,:;]\s*', '', text)
    
    # Nếu sau khi lọc quá ngắn (< 30 ký tự), giữ lại tóm tắt ngắn từ title hoặc text gốc
    if len(text) < 30 and len(raw_text.strip()) >= 30:
        # Fallback lấy đoạn tiếng Việt từ raw_text
        clean_fallback = re.sub(r'[A-Za-z0-9_\-\.]{15,}|\b(ISBN|Barcode)\b.*', '', raw_text)
        text = re.sub(r'\s+', ' ', clean_fallback).strip()
        
    return text

# -----------------------------------------------------------------------------
# 2. LEXICONS FOR MOOD, EFFORT, AUDIENCE, INTENT
# -----------------------------------------------------------------------------
ALLOWED_MOODS = [
    "thư giãn", "nhẹ nhàng", "chữa lành", "vui vẻ", "hài hước",
    "cảm động", "hồi hộp", "suy ngẫm", "truyền cảm hứng", "nghiêm túc", "nặng đầu"
]

# Từ khóa đặc trưng theo nội dung
LEXICON_MOODS = {
    "thư giãn": ["thư giãn", "thảnh thơi", "nghỉ ngơi", "nhâm nhi", "cuối tuần", "thư thái", "an yên", "bình dị", "thanh thản", "trà chiều"],
    "nhẹ nhàng": ["nhẹ nhàng", "êm đềm", "ấm áp", "dịu dàng", "trong trẻo", "mộc mạc", "chậm rãi", "bình yên", "tuổi thơ", "hoài niệm"],
    "chữa lành": ["chữa lành", "tổn thương", "vết thương", "xoa dịu", "vỗ về", "trầm cảm", "nỗi đau", "an ủi", "vượt qua", "tự chữa", "tâm hồn"],
    "vui vẻ": ["vui vẻ", "vui tươi", "tiếng cười", "hứng khởi", "rộn ràng", "tươi sáng", "nghịch ngợm", "hồn nhiên", "phấn khởi"],
    "hài hước": ["hài hước", "dí dỏm", "hóm hỉnh", "tiếu lâm", "châm biếm", "buồn cười", "cười ra nước mắt", "tếu táo", "ngộ nghĩnh"],
    "cảm động": ["cảm động", "nước mắt", "rơi lệ", "xúc động", "nghẹn ngào", "tình mẹ", "tình cha", "hy sinh", "chia ly", "mồ côi", "tình thương", "trắc ẩn"],
    "hồi hộp": ["hồi hộp", "kỳ bí", "trinh thám", "án mạng", "hung thủ", "sát nhân", "nguy hiểm", "rượt đuổi", "bí ẩn", "ly kỳ", "gay cấn", "tội ác", "căng thẳng"],
    "suy ngẫm": ["suy ngẫm", "chiêm nghiệm", "triết lý", "nhân sinh", "ý nghĩa", "suy tư", "bản chất", "tự vấn", "thức tỉnh", "bài học", "cuộc đời"],
    "truyền cảm hứng": ["truyền cảm hứng", "động lực", "vươn lên", "ước mơ", "khát vọng", "nghị lực", "thành công", "vượt khó", "thắp sáng", "dấn thân", "bứt phá", "nỗ lực"],
    "nghiêm túc": ["nghiêm túc", "học thuật", "chính thống", "hệ thống", "lý thuyết", "phương pháp luận", "nghiên cứu", "nguyên lý", "tiêu chuẩn", "thực hành", "chuyên nghiệp"],
    "nặng đầu": ["nặng đầu", "phức tạp", "thuật toán", "cấu trúc dữ liệu", "học máy", "trí tuệ nhân tạo", "toán cao cấp", "kinh tế lượng", "lập trình nhúng", "mật mã", "vi tích phân", "hàn lâm"]
}

# Subcategory baseline prior (thiên hướng tự nhiên của 106 subcategories)
SUBCAT_PRIORS = {
    # Văn học
    "Truyện ngắn - Tản văn - Tạp Văn": {"moods": ["nhẹ nhàng", "suy ngẫm", "thư giãn"], "effort": "nhẹ", "intent": "giải trí"},
    "Truyện dài": {"moods": ["cảm động", "suy ngẫm"], "effort": "vừa", "intent": "giải trí"},
    "Truyện đam mỹ": {"moods": ["nhẹ nhàng", "cảm động"], "effort": "nhẹ", "intent": "giải trí"},
    "Truyện ngôn tình": {"moods": ["nhẹ nhàng", "cảm động", "thư giãn"], "effort": "nhẹ", "intent": "giải trí"},
    "Tiểu Thuyết": {"moods": ["suy ngẫm", "cảm động"], "effort": "vừa", "intent": "giải trí"},
    "Truyện trinh thám": {"moods": ["hồi hộp", "suy ngẫm"], "effort": "vừa", "intent": "giải trí"},
    "Truyện kiếm hiệp": {"moods": ["hồi hộp", "truyền cảm hứng"], "effort": "vừa", "intent": "giải trí"},
    "Thơ": {"moods": ["nhẹ nhàng", "suy ngẫm"], "effort": "nhẹ", "intent": "giải trí"},
    
    # CNTT
    "Lập Trình Web": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "nâng cao kỹ năng"},
    "Khoa Học Máy Tính": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "học tập"},
    "Trí Tuệ Nhân Tạo": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "học tập"},
    "Học Máy": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "học tập"},
    "An Toàn Thông Tin": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "nâng cao kỹ năng"},
    "Cơ Sở Dữ Liệu": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "vừa", "intent": "nâng cao kỹ năng"},
    "Mạng Máy Tính": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "vừa", "intent": "học tập"},
    "Tin Học Văn Phòng": {"moods": ["nghiêm túc"], "effort": "nhẹ", "intent": "nâng cao kỹ năng"},
    "Đồ Họa - Đa Phương Tiện": {"moods": ["truyền cảm hứng", "nghiêm túc"], "effort": "vừa", "intent": "nâng cao kỹ năng"},
    
    # Kinh tế
    "Quản Trị Kinh Doanh": {"moods": ["nghiêm túc", "truyền cảm hứng"], "effort": "vừa", "intent": "nâng cao kỹ năng"},
    "Tài Chính - Ngân Hàng": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "tra cứu"},
    "Marketing": {"moods": ["truyền cảm hứng", "nghiêm túc"], "effort": "vừa", "intent": "nâng cao kỹ năng"},
    "Khởi Nghiệp": {"moods": ["truyền cảm hứng", "nghiêm túc"], "effort": "vừa", "intent": "tìm cảm hứng"},
    "Kinh Tế Học": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "học tập"},
    
    # Kỹ năng sống
    "Tư duy tích cực": {"moods": ["truyền cảm hứng", "chữa lành"], "effort": "nhẹ", "intent": "tìm cảm hứng"},
    "Động lực sống": {"moods": ["truyền cảm hứng", "vui vẻ"], "effort": "nhẹ", "intent": "tìm cảm hứng"},
    "Kỹ năng giao tiếp": {"moods": ["nghiêm túc", "truyền cảm hứng"], "effort": "vừa", "intent": "nâng cao kỹ năng"},
    "Nghệ thuật lãnh đạo": {"moods": ["nghiêm túc", "truyền cảm hứng"], "effort": "vừa", "intent": "nâng cao kỹ năng"},
    "Quản lý thời gian": {"moods": ["nghiêm túc", "thư giãn"], "effort": "nhẹ", "intent": "nâng cao kỹ năng"},
    
    # Khoa học – Công nghệ
    "Vật lý đại cương": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "học tập"},
    "Toán học": {"moods": ["nghiêm túc", "nặng đầu"], "effort": "nặng", "intent": "học tập"},
    "Khoa học thường thức": {"moods": ["nhẹ nhàng", "truyền cảm hứng"], "effort": "nhẹ", "intent": "học tập"},
    "Thiên văn học": {"moods": ["suy ngẫm", "truyền cảm hứng"], "effort": "vừa", "intent": "học tập"},
    "Sinh học môi trường": {"moods": ["nghiêm túc", "suy ngẫm"], "effort": "vừa", "intent": "học tập"},
    
    # Thiếu nhi
    "Truyện tranh": {"moods": ["vui vẻ", "hài hước", "nhẹ nhàng"], "effort": "nhẹ", "intent": "giải trí"},
    "Văn học thiếu nhi": {"moods": ["vui vẻ", "nhẹ nhàng", "cảm động"], "effort": "nhẹ", "intent": "giải trí"},
    "Kiến thức - khoa học": {"moods": ["vui vẻ", "nhẹ nhàng"], "effort": "nhẹ", "intent": "học tập"},
    "Văn học Việt Nam": {"moods": ["nhẹ nhàng", "cảm động"], "effort": "nhẹ", "intent": "giải trí"},
    
    # Tâm lý học
    "Tâm lý học hành vi": {"moods": ["suy ngẫm", "nghiêm túc"], "effort": "vừa", "intent": "học tập"},
    "Tâm lý học nhận thức": {"moods": ["suy ngẫm", "nghiêm túc"], "effort": "vừa", "intent": "học tập"},
    "Tâm lý trị liệu": {"moods": ["chữa lành", "suy ngẫm"], "effort": "vừa", "intent": "học tập"},
    
    # Lịch sử – Văn hóa
    "Lịch sử Việt Nam": {"moods": ["suy ngẫm", "nghiêm túc"], "effort": "vừa", "intent": "học tập"},
    "Lịch sử thế giới": {"moods": ["suy ngẫm", "nghiêm túc"], "effort": "vừa", "intent": "học tập"},
    "Triết học văn hóa": {"moods": ["suy ngẫm", "nặng đầu"], "effort": "nặng", "intent": "học tập"},
    "Văn hóa phương Đông": {"moods": ["suy ngẫm", "nhẹ nhàng"], "effort": "vừa", "intent": "học tập"},
    
    # Giáo dục – Ngoại ngữ
    "Tiếng Anh": {"moods": ["nghiêm túc"], "effort": "vừa", "intent": "ôn thi"},
    "Tiếng Trung": {"moods": ["nghiêm túc"], "effort": "vừa", "intent": "ôn thi"},
    "Tiếng Nhật": {"moods": ["nghiêm túc"], "effort": "vừa", "intent": "ôn thi"},
    "Phương pháp giảng dạy": {"moods": ["nghiêm túc"], "effort": "vừa", "intent": "nâng cao kỹ năng"}
}

# -----------------------------------------------------------------------------
# 3. LABELING ENGINE PER BOOK (CONTENT-GROUNDED)
# -----------------------------------------------------------------------------
def analyze_book(row, clean_desc):
    title = str(row.get('Title', '')).strip()
    author = str(row.get('Author', '')).strip()
    cat = str(row.get('Category', '')).strip()
    subcat = str(row.get('Subcategory', '')).strip()
    kw = str(row.get('Keywords', '')).strip()
    
    full_text_lower = f"{title} {subcat} {clean_desc} {kw}".lower()
    
    # --- A. MOOD TAGS (Content-specific scoring) ---
    mood_scores = {m: 0.0 for m in ALLOWED_MOODS}
    
    # 1. Trọng số từ vựng xuất hiện trong Description & Title của chính cuốn sách
    for m, words in LEXICON_MOODS.items():
        for w in words:
            if w in title.lower():
                mood_scores[m] += 3.0  # Từ khóa trong Title có trọng số rất cao
            if w in clean_desc.lower():
                mood_scores[m] += 1.5  # Từ khóa trong Description
            if w in kw.lower():
                mood_scores[m] += 1.0
                
    # 2. Bổ sung thiên hướng Subcategory (prior nhẹ 0.8 để tránh đồng nhất hóa)
    if subcat in SUBCAT_PRIORS:
        for m in SUBCAT_PRIORS[subcat].get("moods", []):
            mood_scores[m] += 0.8
    else:
        # Fallback category-level prior nhẹ
        if cat == "Văn học – Tiểu thuyết":
            mood_scores["suy ngẫm"] += 0.5
        elif cat == "Thiếu nhi":
            mood_scores["vui vẻ"] += 0.5
            mood_scores["nhẹ nhàng"] += 0.5
        elif cat == "Kỹ năng sống – Phát triển bản thân":
            mood_scores["truyền cảm hứng"] += 0.5
        elif cat in ("Công nghệ thông tin", "Giáo dục – Ngoại ngữ", "Kinh tế – Kinh doanh"):
            mood_scores["nghiêm túc"] += 0.5
            
    # Lấy top 1 đến 3 mood có điểm cao nhất > 0.5
    sorted_moods = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
    selected_moods = [m for m, score in sorted_moods if score > 0.6][:3]
    if not selected_moods:
        # Nếu điểm thấp, chọn mood top 1
        selected_moods = [sorted_moods[0][0]]
        
    mood_tags = ", ".join(selected_moods)
    
    # --- B. READING EFFORT ---
    # Phân loại theo độ phức tạp kỹ thuật và tính chất nội dung
    effort = "vừa"
    if cat == "Thiếu nhi" or any(w in full_text_lower for w in ["cho bé", "trẻ em", "mầm non", "tô màu", "truyện tranh", "học sinh tiểu học"]):
        effort = "nhẹ"
    elif "Truyện ngắn" in subcat or "Tản văn" in subcat or "Thơ" in subcat:
        effort = "nhẹ"
    elif cat in ("Công nghệ thông tin", "Khoa học – Công nghệ") and any(w in full_text_lower for w in ["thuật toán", "cấu trúc dữ liệu", "học máy", "trí tuệ nhân tạo", "lập trình c", "vi tích phân", "kinh tế lượng", "chuyên sâu"]):
        effort = "nặng"
    elif subcat in SUBCAT_PRIORS and "effort" in SUBCAT_PRIORS[subcat]:
        effort = SUBCAT_PRIORS[subcat]["effort"]
    elif any(w in full_text_lower for w in ["giáo trình", "chuyên sâu", "nghiên cứu", "học thuật", "luận án"]):
        effort = "nặng"
    elif any(w in full_text_lower for w in ["nhẹ nhàng", "dễ đọc", "dành cho bé", "thư giãn", "tranh màu"]):
        effort = "nhẹ"
        
    # --- C. AUDIENCE ---
    audience = "mọi người"
    if cat == "Thiếu nhi" or any(w in full_text_lower for w in ["cho bé", "trẻ em", "mầm non", "học sinh tiểu học"]):
        audience = "trẻ em"
    elif any(w in full_text_lower for w in ["học sinh", "lớp 10", "lớp 11", "lớp 12", "thi thpt", "tuổi teen", "thanh thiếu niên"]):
        audience = "học sinh"
    elif cat == "Công nghệ thông tin" or "giáo trình" in full_text_lower or "ielts" in full_text_lower or "hsk" in full_text_lower or "đại học" in full_text_lower or "khoa học máy tính" in full_text_lower:
        audience = "sinh viên"
    elif cat == "Kinh tế – Kinh doanh" or any(w in full_text_lower for w in ["lãnh đạo", "quản lý", "doanh nghiệp", "thăng tiến", "người đi làm", "công sở", "nhân sự", "đầu tư"]):
        audience = "người đi làm"
    else:
        audience = "mọi người"
        
    # --- D. READER INTENT ---
    intent = "giải trí"
    if subcat in SUBCAT_PRIORS and "intent" in SUBCAT_PRIORS[subcat]:
        intent = SUBCAT_PRIORS[subcat]["intent"]
    elif any(w in full_text_lower for w in ["ôn thi", "luyện thi", "ielts", "toeic", "hsk", "topik", "đề thi"]):
        intent = "ôn thi"
    elif any(w in full_text_lower for w in ["tra cứu", "sổ tay", "từ điển", "bách khoa", "cẩm nang"]):
        intent = "tra cứu"
    elif any(w in full_text_lower for w in ["học tập", "giáo trình", "kiến thức", "lý thuyết", "nguyên lý"]):
        intent = "học tập"
    elif any(w in full_text_lower for w in ["kỹ năng", "thực hành", "phương pháp", "bí quyết", "rèn luyện"]):
        intent = "nâng cao kỹ năng"
    elif any(w in full_text_lower for w in ["cảm hứng", "động lực", "thức tỉnh", "vươn lên", "ý nghĩa"]):
        intent = "tìm cảm hứng"
    elif cat == "Thiếu nhi" or any(w in full_text_lower for w in ["đọc cho bé", "cùng con"]):
        intent = "đọc cùng con"
    elif cat in ("Văn học – Tiểu thuyết"):
        intent = "giải trí"
        
    # --- E. SUMMARY_VI (1-2 sentences purely grounded in data) ---
    first_sentence = ""
    if clean_desc:
        # Lấy câu có nghĩa đầu tiên từ clean_desc
        sentences = [s.strip() for s in re.split(r'[\.\?!]\s+', clean_desc) if len(s.strip()) > 15]
        for s in sentences:
            s_clean = re.sub(r'^\s*(\d+[\.\:\-]\s*)+', '', s).strip()
            if len(s_clean) > 20:
                first_sentence = s_clean
                if not first_sentence.endswith('.'):
                    first_sentence += '.'
                break
    
    if first_sentence and len(first_sentence) < 150:
        summary_vi = f"Sách nói về {first_sentence[0].lower() + first_sentence[1:]} Tác phẩm mang phong cách {mood_tags}, phù hợp với đối tượng {audience} có mục đích {intent}."
    else:
        summary_vi = f"Tác phẩm thuộc thể loại {cat} ({subcat}) của tác giả {author if author else 'nhiều tác giả'}, mang sắc thái {mood_tags}, rất phù hợp cho đối tượng {audience} muốn {intent}."
        
    # --- F. SEARCH_TEXT ---
    search_text = f"{title} {author}. Thể loại: {cat} - {subcat}. {summary_vi} Tâm trạng: {mood_tags}. Nỗ lực đọc: {effort}. Đối tượng: {audience}."
    
    return {
        "clean_description": clean_desc,
        "summary_vi": summary_vi,
        "mood_tags": mood_tags,
        "reader_intent": intent,
        "reading_effort": effort,
        "audience": audience,
        "search_text": search_text
    }

# -----------------------------------------------------------------------------
# 4. EXECUTE ENRICHMENT ON 3,000 BOOKS
# -----------------------------------------------------------------------------
enriched_rows = []
for idx, row in df.iterrows():
    raw_desc = row.get('Description', '')
    title = row.get('Title', '')
    c_desc = clean_description_text(raw_desc, title)
    enrichment = analyze_book(row, c_desc)
    
    # Merge existing columns + enriched columns
    merged = row.to_dict()
    merged.update(enrichment)
    enriched_rows.append(merged)

df_enriched = pd.DataFrame(enriched_rows)
df_enriched.to_csv(DATASET_OUT, index=False, encoding='utf-8')
print(f"[+] Đã lưu file enriched dataset: {DATASET_OUT} với {len(df_enriched)} cuốn sách.")

# -----------------------------------------------------------------------------
# 5. COMPUTE COMPREHENSIVE STATISTICS
# -----------------------------------------------------------------------------
# Đếm phân bố từng nhãn đơn lẻ trong mood_tags (mỗi cuốn có thể có 1-3 tags)
all_mood_tokens = []
for m_str in df_enriched['mood_tags']:
    tokens = [t.strip() for t in m_str.split(',') if t.strip()]
    all_mood_tokens.extend(tokens)
mood_counts = {k: int(v) for k, v in Counter(all_mood_tokens).items()}

effort_counts = {k: int(v) for k, v in df_enriched['reading_effort'].value_counts().items()}
audience_counts = {k: int(v) for k, v in df_enriched['audience'].value_counts().items()}
intent_counts = {k: int(v) for k, v in df_enriched['reader_intent'].value_counts().items()}

empty_clean_desc = int((df_enriched['clean_description'] == '').sum())
empty_moods = int((df_enriched['mood_tags'] == '').sum())
empty_effort = int((df_enriched['reading_effort'] == '').sum())
empty_audience = int((df_enriched['audience'] == '').sum())

stats = {
    "total_books": len(df_enriched),
    "mood_counts": mood_counts,
    "reading_effort_counts": effort_counts,
    "audience_counts": audience_counts,
    "reader_intent_counts": intent_counts,
    "quality_checks": {
        "empty_clean_description": empty_clean_desc,
        "empty_mood_tags": empty_moods,
        "empty_reading_effort": empty_effort,
        "empty_audience": empty_audience,
        "unique_mood_combinations": int(df_enriched['mood_tags'].nunique()),
        "distinct_search_texts": int(df_enriched['search_text'].nunique())
    }
}

with open(STATS_OUT, 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("THỐNG KÊ CHI TIẾT BƯỚC 1:")
print("=" * 80)
print(f"Tổng số sách: {stats['total_books']}")
print("\n1. Phân bố MOOD TAGS:")
for m, c in sorted(mood_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   - {m:<18}: {c:>4} sách ({round(c/len(df_enriched)*100, 1)}%)")

print("\n2. Phân bố READING EFFORT:")
for e, c in effort_counts.items():
    print(f"   - {e:<10}: {c:>4} sách ({round(c/len(df_enriched)*100, 1)}%)")

print("\n3. Phân bố AUDIENCE:")
for a, c in audience_counts.items():
    print(f"   - {a:<15}: {c:>4} sách ({round(c/len(df_enriched)*100, 1)}%)")

print("\n4. Phân bố INTENT:")
for i, c in intent_counts.items():
    print(f"   - {i:<20}: {c:>4} sách ({round(c/len(df_enriched)*100, 1)}%)")

print("\n5. Kiểm tra chất lượng (Quality Check):")
print(f"   - Số sách bị mood_tags rỗng        : {empty_moods}")
print(f"   - Số sách bị reading_effort rỗng    : {empty_effort}")
print(f"   - Số sách bị audience rỗng          : {empty_audience}")
print(f"   - Số tổ hợp mood khác nhau          : {stats['quality_checks']['unique_mood_combinations']}")
print(f"   - Số search_text độc nhất           : {stats['quality_checks']['distinct_search_texts']} / {len(df_enriched)}")

# -----------------------------------------------------------------------------
# 6. EXTRACT 30 RANDOM BOOKS COVERING ALL 9 CATEGORIES
# -----------------------------------------------------------------------------
random.seed(42)  # Cố định seed để có thể tái lập kết quả
categories = list(df_enriched['Category'].unique())
samples_30 = []

# Đảm bảo phủ đủ 9 Categories: lấy 3-4 cuốn cho mỗi category để đủ 30 cuốn
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

for cat, count in target_per_cat.items():
    cat_df = df_enriched[df_enriched['Category'] == cat]
    sampled = cat_df.sample(n=min(count, len(cat_df)), random_state=42)
    for _, row in sampled.iterrows():
        raw_d = str(row['Description'])
        short_desc = raw_d[:120] + "..." if len(raw_d) > 120 else raw_d
        samples_30.append({
            "book_id": row['Book_ID'],
            "title": row['Title'],
            "author": row['Author'],
            "category": row['Category'],
            "subcategory": row['Subcategory'],
            "raw_desc_short": short_desc,
            "summary_vi": row['summary_vi'],
            "mood_tags": row['mood_tags'],
            "reading_effort": row['reading_effort'],
            "audience": row['audience'],
            "reader_intent": row['reader_intent']
        })

with open(SAMPLES_OUT, 'w', encoding='utf-8') as f:
    json.dump(samples_30, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print(f"[+] Đã trích xuất 30 cuốn mẫu phủ đủ 9 Category vào {SAMPLES_OUT}")
print("=" * 80)
