import sys
import os
import json
import time
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

print("[*] Bắt đầu kiểm thử Độ ổn định của kết quả (Hạng mục E)...")

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
work_mapping = get_work_catalog(df)

embedding_engine = EmbeddingEngine()
embeddings, book_ids = embedding_engine.get_or_build_embeddings(df)

bm25_engine = BM25SearchEngine(df, work_mapping=work_mapping)
semantic_engine = SemanticSearchEngine(df, embedding_engine, embeddings, book_ids, work_mapping=work_mapping)
hybrid_engine = HybridSearchEngine(bm25_engine, semantic_engine, k=60)

test_queries = [
    "Tôi muốn học lập trình Python từ con số 0",
    "Nguyễn Nhật Ánh",
    "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông",
    "Sách dạy làm giàu",
    "Nhà Giả Kim",
    "chàng trai chăn cừu vượt sa mạc đi tìm kho báu dưới chân kim tự tháp",
    "tieng viet khong dau",
    "Sách về trí tuệ nhân tạo và máy học",
    "Fredrik Backman",
    "Lập trình hướng đối tượng Java"
]

NUM_RUNS = 10
stability_results = []

for q_idx, q in enumerate(test_queries, 1):
    runs_data = []
    top1_list = []
    top5_orders = []
    scores_list = []
    has_duplicates_in_any_run = False
    
    for r in range(NUM_RUNS):
        res = hybrid_engine.search(q, top_k=5, fetch_k=200)
        
        # Check duplicates
        bids = [item['book_id'] for item in res]
        wids = [item['work_id'] for item in res]
        if len(bids) != len(set(bids)) or len(wids) != len(set(wids)):
            has_duplicates_in_any_run = True
            
        top1 = res[0]['title'] if res else None
        top1_score = res[0]['score'] if res else None
        top5_order = [item['title'] for item in res]
        scores = [item['score'] for item in res]
        
        top1_list.append(top1)
        top5_orders.append(top5_order)
        scores_list.append(scores)
        
        runs_data.append({
            "run": r + 1,
            "top1": top1,
            "top1_score": top1_score,
            "top5": top5_order
        })
        
    # Check consistency
    top1_stable = all(t == top1_list[0] for t in top1_list)
    top5_order_stable = all(order == top5_orders[0] for order in top5_orders)
    # Check scores consistency within float precision 1e-6
    scores_diff = max(abs(s[i] - scores_list[0][i]) for s in scores_list for i in range(len(s)))
    scores_stable = scores_diff < 1e-6
    
    print(f"\n[Q{q_idx}] '{q}' (Chạy {NUM_RUNS} lần):")
    print(f"     Top 1 đồng nhất 100%? {top1_stable} ('{top1_list[0]}')")
    print(f"     Thứ tự Top 5 giữ nguyên? {top5_order_stable}")
    print(f"     Điểm RRF đồng nhất (diff={scores_diff:.2e})? {scores_stable}")
    print(f"     Có trùng lặp kết quả (duplicates)? {has_duplicates_in_any_run}")
    
    stability_results.append({
        "query": q,
        "runs": NUM_RUNS,
        "top1_stable": top1_stable,
        "top5_order_stable": top5_order_stable,
        "scores_stable": scores_stable,
        "max_score_diff": float(scores_diff),
        "has_duplicates": has_duplicates_in_any_run,
        "top1_title": top1_list[0],
        "top5_sample": top5_orders[0]
    })

os.makedirs("tests", exist_ok=True)
with open("tests/stability_repeatability_eval.json", "w", encoding="utf-8") as f:
    json.dump(stability_results, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu toàn bộ kết quả kiểm thử độ ổn định vào tests/stability_repeatability_eval.json")
