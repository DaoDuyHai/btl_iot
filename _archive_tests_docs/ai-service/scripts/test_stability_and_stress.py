import os
import sys
import json
import time
import psutil
import concurrent.futures

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

df = load_and_verify_dataset('dataset/cleaned_books_dataset.csv')
work_mapping = get_work_catalog(df)
emb_engine = EmbeddingEngine(cache_dir="embeddings")
embeddings, book_ids = emb_engine.get_or_build_embeddings(df)

bm25 = BM25SearchEngine(df, work_mapping)
semantic = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
hybrid = HybridSearchEngine(bm25, semantic, k=60)

with open('tests/verified_ground_truth_110.json', 'r', encoding='utf-8') as f:
    gt_cases = json.load(f)

queries = [tc['query'] for tc in gt_cases[:50]] * 10  # 500 requests

proc = psutil.Process()
ram_initial = proc.memory_info().rss / (1024**2)

print("=" * 70)
print("STRESS & STABILITY BENCHMARK (500 SEQUENTIAL + CONCURRENT TEST)")
print("=" * 70)
print(f"RAM khởi điểm: {ram_initial:.2f} MB")

# Phase 1: Sequential 500 queries to test memory leak
ram_checkpoints = []
t0 = time.time()
for i, q in enumerate(queries, 1):
    _ = hybrid.search(q, top_k=5, fetch_k=200)
    if i in [100, 250, 500]:
        r = proc.memory_info().rss / (1024**2)
        ram_checkpoints.append((i, r))

total_seq_time = time.time() - t0
seq_qps = len(queries) / total_seq_time

print(f"\n1. Chạy tuần tự 500 truy vấn: {total_seq_time:.2f}s (Throughput: {seq_qps:.2f} QPS)")
for req_num, r in ram_checkpoints:
    print(f"   - Sau {req_num} queries: RAM = {r:.2f} MB (Delta so với đầu: {r - ram_initial:+.2f} MB)")

# Phase 2: Concurrent stress test (5 threads simulating 5 simultaneous Kiosk users)
print("\n2. Kiểm tra tải đồng thời (5 concurrent threads, 100 queries)...")
test_concurrent_queries = queries[:100]

def search_task(q):
    t_start = time.perf_counter()
    res = hybrid.search(q, top_k=5, fetch_k=200)
    return (time.perf_counter() - t_start) * 1000

t_conc_start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    conc_latencies = list(executor.map(search_task, test_concurrent_queries))
total_conc_time = time.time() - t_conc_start
conc_qps = len(test_concurrent_queries) / total_conc_time

print(f"   - Tổng thời gian 100 truy vấn đồng thời: {total_conc_time:.2f}s")
print(f"   - Throughput đồng thời: {conc_qps:.2f} QPS")
print(f"   - Độ trễ TB dưới tải đồng thời: {np.mean(conc_latencies):.2f} ms")
print(f"   - P95 độ trễ dưới tải đồng thời: {np.percentile(conc_latencies, 95):.2f} ms")

ram_final = proc.memory_info().rss / (1024**2)
print(f"\nRAM cuối cùng sau toàn bộ test: {ram_final:.2f} MB (Rò rỉ bộ nhớ = {ram_final - ram_initial:.2f} MB)")

stability_results = {
    "ram_initial_mb": round(ram_initial, 2),
    "ram_final_mb": round(ram_final, 2),
    "ram_leak_mb": round(ram_final - ram_initial, 2),
    "sequential_500_time_sec": round(total_seq_time, 2),
    "sequential_qps": round(seq_qps, 2),
    "concurrent_5_threads_qps": round(conc_qps, 2),
    "concurrent_latency_mean_ms": round(float(np.mean(conc_latencies)), 2),
    "concurrent_latency_p95_ms": round(float(np.percentile(conc_latencies, 95)), 2)
}

with open('tests/stability_and_stress_results.json', 'w', encoding='utf-8') as f:
    json.dump(stability_results, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu kết quả đo độ ổn định vào tests/stability_and_stress_results.json!")
