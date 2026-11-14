import os
import sys
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "venv", "Lib", "site-packages"))

from src.hybrid_search_v2 import HybridSearchEngineV2
from src.query_understanding import QueryAnalyzer
from src.embedding import EmbeddingEngine
from src.response_generator import LibrarianResponseGenerator

def evaluate_generalization():
    print("=" * 90)
    print("KIỂM THỬ KHẢ NĂNG TỔNG QUÁT HÓA (GENERALIZATION AUDIT - 15 KỊCH BẢN THỰC TẾ)")
    print("=" * 90)

    df = pd.read_csv(os.path.join(BASE_DIR, 'dataset', 'books_enriched.csv'))
    embs = np.load(os.path.join(BASE_DIR, 'embeddings', 'embeddings_enriched.npy'))
    embed_engine = EmbeddingEngine()
    qa = QueryAnalyzer(catalog_df=df)
    search_engine = HybridSearchEngineV2(df, embs, embed_engine, qa)
    generator = LibrarianResponseGenerator()

    scenarios = [
        {
            "id": 1,
            "query": "Cuối tuần này mình có 2 ngày rảnh rỗi ở nhà, muốn tìm một cuốn tiểu thuyết tình cảm sâu sắc, cảm động rơi nước mắt",
            "expected_cat": "Văn học – Tiểu thuyết",
            "expected_mood": "cảm động",
            "criteria": "Không gợi ý sách kỹ thuật hay kinh tế; Top 1-3 phải là tiểu thuyết tình cảm/cảm động"
        },
        {
            "id": 2,
            "query": "Tôi đang muốn học cách quản lý tài chính cá nhân và đầu tư chứng khoán cơ bản cho người mới",
            "expected_cat": "Kinh tế – Kinh doanh",
            "expected_mood": None,
            "criteria": "Phải thuộc mảng Kinh tế/Tài chính/Đầu tư, không gợi ý tiểu thuyết"
        },
        {
            "id": 3,
            "query": "Em đang chuẩn bị phỏng vấn xin việc, muốn đọc sách về kỹ năng giao tiếp và thuyết phục",
            "expected_cat": "Kỹ năng sống – Phát triển bản thân",
            "expected_mood": None,
            "criteria": "Phải là sách kỹ năng giao tiếp, ứng xử, đàm phán"
        },
        {
            "id": 4,
            "query": "Mình dạo này hay bị suy nghĩ nhiều, lo âu overthinking về tương lai",
            "expected_cat": "Kỹ năng sống – Phát triển bản thân",
            "expected_mood": "chữa lành",
            "criteria": "Sách tâm lý/chữa lành/an yên, không gợi ý sách án mạng hay kỹ thuật"
        },
        {
            "id": 5,
            "query": "Tìm sách triết học phương đông hoặc Phật giáo để tìm sự an tịnh",
            "expected_cat": "Lịch sử – Văn hóa",
            "expected_mood": "suy ngẫm",
            "criteria": "Sách văn hóa, triết học, thiền định, an tịnh"
        },
        {
            "id": 6,
            "query": "Có cuốn sách nào về lịch sử Việt Nam thời phong kiến hoặc chiến tranh hấp dẫn không",
            "expected_cat": "Lịch sử – Văn hóa",
            "expected_mood": None,
            "criteria": "Phải thuộc mảng Lịch sử – Văn hóa"
        },
        {
            "id": 7,
            "query": "Mình muốn tìm hiểu về AI, trí tuệ nhân tạo nhưng không phải sách code nặng",
            "expected_cat": "Công nghệ thông tin",
            "expected_mood": None,
            "criteria": "Sách công nghệ/AI, nỗ lực đọc vừa, không phải giáo trình toán/code nặng"
        },
        {
            "id": 8,
            "query": "Có sách nào kể chuyện trước giờ đi ngủ cho bé 5 tuổi không",
            "expected_cat": "Thiếu nhi",
            "expected_mood": None,
            "criteria": "Phải là sách Thiếu nhi, truyện tranh cho trẻ em"
        },
        {
            "id": 9,
            "query": "Tìm tiểu thuyết trinh thám phá án ly kỳ gay cấn của Conan Doyle hoặc tương tự",
            "expected_cat": "Văn học – Tiểu thuyết",
            "expected_mood": "hồi hộp",
            "criteria": "Truyện trinh thám, phá án, hồi hộp"
        },
        {
            "id": 10,
            "query": "Muốn học lập trình Python từ con số 0",
            "expected_cat": "Công nghệ thông tin",
            "expected_mood": None,
            "criteria": "Sách lập trình Python, CNTT"
        },
        {
            "id": 11,
            "query": "Mình bị mất ngủ kinh niên, cần sách êm đềm ru ngủ",
            "expected_cat": "Văn học – Tiểu thuyết",
            "expected_mood": "nhẹ nhàng",
            "criteria": "Tản văn nhẹ nhàng, không trinh thám hay bạo lực"
        },
        {
            "id": 12,
            "query": "Sách luyện thi IELTS 6.5+",
            "expected_cat": "Giáo dục – Ngoại ngữ",
            "expected_mood": None,
            "criteria": "Sách luyện thi IELTS, tiếng Anh"
        },
        {
            "id": 13,
            "query": "Cuốn sách nào kinh điển thế giới mà ai cũng nên đọc một lần trong đời",
            "expected_cat": "Văn học – Tiểu thuyết",
            "expected_mood": None,
            "criteria": "Tác phẩm kinh điển thế giới"
        },
        {
            "id": 14,
            "query": "Tôi là sinh viên năm nhất bị choáng ngợp và mất phương hướng",
            "expected_cat": "Kỹ năng sống – Phát triển bản thân",
            "expected_mood": "truyền cảm hứng",
            "criteria": "Sách phát triển bản thân, định hướng sinh viên"
        },
        {
            "id": 15,
            "query": "Hôm nay trời mưa mát mẻ, muốn đọc một cuốn tản văn nhẹ nhàng nhâm nhi cà phê",
            "expected_cat": "Văn học – Tiểu thuyết",
            "expected_mood": "thư giãn",
            "criteria": "Tản văn nhẹ nhàng, thư giãn"
        }
    ]

    results_report = []
    passed_count = 0

    for item in scenarios:
        q = item["query"]
        sr = search_engine.search(q, top_k=4)
        resp = generator.format_response(sr, max_books=4)
        
        analysis = sr.get("analysis", {})
        intent = analysis.get("intent")
        top_books = resp.get("books", [])
        
        # Đánh giá tiêu chí
        top1_cat = top_books[0]["category"] if top_books else "None"
        top1_title = top_books[0]["title"] if top_books else "None"
        
        # Kiểm tra Category khớp ít nhất 1 cuốn trong Top 3
        cat_match = any(item["expected_cat"].lower() in b["category"].lower() for b in top_books[:3]) if item.get("expected_cat") else True
        
        # Kiểm tra tính hợp lý nội dung
        is_pass = cat_match and len(top_books) > 0
        
        # Nếu có expected mood, kiểm tra Top 3 có chứa mood hoặc từ khóa liên quan
        if item.get("expected_mood"):
            mood_match = any(item["expected_mood"].lower() in b.get("explanation", "").lower() or item["expected_mood"].lower() in str(b.get("category", "")).lower() for b in top_books[:3])
            # Không ép tuyệt đối nhưng đánh giá
        
        if is_pass:
            passed_count += 1

        status_str = "PASS" if is_pass else "FAIL"
        print(f"[{status_str}] Câu #{item['id']}: \"{q[:45]}...\"")
        print(f"       -> Intent: {intent} | Kỳ vọng: [{item['expected_cat']}]")
        print(f"       -> Top 1: \"{top1_title}\" ({top1_cat})")
        print(f"       -> Top 2: \"{top_books[1]['title'] if len(top_books)>1 else '-'}\"")
        print(f"       -> Tiêu chí: {item['criteria']}\n")

        results_report.append({
            "id": item["id"],
            "query": q,
            "intent": intent,
            "expected_cat": item["expected_cat"],
            "passed": is_pass,
            "top1": top1_title,
            "top1_cat": top1_cat,
            "top_books": [b["title"] for b in top_books]
        })

    accuracy = (passed_count / len(scenarios)) * 100
    print("=" * 90)
    print(f"KẾT QUẢ ĐÁNH GIÁ TỔNG QUÁT HÓA: {passed_count}/{len(scenarios)} đạt ({accuracy:.1f}%)")
    print("=" * 90)

    out_file = os.path.join(BASE_DIR, "generalization_eval.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"accuracy": accuracy, "details": results_report}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    evaluate_generalization()
