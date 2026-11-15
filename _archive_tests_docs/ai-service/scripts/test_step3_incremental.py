import os
import sys
import json
import time
import pandas as pd
import numpy as np

# Thêm ai-service vào sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

venv_site = os.path.join(BASE_DIR, "venv", "Lib", "site-packages")
if os.path.exists(venv_site) and venv_site not in sys.path:
    # Append to the end to prioritize working global torch
    sys.path.append(venv_site)

from src.hybrid_search_v2 import HybridSearchEngineV2
from src.query_understanding import QueryAnalyzer
from src.embedding import EmbeddingEngine

def run_tests():
    print("=" * 80)
    print("KIỂM THỬ TỪNG BƯỚC HYBRID SEARCH ENGINE V2 (BƯỚC 3)")
    print("=" * 80)
    
    # 1. Tải dữ liệu
    dataset_path = os.path.join(BASE_DIR, "dataset", "books_enriched.csv")
    emb_path = os.path.join(BASE_DIR, "embeddings", "embeddings_enriched.npy")
    
    print(f"[*] Đọc dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    print(f"[*] Đọc embeddings: {emb_path}")
    embeddings = np.load(emb_path)
    
    print(f"[*] Khởi tạo EmbeddingEngine và QueryAnalyzer...")
    embed_engine = EmbeddingEngine()
    query_analyzer = QueryAnalyzer(catalog_df=df)
    
    print(f"[*] Khởi tạo HybridSearchEngineV2...")
    engine = HybridSearchEngineV2(
        df=df,
        embeddings=embeddings,
        embedding_engine=embed_engine,
        query_analyzer=query_analyzer,
        k=60
    )
    
    test_queries = [
        # 1. Câu hỏi do User đặt trực tiếp:
        "giờ tôi đang rất buồn, tôi cần 1 cuốn sách giúp tôi giải trí vui vẻ hơn",
        
        # 2. Câu kinh điển trong final.md:
        "Hôm nay tôi đang rất mệt, tôi muốn có cuốn sách giúp tôi thư giãn",
        
        # 3. Câu trong ảnh chụp màn hình kiosk bị lỗi cũ:
        "tiếng anh",
        "tiếng nhật",
        
        # 4. Câu cụ thể tên sách:
        "Người Đàn Ông Mang Tên Ove",
        
        # 5. Câu có phủ định rõ ràng:
        "Tôi muốn đọc gì đó thư giãn nhưng đừng gợi ý sách kinh tế hay kỹ thuật"
    ]
    
    all_results = {}
    
    for i, q in enumerate(test_queries, 1):
        print("\n" + "-" * 80)
        print(f"TEST CASE {i}: '{q}'")
        print("-" * 80)
        
        t0 = time.time()
        res = engine.search(q, top_k=5)
        latency = (time.time() - t0) * 1000
        
        intent = res["analysis"]["intent"]
        moods = res["analysis"]["target_moods"]
        avoid = res["analysis"]["avoid_keywords"]
        expanded = res["analysis"].get("expanded_queries", [])
        
        print(f"-> Phân tích: Intent={intent} | Moods={moods} | Tránh={avoid}")
        if expanded:
            print(f"-> Truy vấn mở rộng: {expanded}")
        print(f"-> Thời gian tìm kiếm: {latency:.1f}ms\n")
        print(f"{'Top':<4} | {'Book_ID':<8} | {'Điểm':<7} | {'Kệ/Tầng':<10} | {'Còn':<4} | {'Tựa sách (Tác giả) / Thể loại'}")
        print("-" * 80)
        
        case_items = []
        for rank, b in enumerate(res["results"], 1):
            pos_info = f"T{b['floor']}-{b['shelf']}:{b['position']}"
            author_display = b['author'] if b['author'] else "Nhiều tác giả"
            line_str = f"#{rank:<3} | {b['book_id']:<8} | {b['score']:<7.4f} | {pos_info:<10} | {b['available_copies']:<4} | {b['title']} ({author_display}) [{b['category']} - {b['subcategory']}]"
            print(line_str)
            print(f"      -> Mood: [{b['mood_tags']}] | Effort: [{b['reading_effort']}]")
            print(f"      -> Lý do: {b['match_reason']}")
            print(f"      -> Trích dẫn: {b['description'][:100]}...\n")
            
            case_items.append({
                "rank": rank,
                "book_id": b["book_id"],
                "title": b["title"],
                "author": b["author"],
                "category": b["category"],
                "subcategory": b["subcategory"],
                "mood_tags": b["mood_tags"],
                "reading_effort": b["reading_effort"],
                "score": b["score"],
                "floor": b["floor"],
                "shelf": b["shelf"],
                "position": b["position"],
                "available_copies": b["available_copies"],
                "match_reason": b["match_reason"]
            })
            
        all_results[q] = {
            "intent": intent,
            "latency_ms": latency,
            "results": case_items
        }
        
    out_file = os.path.join(BASE_DIR, "step3_test_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Đã lưu toàn bộ kết quả kiểm thử vào: {out_file}")

if __name__ == "__main__":
    run_tests()
