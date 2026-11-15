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

def test_librarian():
    print("=" * 80)
    print("KIỂM THỬ BƯỚC 4: THỦ THƯ AI TRẢ LỜI ĐỘC GIẢ (RESPONSE GENERATOR)")
    print("=" * 80)

    df = pd.read_csv(os.path.join(BASE_DIR, 'dataset', 'books_enriched.csv'))
    embs = np.load(os.path.join(BASE_DIR, 'embeddings', 'embeddings_enriched.npy'))
    embed_engine = EmbeddingEngine()
    qa = QueryAnalyzer(catalog_df=df)
    search_engine = HybridSearchEngineV2(df, embs, embed_engine, qa)
    generator = LibrarianResponseGenerator()

    test_queries = [
        "nay tôi tâm trạng không tốt, tôi cần 1 cuốn truyện hài",
        "Hôm nay tôi đang rất mệt, tôi muốn có cuốn sách giúp tôi thư giãn",
        "tiếng anh",
        "Người Đàn Ông Mang Tên Ove",
        "hôm nay ăn gì ở căng tin"
    ]

    all_outputs = {}

    for i, q in enumerate(test_queries, 1):
        print("\n" + "=" * 80)
        print(f"TEST CASE {i}: ĐỘC GIẢ HỎI: \"{q}\"")
        print("=" * 80)

        # Chạy Search Engine V2
        search_res = search_engine.search(q, top_k=4)
        
        # Chạy Response Generator V2
        response_data = generator.format_response(search_res, max_books=4)
        
        print("\n--- PHẢN HỒI THỦ THƯ AI (RENDERED UI) ---")
        print(response_data["rendered_markdown"])
        print("-" * 80)
        
        all_outputs[q] = response_data

    out_file = os.path.join(BASE_DIR, "step4_librarian_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_outputs, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Đã lưu kết quả Bước 4 vào: {out_file}")

if __name__ == "__main__":
    test_librarian()
