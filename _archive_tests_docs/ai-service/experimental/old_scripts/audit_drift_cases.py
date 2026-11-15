import sys
import os
import json
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
work_mapping = get_work_catalog(df)
emb_engine = EmbeddingEngine()
embeddings, book_ids = emb_engine.get_or_build_embeddings(df)
bm25 = BM25SearchEngine(df, work_mapping)
semantic = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
hybrid = HybridSearchEngine(bm25, semantic, k=60)

queries = [
    ("SD01", "Sách về loài trăn khổng lồ săn mồi trong rừng nhiệt đới"),
    ("SD02", "Văn hóa và lịch sử vùng đảo Java Indonesia"),
    ("SD03", "Khởi đầu mùa xuân tươi đẹp và tràn đầy sức sống"),
    ("SD04/TC053", "ông già khó tính cộc cằn nhưng có trái tim ấm áp luôn muốn tự tử"),
    ("SD05", "Có ai cùng tôi đi qua những năm tháng thanh xuân cô đơn"),
    ("SD06", "Tác phẩm của tác giả Fredrik Backman")
]

print("=== RE-RUNNING SD01 - SD06 WITH FULL BREAKDOWN ===")
for qid, q in queries:
    b_res = bm25.search(q, top_k=3)
    s_res = semantic.search(q, top_k=3)
    h_res = hybrid.search(q, top_k=3, fetch_k=200)
    print(f"\n--- [{qid}] '{q}' ---")
    print(f"BM25 Top 1    : [{b_res[0]['book_id']}] {b_res[0]['title']} | Author: {b_res[0]['author']} | Cat: {b_res[0]['category']} | Score: {b_res[0]['score']:.2f}")
    print(f"Semantic Top 1: [{s_res[0]['book_id']}] {s_res[0]['title']} | Author: {s_res[0]['author']} | Cat: {s_res[0]['category']} | Score: {s_res[0]['score']:.4f}")
    print(f"Hybrid Top 1  : [{h_res[0]['book_id']}] {h_res[0]['title']} | Author: {h_res[0]['author']} | Cat: {h_res[0]['category']} | Score: {h_res[0]['score']:.5f}")
    # Also find Ove rank for SD04
    if "SD04" in qid:
        b_all = bm25.search(q, top_k=200)
        s_all = semantic.search(q, top_k=200)
        h_all = hybrid.search(q, top_k=200, fetch_k=200)
        b_ove = next((r['rank'] for r in b_all if "ove" in r['title'].lower()), None)
        s_ove = next((r['rank'] for r in s_all if "ove" in r['title'].lower()), None)
        h_ove = next((r['rank'] for r in h_all if "ove" in r['title'].lower()), None)
        print(f"  -> Ove ranks: BM25 Rank = {b_ove}, Semantic Rank = {s_ove}, Hybrid Rank = {h_ove}")
