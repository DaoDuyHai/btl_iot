import re
import unicodedata

def clean_text(text: str) -> str:
    if not text:
        return ""
    return str(text).strip()

def strip_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt chuẩn Unicode phục vụ tìm kiếm không dấu."""
    t = clean_text(text)
    if not t:
        return ""
    t = unicodedata.normalize('NFD', t)
    t = ''.join([c for c in t if unicodedata.category(c) != 'Mn'])
    t = t.replace('đ', 'd').replace('Đ', 'D')
    return t.lower().strip()

# -----------------------------------------------------------------------------
# 1. TỪ ĐIỂN CẢM XÚC, NGỮ CẢNH & TRẠNG THÁI NGƯỜI ĐỌC (OFFLINE LEXICON)
# -----------------------------------------------------------------------------
EMOTIONAL_PATTERNS = {
    "breakup_healing": {
        "display_name": "Thất tình / Tan vỡ tình cảm",
        "keywords": [
            "chia tay", "vừa chia tay", "người yêu", "thất tình", "tan vỡ", "đổ vỡ", "chữa lành", "chữa lành tâm hồn",
            "vết thương lòng", "muốn khóc", "khóc", "cảm động", "rơi nước mắt", "ấm áp", "yêu đời hơn", "yêu đời"
        ],
        "target_moods": ["chữa lành", "nhẹ nhàng", "bình yên", "vui vẻ"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân", "Tâm lý học"],
        "avoid_keywords": ["kỹ thuật", "lập trình", "toán học", "án mạng", "bạo lực"],
        "expanded_queries": [
            "sách chữa lành tâm hồn vỗ về cảm xúc bình yên",
            "tản văn nhẹ nhàng vượt qua chia tay và đổ vỡ",
            "truyện ngắn ấm áp xoa dịu trái tim tổn thương"
        ]
    },
    "sadness": {
        "display_name": "Buồn bã / Tâm trạng chùng",
        "keywords": [
            "buồn", "chán nản", "thất tình", "tâm trạng chùng", "trống rỗng", "tổn thương", "đau lòng",
            "cô đơn", "lạc lõng", "tuyệt vọng", "tâm trạng không tốt", "tâm trạng tồi tệ", "tâm trạng tệ",
            "tâm trạng không được tốt", "tâm trạng đang không tốt", "không vui", "đang không vui",
            "tụt mood", "down mood", "tụt mút", "chán đời", "chán quá", "hôm nay tệ quá", "nặng lòng",
            "muốn giải sầu", "giải khuây", "u uất", "tức giận", "thất vọng", "bình tâm", "kiểm soát cảm xúc", "nóng giận", "bình tĩnh"
        ],
        "target_moods": ["vui vẻ", "hài hước", "nhẹ nhàng", "chữa lành"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
        "avoid_keywords": ["án mạng", "cái chết", "đám tang", "tự tử", "bạo lực", "chiến tranh", "tang thương", "u uất", "kinh dị"],
        "expanded_queries": [
            "sách hài hước dí dỏm mang lại tiếng cười vui vẻ",
            "truyện ngắn nhẹ nhàng ấm áp xua tan nỗi buồn",
            "tản văn chữa lành tâm hồn bình yên"
        ]
    },
    "loneliness": {
        "display_name": "Cô đơn / Lạc lõng",
        "keywords": ["cô đơn", "lạc lõng", "trống trải", "một mình", "bơ vơ", "lẻ loi"],
        "target_moods": ["ấm áp", "nhẹ nhàng", "bình yên"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
        "avoid_keywords": ["án mạng", "kinh dị", "kỹ thuật"],
        "expanded_queries": [
            "tản văn ấm áp xua tan cô đơn trống trải",
            "sách bầu bạn xoa dịu những ngày một mình",
            "truyện ngắn bình yên sưởi ấm tâm hồn"
        ]
    },
    "humor_entertainment": {
        "display_name": "Cần tiếng cười / Hài hước",
        "keywords": [
            "truyện hài", "sách hài", "hài hước", "truyện cười", "vui nhộn", "hài hước dí dỏm",
            "đọc cho vui", "đọc cho cười", "muốn cười", "gây cười", "dí dỏm", "giải trí vui vẻ",
            "truyện vui", "hài bựa", "hài hước nhẹ nhàng", "cười sảng khoái", "xả stress vui vẻ",
            "tiểu thuyết hài", "chuyện cười", "cười bể bụng", "đọc giải trí"
        ],
        "target_moods": ["hài hước", "vui vẻ"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
        "avoid_keywords": ["án mạng", "cái chết", "đám tang", "tự tử", "bạo lực", "chiến tranh", "tang thương", "u uất", "kinh dị", "kỹ thuật"],
        "expanded_queries": [
            "truyện hài hước dí dỏm vui nhộn đem lại tiếng cười sảng khoái",
            "sách đọc giải trí vui vẻ xả stress nhẹ đầu",
            "truyện ngắn tiểu thuyết hài hước vui vẻ dí dỏm"
        ]
    },
    "fatigue_relax": {
        "display_name": "Mệt mỏi / Cần thư giãn",
        "keywords": ["mệt", "mỏi mệt", "kiệt sức", "thư giãn", "chill", "nghỉ ngơi", "thảnh thơi", "thư thái", "nhâm nhi", "cuối tuần", "bình yên", "ngắn ngắn nhẹ tênh", "nhẹ tênh"],
        "target_moods": ["thư giãn", "nhẹ nhàng"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
        "avoid_keywords": ["thuật toán", "lập trình", "toán cao cấp", "kinh tế lượng", "kỹ thuật", "giáo trình", "nặng đầu", "chiến lược", "quản trị", "lớp 2"],
        "expanded_queries": [
            "sách nhẹ nhàng dễ đọc để thư giãn thảnh thơi",
            "tản văn bình dị ấm áp đọc cuối tuần",
            "truyện ngắn êm đềm bình yên xả hơi"
        ]
    },
    "stress_burnout": {
        "display_name": "Căng thẳng / Áp lực (Stress)",
        "keywords": ["stress", "áp lực", "deadline", "quá tải", "căng thẳng", "nhẹ đầu", "đầu óc rối bời", "mệt mỏi công việc", "burnout", "căng như dây đàn", "đồ án tốt nghiệp"],
        "target_moods": ["thư giãn", "nhẹ nhàng", "hài hước"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân"],
        "avoid_keywords": ["thăng tiến", "quản trị", "lãnh đạo", "kỹ thuật", "lập trình", "tài chính", "áp lực", "doanh số", "đầu tư", "toán học"],
        "expanded_queries": [
            "sách đọc giải trí nhẹ đầu xả stress áp lực",
            "truyện vui nhộn dễ đọc không cần suy nghĩ nhiều",
            "tản văn nhẹ nhàng bình yên lấy lại thảnh thơi"
        ]
    },
    "insomnia": {
        "display_name": "Mất ngủ / Khó ngủ",
        "keywords": ["mất ngủ", "khó ngủ", "đêm khuya", "trằn trọc", "ru ngủ", "dễ ngủ", "chìm vào giấc ngủ", "ngủ một giấc thật ngon", "ngủ ngon", "mỉm cười", "giấc ngủ ngon"],
        "target_moods": ["nhẹ nhàng", "thư giãn", "vui vẻ"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân", "Thiếu nhi"],
        "avoid_keywords": ["trinh thám", "án mạng", "rùng rợn", "kinh dị", "hồi hộp", "kỹ thuật", "giật gân", "khoa học thường thức"],
        "expanded_queries": [
            "sách êm đềm ru ngủ nhẹ nhàng đêm khuya",
            "tản văn bình yên dễ chìm vào giấc ngủ",
            "truyện ngắn dịu dàng ấm áp thư thái"
        ]
    },
    "children_bedtime": {
        "display_name": "Đọc cho trẻ em / Bé ngủ",
        "keywords": ["đọc cho con", "cho bé", "con gái", "con trai", "trước giờ đi ngủ", "kể chuyện bé", "ru bé", "5 tuổi", "6 tuổi", "mầm non", "tiểu học"],
        "target_moods": ["vui vẻ", "nhẹ nhàng", "thư giãn"],
        "reading_effort": "nhẹ",
        "audience": "trẻ em",
        "preferred_categories": ["Thiếu nhi"],
        "avoid_keywords": ["người lớn", "tâm lý phức tạp", "bạo lực", "kinh dị", "kỹ thuật"],
        "expanded_queries": [
            "truyện tranh thiếu nhi đọc cho bé trước giờ đi ngủ",
            "truyện cổ tích nhẹ nhàng ấm áp cho trẻ em",
            "sách tranh đồng thoại vui nhộn cho bé"
        ]
    },
    "beginner_reader": {
        "display_name": "Người mới bắt đầu đọc",
        "keywords": ["mới bắt đầu đọc", "mới tập đọc", "chưa quen đọc nhiều", "sách mỏng", "dễ đọc", "ngại đọc nhiều chữ", "nhiều hình minh họa", "hình minh họa", "hình vẽ", "vừa có nhiều hình minh họa vừa hài hước dễ đọc", "hài hước dễ đọc"],
        "target_moods": ["nhẹ nhàng", "vui vẻ", "hài hước"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Thiếu nhi", "Kỹ năng sống – Phát triển bản thân"],
        "avoid_keywords": ["chuyên sâu", "hàn lâm", "giáo trình", "dày", "nặng đầu", "kỹ thuật", "thuật toán"],
        "expanded_queries": [
            "sách mỏng ngắn dễ đọc cho người mới bắt đầu",
            "truyện tranh tiểu thuyết ngắn hài hước nhiều hình minh họa dễ đọc",
            "tác phẩm văn học ngắn nhẹ nhàng lôi cuốn vui vẻ"
        ]
    },
    "demotivated": {
        "display_name": "Mất động lực / Bế tắc",
        "keywords": [
            "mất động lực", "chán nản công việc", "bế tắc", "mất phương hướng", "tìm lại động lực", "tìm cảm hứng", "vực dậy",
            "uể oải", "không có chút động lực", "không có động lực", "mất cảm hứng", "chán học", "lười học",
            "học tập, cứu mình với", "cứu mình với", "không biết tương lai đi về đâu", "chênh vênh", "lạc lối"
        ],
        "target_moods": ["truyền cảm hứng", "chữa lành"],
        "reading_effort": "vừa",
        "preferred_categories": ["Kỹ năng sống – Phát triển bản thân", "Văn học – Tiểu thuyết"],
        "avoid_keywords": ["sách bi kịch", "u ám", "đau buồn", "kỹ thuật", "công nghệ thông tin", "lập trình", "arduino", "thuật toán"],
        "expanded_queries": [
            "sách truyền cảm hứng sống tích cực và vươn lên",
            "sách tiếp thêm động lực vượt qua bế tắc học tập",
            "câu chuyện nghị lực thắp sáng niềm tin cuộc sống"
        ]
    },
    "positivity_hope": {
        "display_name": "Tìm kiếm hy vọng / Lạc quan",
        "keywords": [
            "đáng sống", "tích cực", "yêu đời", "cuộc đời này vẫn còn", "hy vọng", "lạc quan", "ấm áp",
            "tin yêu", "tươi sáng", "động lực sống", "niềm tin cuộc sống", "mang lại hy vọng", "yêu bản thân",
            "học cách yêu bản thân", "ngày thật tồi tệ", "một ngày thật tồi tệ", "ngày tồi tệ"
        ],
        "target_moods": ["vui vẻ", "chữa lành", "truyền cảm hứng"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Kỹ năng sống – Phát triển bản thân", "Văn học – Tiểu thuyết"],
        "avoid_keywords": ["thuật toán", "lập trình", "toán học", "kỹ thuật", "công nghệ thông tin", "tài chính", "dự báo", "báo cáo tài chính"],
        "expanded_queries": [
            "sách truyền cảm hứng sống tích cực và yêu đời",
            "tản văn chữa lành tìm lại niềm tin và hy vọng cuộc sống",
            "cuốn sách ấm áp nuôi dưỡng tâm hồn và mang lại hy vọng"
        ]
    },
    "anxiety_fear": {
        "display_name": "Lo âu / Bất an",
        "keywords": [
            "sợ thất bại", "lo âu", "lo sợ", "bất an", "tương lai vô định", "đồng cảm", "khủng hoảng tuổi",
            "áp lực cuộc sống", "tự ti", "tự ti ngoại hình", "tự ti về ngoại hình", "lời động viên"
        ],
        "target_moods": ["chữa lành", "thư giãn", "truyền cảm hứng"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Kỹ năng sống – Phát triển bản thân", "Tâm lý học", "Văn học – Tiểu thuyết"],
        "avoid_keywords": ["thuật toán", "lập trình", "kỹ thuật", "thiên văn học", "vũ trụ", "khoa học", "tài chính"],
        "expanded_queries": [
            "sách chữa lành nỗi sợ thất bại và lo âu",
            "sách đồng cảm và vượt qua khủng hoảng tuổi trẻ",
            "tâm lý học chữa lành sự tự ti và bất an"
        ]
    },
    "thriller_suspense": {
        "display_name": "Hồi hộp / Trinh thám",
        "keywords": ["hồi hộp", "ly kỳ", "gay cấn", "nghẹt thở", "tỉnh cả ngủ", "trinh thám", "phá án", "giật gân"],
        "target_moods": ["hồi hộp"],
        "reading_effort": "vừa",
        "preferred_categories": ["Văn học – Tiểu thuyết"],
        "avoid_keywords": ["sách ru ngủ", "nhẹ nhàng", "tản văn"],
        "expanded_queries": [
            "tiểu thuyết trinh thám gay cấn ly kỳ nghẹt thở",
            "truyện trinh thám phá án hồi hộp bất ngờ",
            "vụ án bí ẩn nghẹt thở không dứt ra được"
        ]
    },
    "comic_manga": {
        "display_name": "Truyện tranh / Giải trí",
        "keywords": ["truyện tranh", "comic", "manga", "manhwa", "truyện hình", "đọc tranh"],
        "target_moods": ["vui vẻ", "hài hước", "nhẹ nhàng"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Thiếu nhi", "Văn học – Tiểu thuyết"],
        "avoid_keywords": ["giáo trình", "kỹ thuật", "kinh tế lượng", "toán học", "hàn lâm"],
        "expanded_queries": [
            "truyện tranh giải trí vui nhộn hấp dẫn",
            "tranh truyện hài hước nhẹ nhàng xả stress",
            "comic manga giải trí vui vẻ tích cực"
        ]
    },
    "satirical_humor": {
        "display_name": "Châm biếm / Trào phúng",
        # Đã loại bỏ "vũ trọng phụng" để tránh xung đột tác giả
        "keywords": ["châm biếm", "trào phúng", "hài hước thâm thúy", "hài sâu cay", "phê phán thói đời"],
        "target_moods": ["hài hước", "suy ngẫm"],
        "reading_effort": "vừa",
        "preferred_categories": ["Văn học – Tiểu thuyết"],
        "avoid_keywords": ["chụp ảnh", "lập trình", "báo cáo tài chính", "nấu ăn", "quản trị"],
        "expanded_queries": [
            "tiểu thuyết trào phúng châm biếm xã hội sâu sắc",
            "tác phẩm văn học hài hước thâm thúy phê phán thói đời",
            "văn học kinh điển trào phúng dí dỏm"
        ]
    },
    "fantasy_magic": {
        "display_name": "Thoát ly thực tại / Kỳ ảo",
        "keywords": ["kỳ ảo", "fantasy", "thoát ly thực tại", "phép thuật", "thế giới ảo", "huyền bí", "phù thủy", "xuyên không"],
        "target_moods": ["thư giãn", "hồi hộp", "kỳ ảo"],
        "reading_effort": "vừa",
        "preferred_categories": ["Văn học – Tiểu thuyết"],
        "avoid_keywords": ["tài chính", "kinh doanh", "làm giàu", "chứng khoán", "marketing", "đầu tư", "quản trị", "bán hàng"],
        "expanded_queries": [
            "tiểu thuyết kỳ ảo phiêu lưu thế giới phép thuật hấp dẫn",
            "truyện phiêu lưu kỳ bí thoát ly thực tại",
            "tác phẩm fantasy kinh điển lôi cuốn"
        ]
    },
    "mental_nourishment": {
        "display_name": "Chữa lành / Vỗ về tâm hồn",
        "keywords": ["liều thuốc tinh thần", "thuốc tinh thần", "xoa dịu tâm hồn", "vỗ về cảm xúc"],
        "target_moods": ["chữa lành", "nhẹ nhàng", "bình yên"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Kỹ năng sống – Phát triển bản thân", "Tâm lý học"],
        "avoid_keywords": ["chữ hán", "hsk", "y học", "dược", "thuốc trị", "ngôn tình"],
        "expanded_queries": [
            "sách chữa lành tâm hồn nhẹ nhàng an yên",
            "tản văn vỗ về cảm xúc bình yên thảnh thơi",
            "những cuốn sách xoa dịu trái tim ấm áp"
        ]
    },
    "happy_ending": {
        "display_name": "Ấm áp / Kết thúc có hậu",
        "keywords": ["kết thúc có hậu", "tươi sáng", "kết hậu", "happy ending", "kết vui", "ấm áp tươi sáng"],
        "target_moods": ["vui vẻ", "nhẹ nhàng", "ấm áp"],
        "reading_effort": "nhẹ",
        "preferred_categories": ["Văn học – Tiểu thuyết", "Thiếu nhi"],
        "avoid_keywords": ["bi kịch", "cái chết", "án mạng", "u ám", "đau thương", "tang tóc"],
        "expanded_queries": [
            "tiểu thuyết kết thúc có hậu tươi sáng vui tươi",
            "câu chuyện ấm áp kết thúc viên mãn hạnh phúc",
            "truyện nhẹ nhàng vui vẻ tươi vui"
        ]
    }
}

OUT_OF_DOMAIN_PATTERNS = [
    r'thời tiết', r'hôm nay ăn gì', r'quán (cà phê|cafe|ăn|cơm|trà sữa)\s+(nào|gần đây|ở đâu|ngon|rẻ)', r'mua (trà sữa|áo|quần)',
    r'viết (code|bài|thơ) giúp', r'viết\s*(giúp|hộ|cho).*thơ', r'bài thơ tỏ tình', r'tỏ tình',
    r'tính\s+(\d+|giúp)', r'tính giúp.*căn bậc', r'căn bậc (hai|ba|\d+)',
    r'\d+\s*(?:cộng(?:\s+với)?|\+|\-|nhân(?:\s+với)?|\*|chia(?:\s+cho)?|\/)\s*\d+',
    r'1\s*\+\s*1', r'1\s*cộng\s*1', r'bằng\s+bao\s+nhiêu', r'mấy giờ rồi', r'bạn là ai',
    r'ai (đang là|là) tổng thống', r'tổng thống', r'giá vàng', r'tỉ giá', r'chứng khoán hôm nay tăng hay giảm',
    r'màn hình xanh', r'sửa lỗi.*windows', r'cài win', r'sửa máy tính', r'cổng trường',
    r'^(hello|hi|how are you|what time is it|who are you)$'
]

LOCATION_STATUS_PATTERNS = [
    r'(ở|nằm ở|đặt ở|trên)\s*(tầng|kệ|khu|vị trí)\s*(nào|mấy|gì|đâu)',
    r'(kệ|tầng|vị trí)\s*(nào|mấy|gì|đâu)',
    r'(sách|cuốn này|còn)\s*(không|bao nhiêu|có sẵn không)',
    r'(tìm|lấy)\s*sách\s*ở\s*đâu',
    r'vị trí\s*(của\s+)?.*?(ở đâu|trên kệ|là ở đâu|trong thư viện)',
    r'vị trí\s*(sách|cuốn|tác phẩm|kệ|tầng)',
    r'còn\s*(bản|cuốn|sách)\s+nào\s+.*không',
    r'còn\s*(trên|ở)\s*kệ',
    r'nằm\s+ở\s+(tầng|kệ|đâu)',
    r'là\s+ở\s+đâu\b'
]

# Ánh xạ từ khóa chuyên ngành/lĩnh vực sang Category chuẩn
TOPIC_TO_CATEGORY = {
    # 1. Giáo dục – Ngoại ngữ
    "tiếng anh chuyên ngành công nghệ thông tin": "Giáo dục – Ngoại ngữ",
    "tiếng anh chuyên ngành cntt": "Giáo dục – Ngoại ngữ",
    "tiếng anh chuyên ngành": "Giáo dục – Ngoại ngữ",
    "tiếng anh giao tiếp": "Giáo dục – Ngoại ngữ",
    "tiếng anh": "Giáo dục – Ngoại ngữ",
    "tiếng nhật": "Giáo dục – Ngoại ngữ",
    "tiếng hoa": "Giáo dục – Ngoại ngữ",
    "tiếng trung": "Giáo dục – Ngoại ngữ",
    "hán ngữ": "Giáo dục – Ngoại ngữ",
    "giáo trình hán ngữ": "Giáo dục – Ngoại ngữ",
    "tiếng hàn": "Giáo dục – Ngoại ngữ",
    "tiếng pháp": "Giáo dục – Ngoại ngữ",
    "ngoại ngữ": "Giáo dục – Ngoại ngữ",
    "ielts": "Giáo dục – Ngoại ngữ",
    "toeic": "Giáo dục – Ngoại ngữ",
    "toefl": "Giáo dục – Ngoại ngữ",
    "hsk": "Giáo dục – Ngoại ngữ",
    "topik": "Giáo dục – Ngoại ngữ",
    "jlpt": "Giáo dục – Ngoại ngữ",
    "ngữ pháp tiếng anh": "Giáo dục – Ngoại ngữ",
    "ngữ pháp": "Giáo dục – Ngoại ngữ",
    "từ vựng tiếng anh": "Giáo dục – Ngoại ngữ",
    "từ vựng": "Giáo dục – Ngoại ngữ",
    "phát âm tiếng anh": "Giáo dục – Ngoại ngữ",
    "phát âm": "Giáo dục – Ngoại ngữ",
    "dịch thuật": "Giáo dục – Ngoại ngữ",
    "học tiếng": "Giáo dục – Ngoại ngữ",
    "giao tiếp tiếng": "Giáo dục – Ngoại ngữ",

    # 2. Công nghệ thông tin
    "kiến trúc vi dịch vụ": "Công nghệ thông tin",
    "vi dịch vụ": "Công nghệ thông tin",
    "microservices": "Công nghệ thông tin",
    "microservice": "Công nghệ thông tin",
    "kiểm thử phần mềm": "Công nghệ thông tin",
    "software testing": "Công nghệ thông tin",
    "toán rời rạc": "Công nghệ thông tin",
    "lập trình android": "Công nghệ thông tin",
    "android": "Công nghệ thông tin",
    "lập trình": "Công nghệ thông tin",
    "lập chình": "Công nghệ thông tin",  # Xử lý gõ sai chính tả
    "python": "Công nghệ thông tin",
    "java": "Công nghệ thông tin",
    "c++": "Công nghệ thông tin",
    "cntt": "Công nghệ thông tin",
    "công nghệ thông tin": "Công nghệ thông tin",
    "thuật toán": "Công nghệ thông tin",
    "giải thuật": "Công nghệ thông tin",
    "giải thuật phần mềm": "Công nghệ thông tin",
    "cấu trúc dữ liệu": "Công nghệ thông tin",
    "algorithm": "Công nghệ thông tin",
    "data structure": "Công nghệ thông tin",
    "trí tuệ nhân tạo": "Công nghệ thông tin",
    "machine learning": "Công nghệ thông tin",
    "deep learning": "Công nghệ thông tin",
    "an toàn thông tin": "Công nghệ thông tin",
    "bảo mật": "Công nghệ thông tin",
    "an ninh mạng": "Công nghệ thông tin",
    "mạng máy tính": "Công nghệ thông tin",
    "cơ sở dữ liệu": "Công nghệ thông tin",
    "csdl": "Công nghệ thông tin",
    "sql": "Công nghệ thông tin",
    "git": "Công nghệ thông tin",
    "github": "Công nghệ thông tin",
    "quản lý mã nguồn": "Công nghệ thông tin",
    "mã nguồn": "Công nghệ thông tin",
    "cloud": "Công nghệ thông tin",
    "điện toán đám mây": "Công nghệ thông tin",
    "aws": "Công nghệ thông tin",
    "docker": "Công nghệ thông tin",
    "kubernetes": "Công nghệ thông tin",
    "devops": "Công nghệ thông tin",
    "5g": "Công nghệ thông tin",
    "mạng không dây": "Công nghệ thông tin",
    "viễn thông": "Công nghệ thông tin",
    "hệ điều hành": "Công nghệ thông tin",
    "linux": "Công nghệ thông tin",
    "lập trình thi đấu": "Công nghệ thông tin",
    "oop": "Công nghệ thông tin",
    "hướng đối tượng": "Công nghệ thông tin",
    "thiết kế web": "Công nghệ thông tin",
    "phần mềm": "Công nghệ thông tin",
    "vi điều khiển": "Công nghệ thông tin",
    "nhúng": "Công nghệ thông tin",
    "iot": "Công nghệ thông tin",

    # 3. Kinh tế – Kinh doanh
    "kinh tế": "Kinh tế – Kinh doanh",
    "kinh doanh": "Kinh tế – Kinh doanh",
    "marketing": "Kinh tế – Kinh doanh",
    "quản trị": "Kinh tế – Kinh doanh",
    "quản trị kinh doanh": "Kinh tế – Kinh doanh",
    "tài chính": "Kinh tế – Kinh doanh",
    "tài chính cá nhân": "Kinh tế – Kinh doanh",
    "đầu tư": "Kinh tế – Kinh doanh",
    "chứng khoán": "Kinh tế – Kinh doanh",
    "khởi nghiệp": "Kinh tế – Kinh doanh",
    "kế toán": "Kinh tế – Kinh doanh",
    "thương mại điện tử": "Kinh tế – Kinh doanh",
    "bán lẻ": "Kinh tế – Kinh doanh",
    "bán hàng": "Kinh tế – Kinh doanh",
    "thương hiệu": "Kinh tế – Kinh doanh",
    "xây dựng thương hiệu": "Kinh tế – Kinh doanh",
    "kinh tế học": "Kinh tế – Kinh doanh",
    "kinh tế vi mô": "Kinh tế – Kinh doanh",
    "kinh tế vĩ mô": "Kinh tế – Kinh doanh",

    # 4. Kỹ năng sống – Phát triển bản thân
    "kỹ năng sống": "Kỹ năng sống – Phát triển bản thân",
    "phát triển bản thân": "Kỹ năng sống – Phát triển bản thân",
    "quản lý thời gian": "Kỹ năng sống – Phát triển bản thân",
    "thói quen": "Kỹ năng sống – Phát triển bản thân",
    "tư duy phản biện": "Kỹ năng sống – Phát triển bản thân",
    "phản biện": "Kỹ năng sống – Phát triển bản thân",
    "giao tiếp": "Kỹ năng sống – Phát triển bản thân",
    "kỹ năng giao tiếp": "Kỹ năng sống – Phát triển bản thân",
    "thuyết trình": "Kỹ năng sống – Phát triển bản thân",
    "làm việc nhóm": "Kỹ năng sống – Phát triển bản thân",
    "lắng nghe": "Kỹ năng sống – Phát triển bản thân",
    "tự tin": "Kỹ năng sống – Phát triển bản thân",

    # 5. Tâm lý học
    "tâm lý": "Tâm lý học",
    "tâm lý học": "Tâm lý học",
    "hành vi": "Tâm lý học",
    "tâm lý hành vi": "Tâm lý học",
    "thao túng tâm lý": "Tâm lý học",

    # 6. Thiếu nhi
    "thiếu nhi": "Thiếu nhi",
    "truyện tranh": "Thiếu nhi",
    "cổ tích": "Thiếu nhi",
    "đồng thoại": "Thiếu nhi",

    # 7. Lịch sử – Văn hóa
    "lịch sử": "Lịch sử – Văn hóa",
    "văn hóa": "Lịch sử – Văn hóa",
    "chiến tranh": "Lịch sử – Văn hóa",
    "triều đại": "Lịch sử – Văn hóa",

    # 8. Khoa học – Công nghệ
    "khoa học": "Khoa học – Công nghệ",
    "vũ trụ": "Khoa học – Công nghệ",
    "vật lý": "Khoa học – Công nghệ",
    "hóa học": "Khoa học – Công nghệ",

    # 9. Văn học – Tiểu thuyết
    "tiểu thuyết": "Văn học – Tiểu thuyết",
    "truyện ngắn": "Văn học – Tiểu thuyết",
    "tản văn": "Văn học – Tiểu thuyết",
    "thơ ca": "Văn học – Tiểu thuyết"
}

GENERIC_TOPIC_TITLES = {
    "tư duy phản biện", "tư duy giải quyết vấn đề", "giải quyết vấn đề", "kỹ năng làm việc nhóm",
    "làm việc nhóm", "thương hiệu cá nhân", "xây dựng thương hiệu", "phương pháp học tập",
    "nghệ thuật lắng nghe", "lắng nghe", "tự tin", "bản lĩnh", "giao tiếp", "thuyết trình",
    "quản lý thời gian", "quản lý mã nguồn", "giải thuật", "thuật toán", "lập trình c++",
    "lập trình python", "lập trình java", "cơ sở dữ liệu", "mạng máy tính", "an toàn thông tin",
    "thương mại điện tử", "bán lẻ", "bán hàng", "marketing căn bản", "kinh tế học", "tài chính",
    "kinh doanh", "khởi nghiệp", "đầu tư", "đọc hiểu", "tiếng anh", "tiếng trung", "ielts", "toeic",
    "cuộc sống", "tương lai", "hạnh phúc", "bình yên", "thành công", "học tập", "nghệ thuật"
}

# -----------------------------------------------------------------------------
# 2. HÀM CHÍNH: HIỂU VÀ PHÂN TÍCH CÂU HỎI (QUERY UNDERSTANDING)
# -----------------------------------------------------------------------------
class QueryAnalyzer:
    def __init__(self, catalog_df=None):
        self.catalog_df = catalog_df
        self.categories = [
            "Văn học – Tiểu thuyết", "Công nghệ thông tin", "Kinh tế – Kinh doanh",
            "Giáo dục – Ngoại ngữ", "Kỹ năng sống – Phát triển bản thân",
            "Khoa học – Công nghệ", "Thiếu nhi", "Lịch sử – Văn hóa", "Tâm lý học"
        ]
        
        self.valid_authors = []
        self.titles = []
        if catalog_df is not None:
            self._index_catalog(catalog_df)
            
    def _index_catalog(self, df):
        if 'valid_author' in df.columns:
            self.valid_authors = [
                a.strip() for a in df['valid_author'].dropna().unique() 
                if len(a.strip()) > 2
            ]
        elif 'Author' in df.columns:
            self.valid_authors = [
                a.strip() for a in df['Author'].dropna().unique() 
                if len(a.strip()) > 2
            ]
        if 'Title' in df.columns:
            self.titles = [
                t.strip() for t in df['Title'].dropna().unique() 
                if len(t.strip()) > 2
            ]

    def extract_negation(self, query: str) -> tuple:
        """
        Trích xuất các mệnh đề phủ định / loại trừ:
        - Tách các cụm 'không phải X', 'đừng gợi ý X', 'tránh X', 'chứ không phải X'
        - Trả về: (positive_query, avoid_keywords, avoid_categories)
        """
        q = clean_text(query)
        q_lower = q.lower()

        avoid_keywords = []
        avoid_categories = []
        
        # Regex bắt các mệnh đề phủ định phổ biến
        neg_pattern = r'(?:nhưng\s+)?(?:chứ\s+)?(?:không phải|đừng(?: có| gợi ý)?|tránh|không muốn|loại trừ|ghét|chứ đừng)\s+([^,.;!?]+)'
        matches = list(re.finditer(neg_pattern, q_lower))
        
        if not matches:
            return q, avoid_keywords, avoid_categories
            
        positive_query = q_lower
        for m in matches:
            neg_clause = m.group(1).strip()
            # Bổ sung toàn bộ cụm phủ định vào avoid_keywords
            avoid_keywords.append(neg_clause)
            
            # Phân tách sâu các từ khóa độc lập trong mệnh đề phủ định
            words = [w.strip() for w in neg_clause.split() if len(w.strip()) > 1]
            if "ngữ pháp" in neg_clause:
                avoid_keywords.extend(["ngữ pháp", "grammar"])
            if "hàn lâm" in neg_clause or "giáo trình" in neg_clause:
                avoid_keywords.extend(["hàn lâm", "lý thuyết"])
            if "làm giàu" in neg_clause:
                avoid_keywords.extend(["làm giàu", "triệu phú", "lướt sóng", "bí mật làm giàu"])
            if "trinh thám" in neg_clause:
                avoid_keywords.extend(["trinh thám", "án mạng", "phá án"])
            if "kiến trúc xây dựng" in neg_clause or "nhà ở" in neg_clause:
                avoid_keywords.extend(["kiến trúc dân dụng", "kiến trúc xây dựng", "xây dựng"])
            if "kinh dị" in neg_clause or "máu me" in neg_clause or "rùng rợn" in neg_clause:
                avoid_keywords.extend(["kinh dị", "máu me", "rùng rợn"])
            if "arduino" in neg_clause:
                avoid_keywords.append("arduino")
            if "mầm non" in neg_clause or "mẫu giáo" in neg_clause or "cho bé" in neg_clause:
                avoid_keywords.extend(["mầm non", "mẫu giáo", "cho bé", "thiếu nhi"])
                
            # Xóa mệnh đề phủ định khỏi positive_query
            positive_query = positive_query.replace(m.group(0), " ").strip()
            
        # Làm sạch khoảng trắng dư thừa
        positive_query = re.sub(r'\s+', ' ', positive_query).strip()
        return positive_query, avoid_keywords, avoid_categories

    def extract_entities(self, query: str) -> dict:
        q_lower = query.lower()
        q_unaccent = strip_accents(query)
        entities = {}
        
        # 1. Bắt tựa sách trong dấu ngoặc kép (kể cả ngoặc cong và ngoặc đơn)
        quote_match = re.search(r'["“\'\`«]([^"”\'\`»]{2,})["”\'\`»]', query)
        if quote_match:
            quoted_phrase = quote_match.group(1).strip()
            quoted_lower = quoted_phrase.lower()
            quoted_unacc = strip_accents(quoted_phrase)
            entities["quoted_title"] = quoted_phrase
            
            # Kiểm tra xem có trong catalog không
            catalog_match = None
            for t in self.titles:
                t_lower = t.lower()
                t_unacc = strip_accents(t)
                if t_lower == quoted_lower or t_unacc == quoted_unacc:
                    catalog_match = t
                    break
                elif len(quoted_lower) >= 5 and (quoted_lower in t_lower or t_lower in quoted_lower):
                    catalog_match = t
                    break
            if catalog_match:
                entities["title"] = catalog_match
                entities["title_in_catalog"] = True
            else:
                entities["target_title"] = quoted_phrase
                entities["title_in_catalog"] = False

        # 2. Bắt tác giả có trong query
        matched_authors = []
        for a in self.valid_authors:
            a_lower = a.lower()
            a_unacc = strip_accents(a)
            if len(a.split()) == 1:
                pattern_prefix = r'(?:tác giả|viết bởi|sách của|nhà văn)\s+'
                if not re.search(pattern_prefix + re.escape(a_lower), q_lower) and \
                   not re.search(pattern_prefix + re.escape(a_unacc), q_unaccent):
                    continue

            pattern_a_acc = r'(?:^|\b|\s)' + re.escape(a_lower) + r'(?:$|\b|\s)'
            pattern_a_unacc = r'(?:^|\b|\s)' + re.escape(a_unacc) + r'(?:$|\b|\s)'
            if len(a) >= 4 and (re.search(pattern_a_acc, q_lower) or re.search(pattern_a_unacc, q_unaccent)):
                matched_authors.append(a)
        if matched_authors:
            entities["author"] = max(matched_authors, key=len)
        else:
            # Nhận diện tác giả không có trong catalog (vd: Vũ Trọng Phụng, Stephen Hawking, Tô Hoài...)
            author_pfx = re.search(r'(?:của|tác giả|viết bởi|nhà văn)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,3})', query)
            if author_pfx:
                entities["target_author"] = author_pfx.group(1).strip()

        # 3. Tìm tựa sách trong catalog khi không có ngoặc kép
        if not entities.get("title") and not entities.get("target_title"):
            is_exploratory = bool(re.search(
                r'(sách\s+(dạy|về|hướng dẫn|nói về)|học cách|làm thế nào để|cách để|bí quyết|rèn luyện|phương pháp|tài liệu về|muốn học|tài liệu|cách giải tỏa)',
                q_lower
            ))
            if not is_exploratory:
                matched_titles = []
                for t in self.titles:
                    t_lower = t.lower()
                    t_unacc = strip_accents(t)
                    if t_lower in GENERIC_TOPIC_TITLES or t_unacc in GENERIC_TOPIC_TITLES:
                        continue
                    if len(t) >= 5 and (t_lower in q_lower or t_unacc in q_unaccent):
                        matched_titles.append(t)
                if matched_titles:
                    entities["title"] = max(matched_titles, key=len)
                    entities["title_in_catalog"] = True

        # 4. Nhận diện tựa sách theo mẫu cú pháp: tiểu thuyết X, tác phẩm X, cuốn X
        if not entities.get("title") and not entities.get("target_title"):
            title_pfx = re.search(r'(?:tiểu thuyết|tác phẩm|cuốn sách|cuốn|quyển)\s+([A-ZÀ-Ỹ0-9][a-zà-ỹ0-9]+(?:\s+[a-zà-ỹ0-9A-ZÀ-Ỹ]+){0,4})', query)
            if title_pfx:
                cand = title_pfx.group(1).strip()
                if cand.lower() not in ["nào", "gì", "này", "ấy", "về", "dạy", "học", "hay"]:
                    entities["target_title"] = cand
                    entities["title_in_catalog"] = False

        return entities

    def analyze(self, query: str) -> dict:
        q_raw = clean_text(query)
        q_lower = q_raw.lower()
        q_unaccent = strip_accents(q_raw)
        
        # 1. KIỂM TRA OUT OF DOMAIN (NGOÀI PHẠM VI)
        is_book_intent = any(w in q_lower for w in ["sách", "đọc", "tài liệu", "giáo trình", "truyện", "cuốn", "quyển", "tác phẩm", "tác giả", "mượn", "kệ", "thư viện"])
        is_strictly_disallowed = any(re.search(p, q_lower) or re.search(p, q_unaccent) for p in [
            r'thời tiết', r'viết\s*(giúp|hộ|cho).*thơ', r'bài thơ tỏ tình', r'tỏ tình',
            r'tính\s+(\d+|giúp)', r'\d+\s*(?:cộng(?:\s+với)?|\+|\-|nhân(?:\s+với)?|\*|chia(?:\s+cho)?|\/)\s*\d+', r'1\s*\+\s*1', r'bằng\s+bao\s+nhiêu',
            r'ai (đang là|là) tổng thống', r'tổng thống', r'giá vàng', r'màn hình xanh', r'sửa máy tính', r'sửa lỗi.*windows'
        ])

        if (not is_book_intent and any(re.search(p, q_lower) or re.search(p, q_unaccent) for p in OUT_OF_DOMAIN_PATTERNS)) or is_strictly_disallowed:
            return {
                "raw_query": q_raw,
                "normalized_query": q_lower,
                "positive_query": q_lower,
                "intent": "OUT_OF_DOMAIN",
                "confidence": 0.95,
                "explanation": "Câu hỏi nằm ngoài phạm vi tìm kiếm sách và tra cứu thư viện.",
                "filters": {},
                "detected_emotion": "Không có",
                "detected_moods": [],
                "target_moods": [],
                "target_effort": "vừa",
                "preferred_categories": [],
                "avoid_keywords": [],
                "avoid_authors": [],
                "avoid_titles": [],
                "expanded_queries": []
            }

        # 2. TÁCH MỆNH ĐỀ PHỦ ĐỊNH / LOẠI TRỪ (NEGATION EXTRACTION)
        positive_query, avoid_keywords, avoid_categories = self.extract_negation(q_raw)
        pos_lower = positive_query.lower()
        pos_unacc = strip_accents(positive_query)

        # 3. KIỂM TRA LOCATION_STATUS
        is_loc_status = False
        for p in LOCATION_STATUS_PATTERNS:
            if re.search(p, q_lower) or re.search(p, q_unaccent):
                is_loc_status = True
                break

        # 4. TRÍCH XUẤT CÁC THỰC THỂ (ENTITIES)
        filters = {}
        entities = self.extract_entities(q_raw)
        if entities.get("author"):
            filters["author"] = entities["author"]
        if entities.get("target_author"):
            filters["target_author"] = entities["target_author"]
        if entities.get("title"):
            filters["title"] = entities["title"]
        if entities.get("target_title"):
            filters["target_title"] = entities["target_title"]
        if entities.get("quoted_title"):
            filters["quoted_title"] = entities["quoted_title"]

        # Trivia clues
        if any(w in pos_lower for w in ["ông già ngoài biển", "ông lão đánh cá", "ông già và biển"]):
            filters["title"] = "Ông già và biển cả"
        elif any(w in pos_lower for w in ["cậu bé và con cáo", "con cáo và cậu bé"]):
            filters["target_title"] = "Hoàng tử bé"

        # Lọc tình trạng còn hàng
        if any(w in q_lower for w in ["còn sách", "còn hàng", "đang có sẵn", "chưa ai mượn", "sẵn có"]):
            filters["only_available"] = True
            
        # Lọc tầng / kệ
        floor_match = re.search(r'tầng\s*([123])', q_lower)
        if floor_match:
            filters["floor"] = int(floor_match.group(1))
        shelf_match = re.search(r'kệ\s*([abcdefABCDEF])\b', q_raw)
        if shelf_match:
            filters["shelf"] = shelf_match.group(1).upper()

        # Lọc Category rõ ràng từ positive_query
        matched_topic_cat = None
        if not filters.get("title") and not filters.get("target_title"):
            if any(w in pos_lower for w in ["tiếng anh", "tiếng nhật", "tiếng trung", "tiếng hoa", "tiếng hàn", "tiếng pháp", "ielts", "toeic", "hsk", "hán ngữ", "ngoại ngữ"]):
                filters["category"] = "Giáo dục – Ngoại ngữ"
            else:
                for cat in self.categories:
                    if cat.lower() in pos_lower or strip_accents(cat) in pos_unacc:
                        filters["category"] = cat
                        break

            if "category" not in filters:
                sorted_topics = sorted(TOPIC_TO_CATEGORY.keys(), key=len, reverse=True)
                for top_kw in sorted_topics:
                    pattern_acc = r'(?:^|\b|\s)' + re.escape(top_kw) + r'(?:$|\b|\s)'
                    if re.search(pattern_acc, pos_lower):
                        matched_topic_cat = TOPIC_TO_CATEGORY[top_kw]
                        filters["category"] = matched_topic_cat
                        break
                if not matched_topic_cat:
                    for top_kw in sorted_topics:
                        top_unacc = strip_accents(top_kw)
                        pattern_unacc = r'(?:^|\b|\s)' + re.escape(top_unacc) + r'(?:$|\b|\s)'
                        if re.search(pattern_unacc, pos_unacc):
                            matched_topic_cat = TOPIC_TO_CATEGORY[top_kw]
                            filters["category"] = matched_topic_cat
                            break

        # 5. NHẬN DIỆN CẢM XÚC TRÊN POSITIVE_QUERY (KHÔNG BỊ ẢNH HƯỞNG BỞI CỤM PHỦ ĐỊNH)
        matched_emotions = []
        for emo_id, data in EMOTIONAL_PATTERNS.items():
            for kw in data["keywords"]:
                kw_unacc = strip_accents(kw)
                # Chỉ kiểm tra trên positive_query để tránh bẫy phủ định
                if kw in pos_lower or kw_unacc in pos_unacc:
                    matched_emotions.append((emo_id, data))
                    break

        # 6. XÁC ĐỊNH INTENT THEO THỨ TỰ ƯU TIÊN CHUẨN
        has_specific_book_target = bool(
            filters.get("quoted_title") or 
            filters.get("title") or 
            filters.get("target_title") or 
            filters.get("author") or 
            filters.get("target_author")
        )

        detected_emotion = "Không có"
        detected_moods = []

        if is_loc_status:
            intent = "LOCATION_STATUS"
            book_target = filters.get("title") or filters.get("target_title") or filters.get("quoted_title") or ""
            if book_target:
                explanation = f"Người dùng hỏi vị trí và tình trạng còn/hết của cuốn '{book_target}' trên kệ."
            else:
                explanation = "Người dùng hỏi về vị trí hoặc tình trạng còn/hết của sách trên kệ."

        elif has_specific_book_target:
            # ƯU TIÊN 1 CHO EXACT_BOOK: Khi người dùng nêu tên sách cụ thể hoặc tác giả,
            # luôn ưu tiên EXACT_BOOK kể cả khi trong câu có từ ngữ cảm xúc
            intent = "EXACT_BOOK"
            explanation = "Người dùng tìm kiếm đích danh tên sách hoặc tác giả cụ thể."

        elif matched_emotions:
            intent = "EMOTIONAL_CONTEXT"
            primary_emo = matched_emotions[0]
            detected_emotion = primary_emo[1].get("display_name", "Cảm xúc")
            detected_moods = primary_emo[1].get("target_moods", [])
            explanation = f"Người dùng tìm sách theo cảm xúc: {detected_emotion}."

        elif filters.get("category") or matched_topic_cat or any(w in pos_lower for w in ["giáo trình", "học lập trình", "kinh tế vi mô", "lịch sử", "ielts", "toán học", "cơ sở dữ liệu", "an toàn thông tin", "mạng máy tính"]):
            intent = "CATEGORY_TOPIC"
            explanation = "Người dùng tìm sách theo chủ đề chuyên môn hoặc lĩnh vực cụ thể."

        else:
            intent = "EXACT_BOOK"
            explanation = "Tìm kiếm theo từ khóa tên sách hoặc thông tin cụ thể."

        # 7. TỔNG HỢP MỤC TIÊU VÀ TRUY VẤN MỞ RỘNG
        target_moods = []
        expanded_queries = []
        preferred_cats = []
        target_effort = "vừa"
        target_audience = None

        if intent == "EMOTIONAL_CONTEXT":
            for emo_id, data in matched_emotions:
                if data.get("audience"):
                    target_audience = data["audience"]
                for m in data.get("target_moods", []):
                    if m not in target_moods:
                        target_moods.append(m)
                for ak in data.get("avoid_keywords", []):
                    if ak not in avoid_keywords:
                        avoid_keywords.append(ak)
                for eq in data.get("expanded_queries", []):
                    if eq not in expanded_queries:
                        expanded_queries.append(eq)
                for pc in data.get("preferred_categories", []):
                    if pc not in preferred_cats:
                        preferred_cats.append(pc)
                target_effort = data.get("reading_effort", target_effort)

        if not expanded_queries:
            expanded_queries = [positive_query]

        # Phân lập ngôn ngữ ngoại ngữ
        target_lang = None
        avoid_langs = []
        if any(w in pos_lower for w in ["tiếng anh", "english", "ielts", "toeic"]):
            target_lang = "tiếng anh"
            avoid_langs = ["tiếng trung", "tiếng hoa", "hsk", "hán ngữ", "tiếng hàn", "topik", "tiếng nhật", "jlpt"]
        elif any(w in pos_lower for w in ["tiếng trung", "tiếng hoa", "hsk", "hán ngữ"]):
            target_lang = "tiếng trung"
            avoid_langs = ["tiếng anh", "english", "ielts", "toeic", "tiếng hàn", "tiếng nhật"]

        return {
            "raw_query": q_raw,
            "normalized_query": q_lower,
            "positive_query": positive_query,
            "intent": intent,
            "explanation": explanation,
            "filters": filters,
            "detected_emotion": detected_emotion,
            "detected_moods": detected_moods or target_moods,
            "target_moods": target_moods,
            "target_effort": target_effort,
            "audience": target_audience,
            "preferred_categories": preferred_cats,
            "avoid_keywords": avoid_keywords,
            "avoid_authors": [],
            "avoid_titles": [],
            "target_language": target_lang,
            "avoid_languages": avoid_langs,
            "expanded_queries": expanded_queries[:4]
        }
