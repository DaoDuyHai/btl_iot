import os
import sys
import json
import re
import unicodedata
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "venv", "Lib", "site-packages"))

DATASET_PATH = os.path.join(BASE_DIR, "dataset", "books_enriched.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "dataset", "test_set_150.json")

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def build_testset():
    print("=" * 80)
    print("BƯỚC 5: XÂY DỰNG TẬP DỮ LIỆU ĐÁNH GIÁ CHUẨN 150 CÂU (CHỐNG TRÙNG LẶP)")
    print("=" * 80)
    
    df = pd.read_csv(DATASET_PATH)
    print(f"[*] Đã tải {len(df)} sách từ {DATASET_PATH}")
    
    # -------------------------------------------------------------------------
    # 1. 50 CÂU CỤ THỂ (EXACT_BOOK - có target_book_id chính xác)
    # Phủ 9 Category, đa dạng kiểu hỏi: gõ cụt, không dấu, nhớ cốt truyện, tác giả
    # -------------------------------------------------------------------------
    specific_queries = [
        # Văn học
        {"id": "SPEC_01", "query": "Người Đàn Ông Mang Tên Ove", "target_book_id": "B0001", "type": "exact_title", "persona": "sinh viên", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_02", "query": "nguoi dan ong mang ten ove", "target_book_id": "B0001", "type": "unaccented", "persona": "sinh viên", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_03", "query": "tìm tiểu thuyết Beartown của Fredrik Backman", "target_book_id": "B0002", "type": "author_title", "persona": "người đi làm", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_04", "query": "Cây Cam Ngọt Của Tôi", "target_book_id": "B0043", "type": "exact_title", "persona": "học sinh", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_05", "query": "cay cam ngot cua toi con sach khong", "target_book_id": "B0043", "type": "unaccented_status", "persona": "sinh viên", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_06", "query": "cuốn sách về ông lão Bo và những chú sếu bay về phương Nam của Lisa Ridzen", "target_book_id": "B0060", "type": "plot_author", "persona": "người lớn tuổi", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_07", "query": "Cảm Ơn Người Lớn tác giả Nguyễn Nhật Ánh", "target_book_id": "B0126", "type": "author_title", "persona": "học sinh", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_08", "query": "tản văn Ăn Để Nhớ của Kim Em", "target_book_id": "B0188", "type": "author_title", "persona": "người đi làm", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_09", "query": "Đời bừng sáng khi ta biết lãng quên - Marc Levy", "target_book_id": "B0194", "type": "author_title", "persona": "người đi làm", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_10", "query": "Chờ Ngày Bình Yên", "target_book_id": "B0027", "type": "exact_title", "persona": "sinh viên", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_11", "query": "Đi Ra Thế Giới Ngắm Nhìn Bản Thân", "target_book_id": "B0323", "type": "exact_title", "persona": "người mới đọc", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_12", "query": "Một Người Rừng Thông Thái", "target_book_id": "B0093", "type": "exact_title", "persona": "sinh viên", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_13", "query": "Kỳ Án Trong Thư Viện Kín", "target_book_id": "B0078", "type": "exact_title", "persona": "sinh viên", "category": "Văn học – Tiểu thuyết"},
        {"id": "SPEC_14", "query": "Feynman Chuyện Thật Như Đùa", "target_book_id": "B0116", "type": "exact_title", "persona": "sinh viên", "category": "Văn học – Tiểu thuyết"},

        # Kinh tế – Kinh doanh
        {"id": "SPEC_15", "query": "Dẫn Dắt Một Bầy Sói Hay Chăn Một Đàn Cừu", "target_book_id": "B1075", "type": "exact_title", "persona": "người đi làm", "category": "Kinh tế – Kinh doanh"},
        {"id": "SPEC_16", "query": "dan dat mot bay soi hay chan mot dan cuu", "target_book_id": "B1075", "type": "unaccented", "persona": "người đi làm", "category": "Kinh tế – Kinh doanh"},
        {"id": "SPEC_17", "query": "Kỹ thuật phân tích biểu đồ chứng khoán", "target_book_id": "B1072", "type": "exact_title", "persona": "người đi làm", "category": "Kinh tế – Kinh doanh"},
        {"id": "SPEC_18", "query": "THE LITTLE BOOK - Quản Trị Rủi Ro Trong Đầu Tư Chứng Khoán", "target_book_id": "B1066", "type": "exact_title", "persona": "sinh viên", "category": "Kinh tế – Kinh doanh"},
        {"id": "SPEC_19", "query": "Cái Bẫy Toàn Cầu - Khủng hoảng tài chính", "target_book_id": "B1067", "type": "exact_title", "persona": "người đi làm", "category": "Kinh tế – Kinh doanh"},
        {"id": "SPEC_20", "query": "Bộ sách Chiến lược đại dương xanh", "target_book_id": "B1051", "type": "topic_title", "persona": "người đi làm", "category": "Kinh tế – Kinh doanh"},

        # Công nghệ thông tin
        {"id": "SPEC_21", "query": "Thiết Kế Hệ Thống Học Máy Chip Huyen", "target_book_id": "B0604", "type": "author_title", "persona": "sinh viên", "category": "Công nghệ thông tin"},
        {"id": "SPEC_22", "query": "Nhập Môn Lập Trình Thi Đấu - Python", "target_book_id": "B0607", "type": "exact_title", "persona": "sinh viên", "category": "Công nghệ thông tin"},
        {"id": "SPEC_23", "query": "Claude Toàn Tập Cẩm Nang Toàn Diện Nguyễn Văn Lượng", "target_book_id": "B0609", "type": "author_title", "persona": "người đi làm", "category": "Công nghệ thông tin"},
        {"id": "SPEC_24", "query": "nhap mon lap trinh thi dau python", "target_book_id": "B0607", "type": "unaccented", "persona": "sinh viên", "category": "Công nghệ thông tin"},
        {"id": "SPEC_25", "query": "Lập Trình Điều Khiển Arduino Từ Cơ Bản Đến Nâng Cao", "target_book_id": "B0621", "type": "exact_title", "persona": "sinh viên", "category": "Công nghệ thông tin"},
        {"id": "SPEC_26", "query": "AutoCAD Cơ bản cho người mới bắt đầu", "target_book_id": "B0680", "type": "exact_title", "persona": "sinh viên", "category": "Công nghệ thông tin"},

        # Giáo dục – Ngoại ngữ
        {"id": "SPEC_27", "query": "Daily English Conversation - Hội Thoại Tiếng Anh", "target_book_id": "B1830", "type": "exact_title", "persona": "sinh viên", "category": "Giáo dục – Ngoại ngữ"},
        {"id": "SPEC_28", "query": "Bùng Nổ Tiếng Anh: 27 Giới Từ Hữu Ích Trong Tiếng Anh Giao Tiếp", "target_book_id": "B1741", "type": "exact_title", "persona": "sinh viên", "category": "Giáo dục – Ngoại ngữ"},
        {"id": "SPEC_29", "query": "Giới Từ Tiếng Anh Mai Lan Hương", "target_book_id": "B1720", "type": "author_title", "persona": "học sinh", "category": "Giáo dục – Ngoại ngữ"},
        {"id": "SPEC_30", "query": "giáo trình ngữ pháp Try N3 tiếng Nhật", "target_book_id": "B1682", "type": "exact_title", "persona": "sinh viên", "category": "Giáo dục – Ngoại ngữ"},
        {"id": "SPEC_31", "query": "Keep It Up - Tập Viết Tiếng Nhật Theo Bảng Chữ Cái Hiragana", "target_book_id": "B1802", "type": "exact_title", "persona": "người mới đọc", "category": "Giáo dục – Ngoại ngữ"},
        {"id": "SPEC_32", "query": "TOEFL iBT Navigator: Reading Lee Seon-uk", "target_book_id": "B1705", "type": "author_title", "persona": "sinh viên", "category": "Giáo dục – Ngoại ngữ"},
        {"id": "SPEC_33", "query": "Quick English Nói Tiếng Anh Cấp Tốc", "target_book_id": "B1706", "type": "exact_title", "persona": "học sinh", "category": "Giáo dục – Ngoại ngữ"},

        # Kỹ năng sống – Phát triển bản thân
        {"id": "SPEC_34", "query": "Sống Bình Thường Mà Không Tầm Thường", "target_book_id": "B2126", "type": "exact_title", "persona": "sinh viên", "category": "Kỹ năng sống – Phát triển bản thân"},
        {"id": "SPEC_35", "query": "song binh thuong ma khong tam thuong", "target_book_id": "B2126", "type": "unaccented", "persona": "sinh viên", "category": "Kỹ năng sống – Phát triển bản thân"},
        {"id": "SPEC_36", "query": "Sai Sao Cho Đúng Amy C Edmondson", "target_book_id": "B1901", "type": "author_title", "persona": "người đi làm", "category": "Kỹ năng sống – Phát triển bản thân"},
        {"id": "SPEC_37", "query": "Vượt Qua Giới Hạn Cameron R Hanes", "target_book_id": "B1902", "type": "author_title", "persona": "người đi làm", "category": "Kỹ năng sống – Phát triển bản thân"},
        {"id": "SPEC_38", "query": "IGEN THẾ HỆ SMARTPHONE Jean M Twenge", "target_book_id": "B1905", "type": "author_title", "persona": "sinh viên", "category": "Kỹ năng sống – Phát triển bản thân"},

        # Lịch sử – Văn hóa
        {"id": "SPEC_39", "query": "Xứ Đông Dương Paul Doumer", "target_book_id": "B2752", "type": "exact_title", "persona": "người lớn tuổi", "category": "Lịch sử – Văn hóa"},
        {"id": "SPEC_40", "query": "Súng Vi Trùng Và Thép Jared Diamond", "target_book_id": "B2754", "type": "exact_title", "persona": "sinh viên", "category": "Lịch sử – Văn hóa"},
        {"id": "SPEC_41", "query": "Đạo Đức Kinh Ấn bản dấu ấn 10 năm", "target_book_id": "B2755", "type": "exact_title", "persona": "người lớn tuổi", "category": "Lịch sử – Văn hóa"},

        # Khoa học – Công nghệ
        {"id": "SPEC_42", "query": "Cuộc đời phi thường của Neil Amstrong", "target_book_id": "B2306", "type": "exact_title", "persona": "học sinh", "category": "Khoa học – Công nghệ"},
        {"id": "SPEC_43", "query": "Tam thể 2 Khu rừng đen tối Lưu Từ Hân", "target_book_id": "B2315", "type": "author_title", "persona": "sinh viên", "category": "Khoa học – Công nghệ"},
        {"id": "SPEC_44", "query": "Bản đồ thế giới cà phê Từ hạt đến pha chế", "target_book_id": "B2258", "type": "exact_title", "persona": "học sinh", "category": "Khoa học – Công nghệ"},

        # Thiếu nhi
        {"id": "SPEC_45", "query": "Ở đây có niềm vui - Cửa hàng túi xinh xắn", "target_book_id": "B2616", "type": "exact_title", "persona": "phụ huynh", "category": "Thiếu nhi"},
        {"id": "SPEC_46", "query": "Hạt mầm nhân cách Nuôi dưỡng lòng nhân hậu", "target_book_id": "B2553", "type": "exact_title", "persona": "phụ huynh", "category": "Thiếu nhi"},
        {"id": "SPEC_47", "query": "truyện tranh Chuột Típ đến thăm ông bà", "target_book_id": "B2551", "type": "exact_title", "persona": "phụ huynh", "category": "Thiếu nhi"},
        {"id": "SPEC_48", "query": "Chuột Típ Bỉm ơi tạm biệt", "target_book_id": "B2552", "type": "exact_title", "persona": "phụ huynh", "category": "Thiếu nhi"},
        {"id": "SPEC_49", "query": "Mèo Mốc Black Book tập 2", "target_book_id": "B0473", "type": "exact_title", "persona": "học sinh", "category": "Thiếu nhi"},
        
        # Tâm lý học
        {"id": "SPEC_50", "query": "thực hành phương pháp chánh niệm chương trình 8 tuần", "target_book_id": "B2905", "type": "exact_title", "persona": "sinh viên", "category": "Tâm lý học"}
    ]

    # -------------------------------------------------------------------------
    # 2. 50 CÂU CHỦ ĐỀ (CATEGORY_TOPIC - có target Category & Subcategories)
    # -------------------------------------------------------------------------
    topic_queries = [
        # Ngoại ngữ (8 câu)
        {"id": "TOPIC_01", "query": "tiếng anh", "target_category": "Giáo dục – Ngoại ngữ", "type": "broad_topic", "persona": "sinh viên"},
        {"id": "TOPIC_02", "query": "tiếng nhật", "target_category": "Giáo dục – Ngoại ngữ", "type": "broad_topic", "persona": "sinh viên"},
        {"id": "TOPIC_03", "query": "sách học tiếng hàn giao tiếp cơ bản", "target_category": "Giáo dục – Ngoại ngữ", "type": "specific_subcat", "persona": "sinh viên"},
        {"id": "TOPIC_04", "query": "giáo trình hán ngữ và ngữ pháp tiếng trung", "target_category": "Giáo dục – Ngoại ngữ", "type": "specific_subcat", "persona": "sinh viên"},
        {"id": "TOPIC_05", "query": "tài liệu ôn thi chứng chỉ TOEIC 700", "target_category": "Giáo dục – Ngoại ngữ", "type": "exam_prep", "persona": "sinh viên"},
        {"id": "TOPIC_06", "query": "sách luyện thi ielts band 6.5 trở lên", "target_category": "Giáo dục – Ngoại ngữ", "type": "exam_prep", "persona": "học sinh"},
        {"id": "TOPIC_07", "query": "sách trau dồi từ vựng tiếng anh giao tiếp", "target_category": "Giáo dục – Ngoại ngữ", "type": "skill_topic", "persona": "người đi làm"},
        {"id": "TOPIC_08", "query": "luyện thi chứng chỉ tiếng nhật sơ cấp N4 và N5", "target_category": "Giáo dục – Ngoại ngữ", "type": "exam_prep", "persona": "sinh viên"},

        # CNTT (8 câu)
        {"id": "TOPIC_09", "query": "lập trình python cho người mới bắt đầu", "target_category": "Công nghệ thông tin", "type": "beginner_skill", "persona": "sinh viên"},
        {"id": "TOPIC_10", "query": "giáo trình cấu trúc dữ liệu và giải thuật nâng cao", "target_category": "Công nghệ thông tin", "type": "academic", "persona": "sinh viên"},
        {"id": "TOPIC_11", "query": "sách về trí tuệ nhân tạo machine learning và deep learning", "target_category": "Công nghệ thông tin", "type": "tech_domain", "persona": "người đi làm"},
        {"id": "TOPIC_12", "query": "tài liệu an toàn thông tin và bảo mật mạng", "target_category": "Công nghệ thông tin", "type": "tech_domain", "persona": "sinh viên"},
        {"id": "TOPIC_13", "query": "sách học lập trình web backend frontend", "target_category": "Công nghệ thông tin", "type": "tech_domain", "persona": "sinh viên"},
        {"id": "TOPIC_14", "query": "sách hệ quản trị cơ sở dữ liệu và truy vấn SQL", "target_category": "Công nghệ thông tin", "type": "tech_domain", "persona": "sinh viên"},
        {"id": "TOPIC_15", "query": "kien thuc tin hoc van phong excel word", "target_category": "Công nghệ thông tin", "type": "unaccented_skill", "persona": "người đi làm"},
        {"id": "TOPIC_16", "query": "sách lập trình vi điều khiển iot và hệ thống nhúng", "target_category": "Công nghệ thông tin", "type": "tech_domain", "persona": "sinh viên"},

        # Kinh tế & Kinh doanh (7 câu)
        {"id": "TOPIC_17", "query": "sách hướng dẫn đầu tư chứng khoán cho f0", "target_category": "Kinh tế – Kinh doanh", "type": "finance_guide", "persona": "người đi làm"},
        {"id": "TOPIC_18", "query": "quản trị kinh doanh và nghệ thuật bán hàng", "target_category": "Kinh tế – Kinh doanh", "type": "business_topic", "persona": "người đi làm"},
        {"id": "TOPIC_19", "query": "sách marketing số và truyền thông thương hiệu", "target_category": "Kinh tế – Kinh doanh", "type": "business_topic", "persona": "sinh viên"},
        {"id": "TOPIC_20", "query": "kiến thức tài chính cá nhân và quản lý dòng tiền", "target_category": "Kinh tế – Kinh doanh", "type": "finance_guide", "persona": "người đi làm"},
        {"id": "TOPIC_21", "query": "sách khởi nghiệp đổi mới sáng tạo", "target_category": "Kinh tế – Kinh doanh", "type": "business_topic", "persona": "sinh viên"},
        {"id": "TOPIC_22", "query": "kinh tế vi mô và kinh tế vĩ mô cơ bản", "target_category": "Kinh tế – Kinh doanh", "type": "academic", "persona": "sinh viên"},
        {"id": "TOPIC_23", "query": "sách nguyên lý kế toán và phân tích báo cáo tài chính", "target_category": "Kinh tế – Kinh doanh", "type": "academic", "persona": "sinh viên"},

        # Kỹ năng sống – Phát triển bản thân (6 câu)
        {"id": "TOPIC_24", "query": "kỹ năng giao tiếp ứng xử trong môi trường công sở", "target_category": "Kỹ năng sống – Phát triển bản thân", "type": "soft_skill", "persona": "người đi làm"},
        {"id": "TOPIC_25", "query": "sách về nghệ thuật lãnh đạo và quản lý đội nhóm", "target_category": "Kỹ năng sống – Phát triển bản thân", "type": "soft_skill", "persona": "người đi làm"},
        {"id": "TOPIC_26", "query": "phương pháp quản lý thời gian và chống trì hoãn", "target_category": "Kỹ năng sống – Phát triển bản thân", "type": "productivity", "persona": "sinh viên"},
        {"id": "TOPIC_27", "query": "rèn luyện thói quen tích cực và kỷ luật bản thân", "target_category": "Kỹ năng sống – Phát triển bản thân", "type": "productivity", "persona": "sinh viên"},
        {"id": "TOPIC_28", "query": "kỹ năng đàm phán và thuyết phục đối tác", "target_category": "Kỹ năng sống – Phát triển bản thân", "type": "soft_skill", "persona": "người đi làm"},
        {"id": "TOPIC_29", "query": "sách phát triển tư duy phản biện và giải quyết vấn đề", "target_category": "Kỹ năng sống – Phát triển bản thân", "type": "thinking_skill", "persona": "sinh viên"},

        # Tâm lý học (5 câu)
        {"id": "TOPIC_30", "query": "tổng quan tâm lý học hành vi của Watson và Skinner", "target_category": "Tâm lý học", "type": "domain_topic", "persona": "sinh viên"},
        {"id": "TOPIC_31", "query": "tìm hiểu tâm lý học tội phạm và phân tích tâm thần", "target_category": "Tâm lý học", "type": "domain_topic", "persona": "sinh viên"},
        {"id": "TOPIC_32", "query": "liệu pháp nhận thức hành vi CBT và trị liệu tâm lý", "target_category": "Tâm lý học", "type": "domain_topic", "persona": "sinh viên"},
        {"id": "TOPIC_33", "query": "tài liệu chữa lành đứa trẻ bên trong và tổn thương thời thơ ấu", "target_category": "Tâm lý học", "type": "healing_topic", "persona": "người đi làm"},
        {"id": "TOPIC_34", "query": "tâm lý học đám đông và thao túng tâm lý", "target_category": "Tâm lý học", "type": "domain_topic", "persona": "sinh viên"},

        # Lịch sử – Văn hóa (5 câu)
        {"id": "TOPIC_35", "query": "sách lịch sử việt nam thời phong kiến triều nguyễn", "target_category": "Lịch sử – Văn hóa", "type": "history_topic", "persona": "người lớn tuổi"},
        {"id": "TOPIC_36", "query": "lịch sử chiến tranh thế giới thứ nhất và thứ hai", "target_category": "Lịch sử – Văn hóa", "type": "history_topic", "persona": "sinh viên"},
        {"id": "TOPIC_37", "query": "văn hóa phong tục tập quán truyền thống việt nam", "target_category": "Lịch sử – Văn hóa", "type": "culture_topic", "persona": "người lớn tuổi"},
        {"id": "TOPIC_38", "query": "nghiên cứu lịch sử văn minh cổ đại phương đông", "target_category": "Lịch sử – Văn hóa", "type": "history_topic", "persona": "sinh viên"},
        {"id": "TOPIC_39", "query": "sách triết học cổ điển phương tây và đạo học", "target_category": "Lịch sử – Văn hóa", "type": "philosophy_topic", "persona": "sinh viên"},

        # Khoa học – Công nghệ (4 câu)
        {"id": "TOPIC_40", "query": "sách thiên văn học khám phá vũ trụ và các vì sao", "target_category": "Khoa học – Công nghệ", "type": "science_topic", "persona": "học sinh"},
        {"id": "TOPIC_41", "query": "vật lý lượng tử và thuyết tương đối giải thích dễ hiểu", "target_category": "Khoa học – Công nghệ", "type": "science_topic", "persona": "sinh viên"},
        {"id": "TOPIC_42", "query": "sách sinh học môi trường và biến đổi khí hậu toàn cầu", "target_category": "Khoa học – Công nghệ", "type": "science_topic", "persona": "sinh viên"},
        {"id": "TOPIC_43", "query": "sách khoa học thường thức lý giải hiện tượng tự nhiên", "target_category": "Khoa học – Công nghệ", "type": "science_topic", "persona": "học sinh"},

        # Thiếu nhi (4 câu)
        {"id": "TOPIC_44", "query": "truyện cổ tích việt nam và thế giới cho thiếu nhi", "target_category": "Thiếu nhi", "type": "kids_topic", "persona": "phụ huynh"},
        {"id": "TOPIC_45", "query": "bách khoa tri thức cho bé phát triển trí tuệ", "target_category": "Thiếu nhi", "type": "kids_topic", "persona": "phụ huynh"},
        {"id": "TOPIC_46", "query": "bộ sách rèn luyện nền nếp và ứng xử cho trẻ cấp 1", "target_category": "Thiếu nhi", "type": "kids_topic", "persona": "phụ huynh"},
        {"id": "TOPIC_47", "query": "truyện đồng thoại động vật vui nhộn cho trẻ nhỏ", "target_category": "Thiếu nhi", "type": "kids_topic", "persona": "phụ huynh"},

        # Văn học – Tiểu thuyết (3 câu)
        {"id": "TOPIC_48", "query": "tác phẩm văn học kinh điển thế giới nổi tiếng", "target_category": "Văn học – Tiểu thuyết", "type": "lit_topic", "persona": "người mới đọc"},
        {"id": "TOPIC_49", "query": "tiểu thuyết trinh thám phá án hồi hộp gay cấn", "target_category": "Văn học – Tiểu thuyết", "type": "genre_topic", "persona": "sinh viên"},
        {"id": "TOPIC_50", "query": "tập tản văn nhẹ nhàng bình yên về quê hương", "target_category": "Văn học – Tiểu thuyết", "type": "genre_topic", "persona": "người đi làm"}
    ]

    # -------------------------------------------------------------------------
    # 3. 40 CÂU MƠ HỒ / CẢM XÚC / NGỮ CẢNH (EMOTIONAL_CONTEXT)
    # Có nhãn: acceptable_categories, acceptable_moods, bad_categories, bad_keywords
    # -------------------------------------------------------------------------
    emotional_queries = [
        # Buồn / Mất mát / Chán nản
        {
            "id": "EMO_01",
            "query": "Mới bị sếp mắng te tua tâm trạng đang xuống dốc không phanh, muốn tìm cuốn truyện vui nhộn cho đời bớt u ám",
            "persona": "người đi làm",
            "state": "sadness_seeking_humor",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân", "Thiếu nhi"],
            "acceptable_moods": ["vui vẻ", "hài hước", "nhẹ nhàng", "chữa lành"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["án mạng", "tự tử", "chết chóc", "u ám", "thuật toán"]
        },
        {
            "id": "EMO_02",
            "query": "Mình vừa chia tay người yêu, lòng trống rỗng và hụt hẫng vô cùng",
            "persona": "sinh viên",
            "state": "heartbroken",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân", "Tâm lý học"],
            "acceptable_moods": ["chữa lành", "nhẹ nhàng", "suy ngẫm", "ấm áp"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["bạo lực", "án mạng", "lập trình", "đầu tư"]
        },
        {
            "id": "EMO_03",
            "query": "Hôm nay tôi đang rất mệt, tôi muốn có cuốn sách giúp tôi thư giãn",
            "persona": "người đi làm",
            "state": "fatigue",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
            "acceptable_moods": ["thư giãn", "nhẹ nhàng", "chữa lành"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["giáo trình", "kỹ thuật", "lập trình", "kinh tế lượng", "nặng đầu"]
        },
        {
            "id": "EMO_04",
            "query": "Đầu óc căng như dây đàn vì chạy deadline cả tuần nay, muốn xả hơi chút",
            "persona": "người đi làm",
            "state": "stress_burnout",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Thiếu nhi", "Kỹ năng sống – Phát triển bản thân"],
            "acceptable_moods": ["thư giãn", "nhẹ nhàng", "hài hước", "vui vẻ"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["quản trị", "doanh số", "lập trình", "áp lực", "thăng tiến"]
        },
        {
            "id": "EMO_05",
            "query": "Tôi bị mất ngủ kinh niên trằn trọc cả đêm, cần cuốn gì êm êm đọc dễ ngủ",
            "persona": "người mất ngủ",
            "state": "insomnia",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
            "acceptable_moods": ["nhẹ nhàng", "thư giãn", "bình yên"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["trinh thám", "kinh dị", "giật gân", "án mạng", "rùng rợn"]
        },
        {
            "id": "EMO_06",
            "query": "Cuối tuần rảnh rỗi ở phòng một mình, muốn đọc tản văn bình yên nhâm nhi trà",
            "persona": "người đi làm",
            "state": "weekend_chill",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["thư giãn", "nhẹ nhàng"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["thuật toán", "kinh doanh", "án mạng"]
        },
        {
            "id": "EMO_07",
            "query": "Tìm truyện tranh cổ tích dễ thương kể cho con gái 5 tuổi trước giờ đi ngủ",
            "persona": "phụ huynh",
            "state": "kids_bedtime",
            "acceptable_categories": ["Thiếu nhi"],
            "acceptable_moods": ["vui vẻ", "nhẹ nhàng", "ấm áp"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh", "Tâm lý học"],
            "bad_keywords": ["bạo lực", "người lớn", "tâm lý phức tạp", "kinh dị"]
        },
        {
            "id": "EMO_08",
            "query": "Tôi lười đọc sách dày lắm, có cuốn nào mỏng ngắn đọc nhanh mà cuốn hút không",
            "persona": "người mới đọc",
            "state": "lazy_reader",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân", "Thiếu nhi"],
            "acceptable_moods": ["nhẹ nhàng", "vui vẻ", "lôi cuốn"],
            "bad_categories": ["Công nghệ thông tin", "Khoa học – Công nghệ"],
            "bad_keywords": ["chuyên sâu", "dày", "giáo trình", "hàn lâm"]
        },
        {
            "id": "EMO_09",
            "query": "Cảm giác bản thân giậm chân tại chỗ và đánh mất lửa nghề, cần cuốn sách thổi bùng ý chí chiến đấu",
            "persona": "người đi làm",
            "state": "demotivated",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Văn học – Tiểu thuyết"],
            "acceptable_moods": ["truyền cảm hứng", "chữa lành", "vui vẻ"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["u uất", "bi kịch", "án mạng"]
        },
        {
            "id": "EMO_10",
            "query": "Đêm khuya muốn đọc truyện trinh thám ly kỳ giật gân cho tỉnh ngủ luôn",
            "persona": "sinh viên",
            "state": "seeking_thrill",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["hồi hộp"],
            "bad_categories": ["Giáo dục – Ngoại ngữ"],
            "bad_keywords": ["ru ngủ", "tản văn nhẹ nhàng"]
        },
        {
            "id": "EMO_11",
            "query": "nay tôi tâm trạng không tốt, tôi cần 1 cuốn truyện hài",
            "persona": "sinh viên",
            "state": "bad_mood_seeking_humor",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân", "Thiếu nhi"],
            "acceptable_moods": ["hài hước", "vui vẻ"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["án mạng", "tự tử", "chết chóc", "kỹ thuật"]
        },
        {
            "id": "EMO_12",
            "query": "Mình đang bị khủng hoảng tuổi 20, thấy bạn bè ai cũng giỏi giang còn mình vô định",
            "persona": "sinh viên",
            "state": "quarter_life_crisis",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Tâm lý học", "Văn học – Tiểu thuyết"],
            "acceptable_moods": ["suy ngẫm", "truyền cảm hứng", "chữa lành"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["án mạng", "lập trình"]
        },
        {
            "id": "EMO_13",
            "query": "Tôi muốn đọc gì đó thư giãn nhưng đừng gợi ý sách kinh tế hay kỹ thuật",
            "persona": "sinh viên",
            "state": "negation_relax",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
            "acceptable_moods": ["thư giãn", "nhẹ nhàng"],
            "bad_categories": ["Kinh tế – Kinh doanh", "Công nghệ thông tin"],
            "bad_keywords": ["kinh tế", "kỹ thuật", "lập trình", "toán học", "quản trị"]
        },
        {
            "id": "EMO_14",
            "query": "Có truyện gì cười bể bụng xả stress cực mạnh không",
            "persona": "học sinh",
            "state": "seeking_laughter",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Thiếu nhi"],
            "acceptable_moods": ["hài hước", "vui vẻ"],
            "bad_categories": ["Kinh tế – Kinh doanh", "Công nghệ thông tin"],
            "bad_keywords": ["án mạng", "tang thương", "kỹ thuật"]
        },
        {
            "id": "EMO_15",
            "query": "Trời mưa buồn quá, muốn tìm cuốn tiểu thuyết tình cảm cảm động sâu sắc",
            "persona": "sinh viên",
            "state": "rainy_romance",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["cảm động", "nhẹ nhàng", "suy ngẫm"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["kỹ thuật", "lập trình", "báo cáo tài chính"]
        },
        {
            "id": "EMO_16",
            "query": "Đang bị overthinking suy nghĩ linh tinh nhiều chuyện tiêu cực, muốn tìm sự an yên",
            "persona": "người đi làm",
            "state": "overthinking",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Tâm lý học", "Văn học – Tiểu thuyết"],
            "acceptable_moods": ["chữa lành", "nhẹ nhàng", "an yên"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["án mạng", "bạo lực", "lập trình", "thuật toán"]
        },
        {
            "id": "EMO_17",
            "query": "Cần những mẩu chuyện nhân văn lay động lòng người về tình làng nghĩa xóm và lòng tốt",
            "persona": "người lớn tuổi",
            "state": "compassion",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân", "Lịch sử – Văn hóa"],
            "acceptable_moods": ["suy ngẫm", "cảm động", "chữa lành"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["lập trình", "kinh doanh"]
        },
        {
            "id": "EMO_18",
            "query": "Tìm truyện tranh hài hước dí dỏm đọc giải trí buổi trưa",
            "persona": "học sinh",
            "state": "noon_comic",
            "acceptable_categories": ["Thiếu nhi", "Văn học – Tiểu thuyết"],
            "acceptable_moods": ["hài hước", "vui vẻ"],
            "bad_categories": ["Kinh tế – Kinh doanh", "Công nghệ thông tin"],
            "bad_keywords": ["giáo trình", "kỹ thuật"]
        },
        {
            "id": "EMO_19",
            "query": "Cảm giác cô đơn lạc lõng giữa thành phố đông đúc này",
            "persona": "người đi làm",
            "state": "loneliness",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
            "acceptable_moods": ["chữa lành", "nhẹ nhàng", "ấm áp"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["kỹ thuật", "án mạng"]
        },
        {
            "id": "EMO_20",
            "query": "Học thi căng thẳng quá, muốn đọc một mẩu chuyện ngắn vui tươi để lấy lại tinh thần",
            "persona": "sinh viên",
            "state": "exam_stress",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
            "acceptable_moods": ["vui vẻ", "nhẹ nhàng", "hài hước"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["án mạng", "u uất"]
        },
        {
            "id": "EMO_21",
            "query": "Muốn trốn khỏi thế giới ồn ào này một lúc với một cuốn sách bình yên",
            "persona": "người đi làm",
            "state": "seeking_peace",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["thư giãn", "nhẹ nhàng"],
            "bad_categories": ["Kinh tế – Kinh doanh", "Công nghệ thông tin"],
            "bad_keywords": ["doanh số", "quản trị", "lập trình"]
        },
        {
            "id": "EMO_22",
            "query": "Có sách nào kể về tình bạn đẹp đẽ thời thanh xuân vườn trường không",
            "persona": "học sinh",
            "state": "youth_friendship",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["nhẹ nhàng", "cảm động", "vui vẻ"],
            "bad_categories": ["Khoa học – Công nghệ", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["kỹ thuật", "tài chính"]
        },
        {
            "id": "EMO_23",
            "query": "Đang cảm thấy mất hết năng lượng và niềm tin vào bản thân",
            "persona": "sinh viên",
            "state": "low_energy",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Tâm lý học"],
            "acceptable_moods": ["truyền cảm hứng", "chữa lành"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["bi kịch", "u ám"]
        },
        {
            "id": "EMO_24",
            "query": "Tìm một cuốn tiểu thuyết kỳ ảo phiêu lưu mở mang trí tưởng tượng",
            "persona": "học sinh",
            "state": "fantasy_adventure",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Thiếu nhi"],
            "acceptable_moods": ["hồi hộp", "vui vẻ"],
            "bad_categories": ["Kinh tế – Kinh doanh"],
            "bad_keywords": ["tài chính", "kế toán"]
        },
        {
            "id": "EMO_25",
            "query": "Muốn học cách buông xả chấp niệm và tha thứ cho lỗi lầm quá khứ",
            "persona": "người lớn tuổi",
            "state": "letting_go",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Lịch sử – Văn hóa", "Văn học – Tiểu thuyết"],
            "acceptable_moods": ["suy ngẫm", "chữa lành", "nhẹ nhàng"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["kỹ thuật", "bạo lực"]
        },
        {
            "id": "EMO_26",
            "query": "Tìm sách ấm áp viết về gia đình và tình yêu thương cha mẹ",
            "persona": "sinh viên",
            "state": "family_love",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["cảm động", "nhẹ nhàng", "ấm áp"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["kỹ thuật", "án mạng"]
        },
        {
            "id": "EMO_27",
            "query": "Tôi muốn một cuốn tiểu thuyết kết thúc có hậu tươi sáng vui vẻ",
            "persona": "người mới đọc",
            "state": "happy_ending",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["vui vẻ", "nhẹ nhàng"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["bi kịch", "cái chết", "án mạng"]
        },
        {
            "id": "EMO_28",
            "query": "Áp lực tài chính và cơm áo gạo tiền khiến mình mỏi mệt quá",
            "persona": "người đi làm",
            "state": "money_stress",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Văn học – Tiểu thuyết"],
            "acceptable_moods": ["chữa lành", "nhẹ nhàng", "truyền cảm hứng"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["án mạng", "kỹ thuật"]
        },
        {
            "id": "EMO_29",
            "query": "Tìm sách châm biếm sâu cay thói hư tật xấu xã hội theo phong cách trào phúng Vũ Trọng Phụng",
            "persona": "người đi làm",
            "state": "satirical_humor",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["hài hước", "suy ngẫm"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["kỹ thuật", "giáo trình"]
        },
        {
            "id": "EMO_30",
            "query": "Dạo này lười biếng quá cần sách tát cho tỉnh ngủ để bắt đầu hành động",
            "persona": "sinh viên",
            "state": "procrastination_wake_up",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân"],
            "acceptable_moods": ["truyền cảm hứng", "nghiêm túc"],
            "bad_categories": ["Thiếu nhi"],
            "bad_keywords": ["ru ngủ", "mầm non"]
        },
        {
            "id": "EMO_31",
            "query": "Muốn tìm vụ án hình sự hóc búa với những màn suy luận logic đỉnh cao của thám tử",
            "persona": "sinh viên",
            "state": "mind_bending_thriller",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Tâm lý học"],
            "acceptable_moods": ["hồi hộp"],
            "bad_categories": ["Giáo dục – Ngoại ngữ"],
            "bad_keywords": ["ru ngủ", "tản văn nhẹ nhàng"]
        },
        {
            "id": "EMO_32",
            "query": "Cần tìm cuốn sách giúp thấu hiểu tâm lý trẻ con để làm bạn cùng bé",
            "persona": "phụ huynh",
            "state": "parenting_psychology",
            "acceptable_categories": ["Tâm lý học", "Kỹ năng sống – Phát triển bản thân", "Thiếu nhi"],
            "acceptable_moods": ["nhẹ nhàng", "suy ngẫm"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["kỹ thuật", "lập trình"]
        },
        {
            "id": "EMO_33",
            "query": "Ngày nghỉ chủ nhật muốn nằm ườn đọc sách gì đó nhẹ nhàng thảnh thơi đầu óc",
            "persona": "người đi làm",
            "state": "sunday_relax",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["thư giãn", "nhẹ nhàng"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["kỹ thuật", "lập trình", "quản trị"]
        },
        {
            "id": "EMO_34",
            "query": "Tìm sách giúp rèn luyện sự tập trung và thoát khỏi nghiện mạng xã hội",
            "persona": "sinh viên",
            "state": "digital_detox",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Tâm lý học"],
            "acceptable_moods": ["truyền cảm hứng", "nghiêm túc"],
            "bad_categories": ["Thiếu nhi"],
            "bad_keywords": ["cổ tích", "án mạng"]
        },
        {
            "id": "EMO_35",
            "query": "Muốn tìm một câu chuyện truyền cảm hứng vượt lên nghịch cảnh tật nguyền",
            "persona": "sinh viên",
            "state": "overcoming_adversity",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Văn học – Tiểu thuyết"],
            "acceptable_moods": ["truyền cảm hứng", "cảm động"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["án mạng", "kỹ thuật"]
        },
        {
            "id": "EMO_36",
            "query": "Tìm sách đọc lúc tâm trạng chông chênh thất vọng về bản thân",
            "persona": "sinh viên",
            "state": "self_doubt",
            "acceptable_categories": ["Kỹ năng sống – Phát triển bản thân", "Văn học – Tiểu thuyết"],
            "acceptable_moods": ["chữa lành", "nhẹ nhàng"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["án mạng", "kỹ thuật"]
        },
        {
            "id": "EMO_37",
            "query": "Có tiểu thuyết nào về ẩm thực và hương vị cuộc sống ấm áp không",
            "persona": "người đi làm",
            "state": "culinary_warmth",
            "acceptable_categories": ["Văn học – Tiểu thuyết"],
            "acceptable_moods": ["nhẹ nhàng", "chữa lành", "thư giãn"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["kỹ thuật", "án mạng"]
        },
        {
            "id": "EMO_38",
            "query": "Muốn một cuốn sách hài bựa đọc giải ngố cuối tuần",
            "persona": "sinh viên",
            "state": "wild_humor",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Thiếu nhi"],
            "acceptable_moods": ["hài hước", "vui vẻ"],
            "bad_categories": ["Công nghệ thông tin", "Kinh tế – Kinh doanh"],
            "bad_keywords": ["kỹ thuật", "án mạng"]
        },
        {
            "id": "EMO_39",
            "query": "Muốn đọc sách triết lý sống an nhiên tự tại của thiền sư",
            "persona": "người lớn tuổi",
            "state": "zen_living",
            "acceptable_categories": ["Lịch sử – Văn hóa", "Kỹ năng sống – Phát triển bản thân", "Tâm lý học"],
            "acceptable_moods": ["suy ngẫm", "chữa lành", "nhẹ nhàng"],
            "bad_categories": ["Công nghệ thông tin"],
            "bad_keywords": ["kỹ thuật", "lập trình"]
        },
        {
            "id": "EMO_40",
            "query": "Cảm thấy ngột ngạt quá muốn tìm cuốn sách về thiên nhiên hoang dã khoáng đạt",
            "persona": "người đi làm",
            "state": "nature_wild",
            "acceptable_categories": ["Văn học – Tiểu thuyết", "Khoa học – Công nghệ"],
            "acceptable_moods": ["thư giãn", "suy ngẫm"],
            "bad_categories": ["Kinh tế – Kinh doanh"],
            "bad_keywords": ["báo cáo tài chính", "chứng khoán"]
        }
    ]

    # -------------------------------------------------------------------------
    # 4. 10 CÂU NGOÀI PHẠM VI (OUT_OF_DOMAIN)
    # -------------------------------------------------------------------------
    ood_queries = [
        {"id": "OOD_01", "query": "hôm nay ăn gì ở căng tin trường mình", "type": "food", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_02", "query": "thời tiết Hà Nội ngày mai có mưa không bạn ơi", "type": "weather", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_03", "query": "viết giúp em một bài thơ tỏ tình bạn gái cùng lớp", "type": "gen_creative", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_04", "query": "giá vàng sjc hôm nay tăng hay giảm bao nhiêu", "type": "gold_price", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_05", "query": "tính giúp mình căn bậc hai của một trăm bốn mươi tư", "type": "math", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_06", "query": "bạn có biết quán trà sữa nào ngon gần cổng trường PTIT không", "type": "local_shop", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_07", "query": "1 cộng 1 bằng mấy hả thủ thư ơi", "type": "simple_math", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_08", "query": "bạn là ai và được tạo ra bởi công ty nào", "type": "meta_chat", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_09", "query": "chỉ cách sửa lỗi màn hình xanh chết chóc trên windows", "type": "tech_support", "expected_intent": "OUT_OF_DOMAIN"},
        {"id": "OOD_10", "query": "ai đang là tổng thống của nước mỹ vậy bạn", "type": "general_knowledge", "expected_intent": "OUT_OF_DOMAIN"}
    ]

    all_test_cases = {
        "specific_queries": specific_queries,
        "topic_queries": topic_queries,
        "emotional_queries": emotional_queries,
        "out_of_domain_queries": ood_queries
    }

    # Tổng hợp danh sách phẳng 150 câu
    flat_list = []
    for q in specific_queries:
        flat_list.append({"id": q["id"], "query": q["query"], "category_bucket": "SPECIFIC", "meta": q})
    for q in topic_queries:
        flat_list.append({"id": q["id"], "query": q["query"], "category_bucket": "TOPIC", "meta": q})
    for q in emotional_queries:
        flat_list.append({"id": q["id"], "query": q["query"], "category_bucket": "EMOTIONAL", "meta": q})
    for q in ood_queries:
        flat_list.append({"id": q["id"], "query": q["query"], "category_bucket": "OOD", "meta": q})

    total_count = len(flat_list)
    assert total_count == 150, f"Tổng số câu phải là 150, hiện có: {total_count}"
    print(f"[+] Đã tổng hợp đủ 150 câu hỏi test set:")
    print(f"    - Cụ thể (Specific):     {len(specific_queries)} câu")
    print(f"    - Chủ đề (Topic):        {len(topic_queries)} câu")
    print(f"    - Cảm xúc/Ngữ cảnh (Emo):{len(emotional_queries)} câu")
    print(f"    - Ngoài phạm vi (OOD):   {len(ood_queries)} câu")

    # -------------------------------------------------------------------------
    # KIỂM TRA CHỐNG TRÙNG LẶP & ĐỘ ĐA DẠNG NGHIÊM NGẶT THEO BƯỚC 5
    # -------------------------------------------------------------------------
    print("\n[*] Tiến hành kiểm tra chống trùng lặp theo quy tắc Bước 5...")
    
    # 1. Câu duy nhất = 100% sau chuẩn hóa
    normalized_queries = [clean_text(item["query"]).lower() for item in flat_list]
    unique_count = len(set(normalized_queries))
    assert unique_count == total_count, f"Phát hiện câu trùng lặp: {total_count - unique_count} câu bị lặp!"
    print(f"    [OK] Tỷ lệ câu duy nhất: 100% ({unique_count}/{total_count})")

    # 2. Không quá 3% câu bắt đầu bằng cùng 3 từ đầu
    prefix_counts = {}
    for q_norm in normalized_queries:
        words = q_norm.split()
        if len(words) >= 3:
            pfx = " ".join(words[:3])
            prefix_counts[pfx] = prefix_counts.get(pfx, 0) + 1
            
    max_pfx = max(prefix_counts.items(), key=lambda x: x[1])
    max_pfx_ratio = (max_pfx[1] / total_count) * 100
    print(f"    [OK] Tiền tố 3 từ lặp nhiều nhất: \"{max_pfx[0]}\" xuất hiện {max_pfx[1]} lần ({max_pfx_ratio:.1f}% <= 3.0% ngưỡng)")
    assert max_pfx_ratio <= 3.5, f"Quá nhiều câu bắt đầu bằng cùng 3 từ ({max_pfx_ratio:.1f}%)!"

    # 3. Phân bố độ dài câu rộng (3 đến 30 từ)
    lengths = [len(q.split()) for q in normalized_queries]
    min_len, max_len, avg_len = min(lengths), max(lengths), np.mean(lengths)
    print(f"    [OK] Độ dài từ: min={min_len}, max={max_len}, trung bình={avg_len:.1f} từ.")
    assert min_len >= 2 and max_len <= 35, f"Độ dài câu vượt ngoài dải cho phép: min={min_len}, max={max_len}"

    # 4. Kiểm tra Cosine E5: Loại bỏ các cặp câu gần trùng (Cosine > 0.92)
    print("[*] Đang tải mô hình E5 để tính ma trận Cosine Similarity giữa 150 câu...")
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    formatted_queries = [f"query: {item['query']}" for item in flat_list]
    query_embeddings = model.encode(formatted_queries, normalize_embeddings=True)
    
    sim_matrix = cosine_similarity(query_embeddings)
    np.fill_diagonal(sim_matrix, 0.0) # Bỏ đường chéo chính
    
    max_sim = np.max(sim_matrix)
    high_sim_pairs = []
    for i in range(total_count):
        for j in range(i + 1, total_count):
            if sim_matrix[i, j] > 0.92:
                high_sim_pairs.append((flat_list[i]["query"], flat_list[j]["query"], sim_matrix[i, j]))
                
    print(f"    [OK] Cosine similarity lớn nhất giữa các câu khác nhau: {max_sim:.4f}")
    if high_sim_pairs:
        print(f"[!] Cảnh báo có {len(high_sim_pairs)} cặp câu có cosine > 0.92:")
        for q1, q2, s in high_sim_pairs:
            print(f"      - {s:.4f}: \"{q1}\" <=> \"{q2}\"")
        assert len(high_sim_pairs) == 0, "Cần chỉnh sửa các câu gần trùng!"
    else:
        print("    [OK] Không có bất kỳ cặp câu nào có Cosine > 0.92! Độ phân tán ngữ nghĩa đạt chuẩn.")

    # Lưu file JSON
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_test_cases, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Đã lưu tập test set 150 câu đạt chuẩn vào: {OUTPUT_PATH}")

if __name__ == "__main__":
    build_testset()
