import sys
import os
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine, tokenize_vietnamese, tokenize_query_optimized, QUERY_STOPWORDS
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog, strip_accents

print("[*] Bắt đầu kiểm thử Khả năng truy vết & Giải thích kết quả (Hạng mục G)...")

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
work_mapping = get_work_catalog(df)

embedding_engine = EmbeddingEngine()
embeddings, book_ids = embedding_engine.get_or_build_embeddings(df)

bm25_engine = BM25SearchEngine(df, work_mapping=work_mapping)
semantic_engine = SemanticSearchEngine(df, embedding_engine, embeddings, book_ids, work_mapping=work_mapping)
hybrid_engine = HybridSearchEngine(bm25_engine, semantic_engine, k=60)

class ExplainableSearchTracer:
    """Module truy vết và giải thích chi tiết cơ chế xếp hạng của từng kết quả."""
    def __init__(self, bm25_engine: BM25SearchEngine, semantic_engine: SemanticSearchEngine, k: int = 60):
        self.bm25 = bm25_engine
        self.semantic = semantic_engine
        self.k = k
        self.work_mapping = semantic_engine.work_mapping
        
    def trace_query(self, query: str, top_k: int = 5, fetch_k: int = 200) -> dict:
        # 1. Trích xuất token và stopwords
        raw_tokens = tokenize_vietnamese(query)
        unacc_query = strip_accents(query)
        unacc_tokens = tokenize_vietnamese(unacc_query)
        
        filtered_tokens = [t for t in raw_tokens if t not in QUERY_STOPWORDS]
        removed_stopwords = [t for t in raw_tokens if t in QUERY_STOPWORDS]
        
        # 2. Chạy BM25
        bm25_raw = self.bm25.search(query, top_k=fetch_k)
        bm25_lookup = {r['work_id']: {"rank": r['rank'], "score": r['score']} for r in bm25_raw}
        
        # 3. Chạy Semantic
        sem_raw = self.semantic.search(query, top_k=fetch_k)
        sem_lookup = {r['work_id']: {"rank": r['rank'], "score": r['score']} for r in sem_raw}
        
        # 4. RRF Merge
        all_wids = set(bm25_lookup.keys()) | set(sem_lookup.keys())
        rrf_scored = []
        for wid in all_wids:
            bm_info = bm25_lookup.get(wid, {"rank": None, "score": 0.0})
            sem_info = sem_lookup.get(wid, {"rank": None, "score": 0.0})
            
            bm_rrf_component = (1.0 / (self.k + bm_info['rank'])) if bm_info['rank'] else 0.0
            sem_rrf_component = (1.0 / (self.k + sem_info['rank'])) if sem_info['rank'] else 0.0
            total_rrf = bm_rrf_component + sem_rrf_component
            
            w_meta = self.work_mapping[wid]
            first_copy = w_meta['copies'][0] if w_meta['copies'] else {}
            
            # Giải thích vì sao xếp ở hạng này
            if bm_info['rank'] and sem_info['rank']:
                reason = f"Cộng hưởng từ vựng (#BM25: {bm_info['rank']}) và ngữ nghĩa (#Semantic: {sem_info['rank']})"
            elif bm_info['rank']:
                reason = f"Trúng từ khóa chính xác (#BM25: {bm_info['rank']}), Semantic ngoài Top {fetch_k}"
            else:
                reason = f"Trúng tương đồng ngữ nghĩa (#Semantic: {sem_info['rank']}), BM25 điểm 0 (không trùng chữ)"
                
            rrf_scored.append({
                "work_id": wid,
                "book_id": first_copy.get('book_id', wid),
                "title": w_meta['base_title'],
                "author": w_meta['author'],
                "category": w_meta['category'],
                "bm25_score": round(float(bm_info['score']), 4),
                "bm25_rank": bm_info['rank'],
                "bm25_rrf_contrib": round(bm_rrf_component, 6),
                "semantic_score": round(float(sem_info['score']), 4),
                "semantic_rank": sem_info['rank'],
                "semantic_rrf_contrib": round(sem_rrf_component, 6),
                "rrf_total_score": round(total_rrf, 6),
                "explanation": reason
            })
            
        rrf_scored.sort(key=lambda x: x['rrf_total_score'], reverse=True)
        for rank, item in enumerate(rrf_scored[:top_k], 1):
            item['rrf_final_rank'] = rank
            
        return {
            "query_original": query,
            "query_normalized_unaccented": unacc_query,
            "tokens_raw": raw_tokens,
            "tokens_filtered": filtered_tokens,
            "stopwords_removed": removed_stopwords,
            "top_candidates": rrf_scored[:top_k]
        }

tracer = ExplainableSearchTracer(bm25_engine, semantic_engine, k=60)

test_trace_queries = [
    "Tôi muốn tìm sách học lập trình Python từ số 0",
    "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông",
    "chàng trai chăn cừu vượt sa mạc đi tìm kho báu dưới chân kim tự tháp",
    "Sách của Nguyễn Nhật Ánh",
    "Day kon lam giau"
]

trace_reports = []
for q in test_trace_queries:
    report = tracer.trace_query(q, top_k=5)
    trace_reports.append(report)
    print(f"\n" + "=" * 70)
    print(f"TRUY VẤN: '{report['query_original']}'")
    print(f"Tokens gốc: {report['tokens_raw']}")
    print(f"Tokens sau lọc Stopwords: {report['tokens_filtered']} (Đã loại bỏ: {report['stopwords_removed']})")
    print(f"BẢNG GIẢI THÍCH XẾP HẠNG TOP 5:")
    print(f"{'Hạng':<5} | {'Book_ID':<8} | {'Tên sách':<35} | {'BM25 (Rank/Score)':<18} | {'Semantic (Rank/Score)':<22} | {'RRF Score':<10} | {'Giải thích'}")
    print("-" * 125)
    for c in report['top_candidates']:
        bm_str = f"#{c['bm25_rank']} ({c['bm25_score']})" if c['bm25_rank'] else "None"
        sem_str = f"#{c['semantic_rank']} ({c['semantic_score']})" if c['semantic_rank'] else "None"
        title_disp = (c['title'][:32] + "...") if len(c['title']) > 32 else c['title']
        print(f"#{c['rrf_final_rank']:<4} | {c['book_id']:<8} | {title_disp:<35} | {bm_str:<18} | {sem_str:<22} | {c['rrf_total_score']:<10.5f} | {c['explanation']}")

os.makedirs("tests", exist_ok=True)
with open("tests/traceability_debug_report.json", "w", encoding="utf-8") as f:
    json.dump(trace_reports, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu toàn bộ báo cáo truy vết giải thích vào tests/traceability_debug_report.json")
