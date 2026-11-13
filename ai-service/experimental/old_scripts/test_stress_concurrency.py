import sys
import os
import json
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("[*] Bắt đầu kiểm thử Hiệu năng, Tải & Đột biến đồng thời (Hạng mục F)...")

# 1. Cold Start measurement (đo từ lúc bắt đầu import và load model)
t_start_cold = time.perf_counter()
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
work_mapping = get_work_catalog(df)

t_load_model_start = time.perf_counter()
embedding_engine = EmbeddingEngine()
embeddings, book_ids = embedding_engine.get_or_build_embeddings(df)
t_load_model_end = time.perf_counter()

bm25_engine = BM25SearchEngine(df, work_mapping=work_mapping)
semantic_engine = SemanticSearchEngine(df, embedding_engine, embeddings, book_ids, work_mapping=work_mapping)
hybrid_engine = HybridSearchEngine(bm25_engine, semantic_engine, k=60)

cold_start_total_sec = time.perf_counter() - t_start_cold
model_load_only_sec = t_load_model_end - t_load_model_start

print(f"\n[+] Cold Start:")
print(f"    - Thời gian load model E5: {model_load_only_sec:.2f} s")
print(f"    - Tổng thời gian Cold Start (Load data + Index + Model): {cold_start_total_sec:.2f} s")

# 2. Warm-up: Truy vấn đầu tiên sau khởi động
t_warm_start = time.perf_counter()
first_res = hybrid_engine.search("Khởi động hệ thống thư viện thông minh", top_k=5, fetch_k=200)
warmup_latency_ms = (time.perf_counter() - t_warm_start) * 1000.0
print(f"[+] Warm-up Latency (Truy vấn đầu tiên): {warmup_latency_ms:.2f} ms")

# Tập danh sách câu hỏi đa dạng dùng cho stress test
sample_pool = [
    "Tôi muốn học lập trình Python từ con số 0",
    "Nguyễn Nhật Ánh viết về tuổi học trò",
    "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông",
    "Sách dạy làm giàu và tư duy tài chính",
    "Nhà Giả Kim",
    "chàng trai chăn cừu vượt sa mạc đi tìm kho báu dưới chân kim tự tháp",
    "tieng viet khong dau",
    "Sách về trí tuệ nhân tạo và máy học",
    "Fredrik Backman",
    "Lập trình hướng đối tượng Java",
    "phương pháp dạy con thời đại số",
    "sách tâm lý học hành vi con người",
    "thiết kế website frontend react vue",
    "lịch sử thế giới cổ đại văn minh hy lạp la mã",
    "tiểu thuyết trinh thám sherlock holmes"
]

proc = psutil.Process()

def run_sequential_benchmark(num_queries: int):
    print(f"\n--- Kiểm thử {num_queries} truy vấn tuần tự ---")
    ram_before_mb = proc.memory_info().rss / (1024 * 1024)
    cpu_measurements = []
    latencies = []
    errors = 0
    
    t_start = time.perf_counter()
    for i in range(num_queries):
        q = sample_pool[i % len(sample_pool)]
        try:
            t0 = time.perf_counter()
            _ = hybrid_engine.search(q, top_k=5, fetch_k=200)
            dt = (time.perf_counter() - t0) * 1000.0
            latencies.append(dt)
        except Exception:
            errors += 1
        if i % 100 == 0:
            cpu_measurements.append(psutil.cpu_percent(interval=None))
            
    total_elapsed = time.perf_counter() - t_start
    ram_after_mb = proc.memory_info().rss / (1024 * 1024)
    
    return {
        "num_queries": num_queries,
        "total_time_s": round(total_elapsed, 2),
        "qps": round(num_queries / total_elapsed, 2),
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "p50_latency_ms": round(float(np.percentile(latencies, 50)), 2),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
        "p99_latency_ms": round(float(np.percentile(latencies, 99)), 2),
        "ram_before_mb": round(ram_before_mb, 2),
        "ram_after_mb": round(ram_after_mb, 2),
        "ram_delta_mb": round(ram_after_mb - ram_before_mb, 2),
        "cpu_avg_percent": round(float(np.mean(cpu_measurements)) if cpu_measurements else 0.0, 1),
        "errors": errors
    }

# Chạy 100 tuần tự
res_seq_100 = run_sequential_benchmark(100)
print(f"100 tuần tự: Mean={res_seq_100['mean_latency_ms']}ms, P50={res_seq_100['p50_latency_ms']}ms, P95={res_seq_100['p95_latency_ms']}ms, QPS={res_seq_100['qps']}")

# Chạy 1.000 tuần tự
res_seq_1000 = run_sequential_benchmark(1000)
print(f"1.000 tuần tự: Mean={res_seq_1000['mean_latency_ms']}ms, P50={res_seq_1000['p50_latency_ms']}ms, P95={res_seq_1000['p95_latency_ms']}ms, QPS={res_seq_1000['qps']}")
print(f"RAM delta sau 1000 truy vấn: {res_seq_1000['ram_delta_mb']} MB (Before: {res_seq_1000['ram_before_mb']}MB, After: {res_seq_1000['ram_after_mb']}MB)")

# 3. Concurrent Benchmarks (5, 10, 20 người dùng đồng thời)
def run_concurrent_benchmark(num_concurrency: int, total_requests: int):
    print(f"\n--- Kiểm thử {num_concurrency} người dùng đồng thời ({total_requests} requests) ---")
    ram_before_mb = proc.memory_info().rss / (1024 * 1024)
    cpu_measurements = []
    latencies = []
    errors = 0
    
    def worker_task(idx):
        q = sample_pool[idx % len(sample_pool)]
        t0 = time.perf_counter()
        _ = hybrid_engine.search(q, top_k=5, fetch_k=200)
        return (time.perf_counter() - t0) * 1000.0

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=num_concurrency) as executor:
        futures = [executor.submit(worker_task, i) for i in range(total_requests)]
        for f in as_completed(futures):
            try:
                lat = f.result()
                latencies.append(lat)
            except Exception:
                errors += 1
                
    total_elapsed = time.perf_counter() - t_start
    ram_after_mb = proc.memory_info().rss / (1024 * 1024)
    
    return {
        "concurrency": num_concurrency,
        "total_requests": total_requests,
        "total_time_s": round(total_elapsed, 2),
        "qps": round(total_requests / total_elapsed, 2),
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "p50_latency_ms": round(float(np.percentile(latencies, 50)), 2),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
        "p99_latency_ms": round(float(np.percentile(latencies, 99)), 2),
        "ram_before_mb": round(ram_before_mb, 2),
        "ram_after_mb": round(ram_after_mb, 2),
        "ram_delta_mb": round(ram_after_mb - ram_before_mb, 2),
        "errors": errors
    }

res_conc_5 = run_concurrent_benchmark(5, 50)
print(f"5 đồng thời : Mean={res_conc_5['mean_latency_ms']}ms, P50={res_conc_5['p50_latency_ms']}ms, P95={res_conc_5['p95_latency_ms']}ms, QPS={res_conc_5['qps']}")

res_conc_10 = run_concurrent_benchmark(10, 100)
print(f"10 đồng thời: Mean={res_conc_10['mean_latency_ms']}ms, P50={res_conc_10['p50_latency_ms']}ms, P95={res_conc_10['p95_latency_ms']}ms, QPS={res_conc_10['qps']}")

res_conc_20 = run_concurrent_benchmark(20, 200)
print(f"20 đồng thời: Mean={res_conc_20['mean_latency_ms']}ms, P50={res_conc_20['p50_latency_ms']}ms, P95={res_conc_20['p95_latency_ms']}ms, QPS={res_conc_20['qps']}")

stress_test_report_data = {
    "cold_start": {
        "model_load_sec": round(model_load_only_sec, 2),
        "total_cold_start_sec": round(cold_start_total_sec, 2),
        "warmup_latency_ms": round(warmup_latency_ms, 2)
    },
    "sequential_100": res_seq_100,
    "sequential_1000": res_seq_1000,
    "concurrent_5": res_conc_5,
    "concurrent_10": res_conc_10,
    "concurrent_20": res_conc_20
}

os.makedirs("tests", exist_ok=True)
with open("tests/stress_performance_eval.json", "w", encoding="utf-8") as f:
    json.dump(stress_test_report_data, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu toàn bộ số liệu đo hiệu năng vào tests/stress_performance_eval.json")
