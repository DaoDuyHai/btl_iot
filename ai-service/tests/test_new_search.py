import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

def main():
    print("=" * 70)
    print("TESTING SMART LIBRARY KIOSK SEARCH ON CLEANED DATASET (3,000 BOOKS)")
    print("=" * 70)

    dataset_path = "dataset/cleaned_books_dataset.csv"
    df = load_and_verify_dataset(dataset_path)
    work_mapping = get_work_catalog(df)
    print(f"Total Works: {len(work_mapping)}")

    emb_engine = EmbeddingEngine(cache_dir="embeddings")
    embeddings, book_ids = emb_engine.get_or_build_embeddings(df)
    
    bm25_engine = BM25SearchEngine(df, work_mapping)
    semantic_engine = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
    hybrid_engine = HybridSearchEngine(bm25_engine, semantic_engine, k=60)

    test_queries = [
        # 1. Exact title
        ("Mắt Biếc", "Exact Title"),
        ("Sapiens: Lược sử loài người", "Exact Title"),
        ("Người Đàn Ông Mang Tên Ove", "Exact Title"),
        
        # 2. Author lookup
        ("Nguyễn Nhật Ánh", "Author Search"),
        ("Fredrik Backman", "Author Search"),
        ("Agatha Christie", "Author Search"),
        
        # 3. Pure Semantic / Concept query (without book title words)
        ("sách về nỗi đau chiến tranh và người lính trở về", "Pure Semantic"),
        ("hành trình chăn cừu đi tìm kho báu ở kim tự tháp ai cập", "Pure Semantic"),
        ("vụ án giết người bí ẩn trên chuyến tàu hỏa xuyên châu âu", "Pure Semantic"),
        ("tâm lý học phân tích giấc mơ và vô thức", "Pure Semantic"),
        ("lập trình trí tuệ nhân tạo và học máy bằng python", "Pure Semantic"),
        ("dạy con quản lý tài chính và tự do tiền bạc", "Pure Semantic"),
        
        # 4. Unaccented query
        ("cay cam ngot cua toi", "Unaccented"),
        ("nha gia kim", "Unaccented"),
        ("toi thay hoa vang tren co xanh", "Unaccented")
    ]

    print("\n" + "=" * 70)
    print("RUNNING BENCHMARK EVALUATION ACROSS SEARCH MODES")
    print("=" * 70)

    for q, qtype in test_queries:
        print(f"\n[QUERY] '{q}' ({qtype})")
        print("-" * 50)
        
        t0 = time.time()
        hyb_results = hybrid_engine.search(q, top_k=3)
        hyb_lat = (time.time() - t0) * 1000

        print(f"  Hybrid RRF Top 3 ({hyb_lat:.1f}ms):")
        for r in hyb_results:
            copies_str = f"Kệ {r['copies'][0]['shelf']}, Tầng {r['copies'][0]['floor']}, Vị trí {r['copies'][0]['position']}" if r['copies'] else "N/A"
            print(f"    #{r['rank']} [Score: {r['score']:.4f}] {r['title']} - {r['author']} ({r['category']})")
            print(f"       -> {copies_str}")

if __name__ == '__main__':
    main()
