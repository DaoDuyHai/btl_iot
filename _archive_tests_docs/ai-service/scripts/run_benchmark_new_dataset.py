import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

def main():
    print("=" * 70)
    print("BENCHMARK SUITE FOR NEW DATASET (3,000 REAL BOOKS)")
    print("Senior AI Engineer Implementation")
    print("=" * 70)

    dataset_path = "dataset/cleaned_books_dataset.csv"
    df = load_and_verify_dataset(dataset_path)
    work_mapping = get_work_catalog(df)
    
    emb_engine = EmbeddingEngine(cache_dir="embeddings")
    embeddings, book_ids = emb_engine.get_or_build_embeddings(df)
    
    bm25 = BM25SearchEngine(df, work_mapping)
    semantic = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
    hybrid = HybridSearchEngine(bm25, semantic, k=60)

    # Curate realistic test queries mapped to expected targets in the 3000 books
    test_cases = [
        # G01: Tên sách chính xác
        {"id": "TC001", "group": "Exact_Title", "query": "Người Đàn Ông Mang Tên Ove", "expected_title": "Người Đàn Ông Mang Tên Ove"},
        {"id": "TC002", "group": "Exact_Title", "query": "Trăm năm cô đơn", "expected_title": "Trăm năm cô đơn"},
        {"id": "TC003", "group": "Exact_Title", "query": "Nhà Giả Kim", "expected_title": "Nhà Giả Kim"},
        {"id": "TC004", "group": "Exact_Title", "query": "Cây Cam Ngọt Của Tôi", "expected_title": "Cây Cam Ngọt Của Tôi"},
        {"id": "TC005", "group": "Exact_Title", "query": "Mắt Biếc", "expected_title": "Mắt Biếc"},
        {"id": "TC006", "group": "Exact_Title", "query": "Nỗi buồn chiến tranh", "expected_title": "Nỗi buồn chiến tranh"},
        {"id": "TC007", "group": "Exact_Title", "query": "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông", "expected_title": "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông"},
        {"id": "TC008", "group": "Exact_Title", "query": "Không Gia Đình", "expected_title": "Không Gia Đình"},
        {"id": "TC009", "group": "Exact_Title", "query": "Totto - Chan Bên Cửa Sổ", "expected_title": "Totto - Chan Bên Cửa Sổ"},
        {"id": "TC010", "group": "Exact_Title", "query": "Thiên Tài Bên Trái, Kẻ Điên Bên Phải", "expected_title": "Thiên Tài Bên Trái, Kẻ Điên Bên Phải"},
        
        # G02: Tác giả
        {"id": "TC011", "group": "Author", "query": "Nguyễn Nhật Ánh", "expected_author": "Nguyễn Nhật Ánh"},
        {"id": "TC012", "group": "Author", "query": "Fredrik Backman", "expected_author": "Fredrik Backman"},
        {"id": "TC013", "group": "Author", "query": "Agatha Christie", "expected_author": "Agatha Christie"},
        {"id": "TC014", "group": "Author", "query": "Stephen Hawking", "expected_author": "Stephen Hawking"},
        {"id": "TC015", "group": "Author", "query": "Paulo Coelho", "expected_author": "Paulo Coelho"},

        # G03: Tìm kiếm ngữ nghĩa / cốt truyện / chủ đề (Semantic)
        {"id": "TC016", "group": "Semantic", "query": "sách kể về nỗi đau chiến tranh của người cựu binh", "expected_title": "Nỗi buồn chiến tranh"},
        {"id": "TC017", "group": "Semantic", "query": "chàng chăn cừu đi tìm kho báu dưới chân kim tự tháp", "expected_title": "Nhà Giả Kim"},
        {"id": "TC018", "group": "Semantic", "query": "vụ ám sát bí ẩn trên toa tàu hỏa xuyên châu âu và thám tử poirot", "expected_title": "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông"},
        {"id": "TC019", "group": "Semantic", "query": "cậu bé mồ côi đi lang thang khắp nước pháp cùng đoàn xiếc bác vitalis", "expected_title": "Không Gia Đình"},
        {"id": "TC020", "group": "Semantic", "query": "ngôi trường độc đáo trên toa xe điện và cô bé hiếu động", "expected_title": "Totto - Chan Bên Cửa Sổ"},
        {"id": "TC021", "group": "Semantic", "query": "cuộc trò chuyện với các bệnh nhân tâm thần khám phá góc nhìn khác biệt", "expected_title": "Thiên Tài Bên Trái, Kẻ Điên Bên Phải"},
        {"id": "TC022", "group": "Semantic", "query": "cách quản lý tài chính cá nhân không có tiền vẫn tạo ra tiền cha giàu cha nghèo", "expected_kw": "Dạy Con Làm Giàu"},
        {"id": "TC023", "group": "Semantic", "query": "sách học lập trình trí tuệ nhân tạo và học máy cơ bản", "expected_kw": "Trí Tuệ Nhân Tạo"},
        {"id": "TC024", "group": "Semantic", "query": "tâm lý học hành vi và phân tích tiềm thức con người", "expected_kw": "tiềm thức"},
        {"id": "TC025", "group": "Semantic", "query": "giáo trình học tiếng trung hsk", "expected_kw": "HSK"},

        # G04: Không dấu (Unaccented)
        {"id": "TC026", "group": "Unaccented", "query": "mat biec nguyen nhat anh", "expected_title": "Mắt Biếc"},
        {"id": "TC027", "group": "Unaccented", "query": "cay cam ngot cua toi", "expected_title": "Cây Cam Ngọt Của Tôi"},
        {"id": "TC028", "group": "Unaccented", "query": "nha gia kim paulo coelho", "expected_title": "Nhà Giả Kim"},
        {"id": "TC029", "group": "Unaccented", "query": "an mang tren chuyen tau toc hanh phuong dong", "expected_title": "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông"},
        {"id": "TC030", "group": "Unaccented", "query": "khong gia dinh hector malot", "expected_title": "Không Gia Đình"}
    ]

    print(f"[*] Chạy benchmark trên {len(test_cases)} kịch bản thử nghiệm...")
    results = []
    
    modes = ['bm25', 'semantic', 'hybrid']
    metrics = {m: {'hit@1': 0, 'hit@3': 0, 'hit@5': 0, 'rr': 0.0, 'latencies': []} for m in modes}

    for tc in test_cases:
        qid = tc['id']
        query = tc['query']
        group = tc['group']
        
        tc_res = {
            "test_id": qid,
            "group": group,
            "query": query,
            "modes": {}
        }
        
        for m in modes:
            engine = bm25 if m == 'bm25' else (semantic if m == 'semantic' else hybrid)
            t0 = time.time()
            top_results = engine.search(query, top_k=5)
            lat = (time.time() - t0) * 1000
            metrics[m]['latencies'].append(lat)
            
            # Check relevancy
            rank_found = 0
            for r in top_results:
                matched = False
                if 'expected_title' in tc:
                    if tc['expected_title'].lower() in r['title'].lower():
                        matched = True
                elif 'expected_author' in tc:
                    if tc['expected_author'].lower() in r['author'].lower():
                        matched = True
                elif 'expected_kw' in tc:
                    if tc['expected_kw'].lower() in (r['title'] + " " + r['description']).lower():
                        matched = True
                if matched:
                    rank_found = r['rank']
                    break
                    
            if rank_found == 1:
                metrics[m]['hit@1'] += 1
            if 1 <= rank_found <= 3:
                metrics[m]['hit@3'] += 1
            if 1 <= rank_found <= 5:
                metrics[m]['hit@5'] += 1
            if rank_found > 0:
                metrics[m]['rr'] += 1.0 / rank_found

            tc_res['modes'][m] = {
                "rank_found": rank_found,
                "latency_ms": round(lat, 2),
                "top_results": [
                    {
                        "rank": r['rank'],
                        "title": r['title'],
                        "author": r['author'],
                        "score": round(float(r['score']), 4),
                        "position": r['position']
                    } for r in top_results
                ]
            }
        results.append(tc_res)

    # Compute final metrics
    n = len(test_cases)
    summary = {}
    for m in modes:
        summary[m] = {
            "Hit@1": round(metrics[m]['hit@1'] / n, 4),
            "Hit@3": round(metrics[m]['hit@3'] / n, 4),
            "Hit@5": round(metrics[m]['hit@5'] / n, 4),
            "MRR": round(metrics[m]['rr'] / n, 4),
            "Avg_Latency_ms": round(float(np.mean(metrics[m]['latencies'])), 2),
            "P95_Latency_ms": round(float(np.percentile(metrics[m]['latencies'], 95)), 2)
        }

    # Save to tests/ directory
    os.makedirs("tests", exist_ok=True)
    with open("tests/results_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    with open("tests/metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    pd.DataFrame(test_cases).to_csv("tests/benchmark_test_queries.csv", index=False, encoding="utf-8-sig")

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY RESULTS ON CLEANED 3,000 DATASET:")
    print("=" * 70)
    print(pd.DataFrame(summary).T.to_string())
    print("\n[+] Đã cập nhật tests/results_raw.json và tests/metrics.json chuẩn xác!")

if __name__ == '__main__':
    main()
