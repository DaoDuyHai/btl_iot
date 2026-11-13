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

print("[*] Bắt đầu kiểm thử Sweep RRF hằng số k (20, 40, 60, 80, 100)...")

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
work_mapping = get_work_catalog(df)

embedding_engine = EmbeddingEngine()
embeddings, book_ids = embedding_engine.get_or_build_embeddings(df)

bm25_engine = BM25SearchEngine(df, work_mapping=work_mapping)
semantic_engine = SemanticSearchEngine(df, embedding_engine, embeddings, book_ids, work_mapping=work_mapping)

with open("tests/verified_ground_truth_110.json", "r", encoding="utf-8") as f:
    eval_suite = json.load(f)

in_domain = [t for t in eval_suite if len(t.get('rel_ids', [])) > 0]
print(f"Tổng số câu In-Domain: {len(in_domain)}")

# 1. Kiểm tra 4 tình huống RRF
print("\n=== KIỂM TRA 4 TÌNH HUỐNG RRF (với k=60) ===")
hybrid_default = HybridSearchEngine(bm25_engine, semantic_engine, k=60)

case_examples = {
    "high_both": "Tôi muốn học lập trình Python từ con số 0",
    "bm25_only": "Hector Malot",
    "semantic_only": "chàng trai chăn cừu vượt sa mạc đi tìm kho báu dưới chân kim tự tháp ai cập",
    "low_both": "ông già khó tính cộc cằn nhưng có trái tim ấm áp luôn muốn tự tử"
}

rrf_situations = {}
for name, q in case_examples.items():
    bm_res = bm25_engine.search(q, top_k=50)
    sem_res = semantic_engine.search(q, top_k=50)
    hyb_res = hybrid_default.search(q, top_k=5, fetch_k=200)
    
    if hyb_res:
        top1_wid = hyb_res[0]['work_id']
        top1_bid = hyb_res[0]['book_id']
        top1_title = hyb_res[0]['title']
        
        bm_rank = next((r['rank'] for r in bm_res if r['work_id'] == top1_wid), None)
        sem_rank = next((r['rank'] for r in sem_res if r['work_id'] == top1_wid), None)
        
        rrf_situations[name] = {
            "query": q,
            "top1_title": top1_title,
            "top1_book_id": top1_bid,
            "top1_work_id": top1_wid,
            "bm25_rank": bm_rank,
            "semantic_rank": sem_rank,
            "hybrid_top1_score": hyb_res[0]['score'],
            "hybrid_top5": [f"[{r['book_id']}] {r['title']} (Score: {r['score']:.4f})" for r in hyb_res]
        }
        print(f"[{name}] Query: '{q}'")
        print(f"  -> Top 1 Hybrid: [{top1_bid}] '{top1_title}' (BM25 Rank: {bm_rank}, Semantic Rank: {sem_rank}, Score: {hyb_res[0]['score']:.4f})")

# 2. Sweep tham số k = [20, 40, 60, 80, 100]
k_values = [20, 40, 60, 80, 100]
sweep_results = {}

# Warm-up
_ = hybrid_default.search("test warm up", top_k=5, fetch_k=200)

for k_val in k_values:
    engine = HybridSearchEngine(bm25_engine, semantic_engine, k=k_val)
    
    latencies = []
    hits1 = []
    hits5 = []
    hits10 = []
    recalls5 = []
    recalls10 = []
    precisions5 = []
    precisions10 = []
    mrrs = []
    
    for item in in_domain:
        query = item['query']
        target_ids = set(item['rel_ids'])
        
        t0 = time.perf_counter()
        retrieved = engine.search(query, top_k=10, fetch_k=200)
        dt = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt)
        
        ret_bids = [r['book_id'] for r in retrieved]
        
        # Hits
        h1 = 1.0 if len(set(ret_bids[:1]) & target_ids) > 0 else 0.0
        h5 = 1.0 if len(set(ret_bids[:5]) & target_ids) > 0 else 0.0
        h10 = 1.0 if len(set(ret_bids[:10]) & target_ids) > 0 else 0.0
        
        # Recalls
        r5 = len(set(ret_bids[:5]) & target_ids) / len(target_ids)
        r10 = len(set(ret_bids[:10]) & target_ids) / len(target_ids)
        
        # Precisions
        p5 = len(set(ret_bids[:5]) & target_ids) / 5.0
        p10 = len(set(ret_bids[:10]) & target_ids) / 10.0
        
        # MRR
        rr = 0.0
        for rank, bid in enumerate(ret_bids, 1):
            if bid in target_ids:
                rr = 1.0 / rank
                break
                
        hits1.append(h1)
        hits5.append(h5)
        hits10.append(h10)
        recalls5.append(r5)
        recalls10.append(r10)
        precisions5.append(p5)
        precisions10.append(p10)
        mrrs.append(rr)
        
    sweep_results[f"k={k_val}"] = {
        "k": k_val,
        "hit@1": round(float(np.mean(hits1) * 100), 2),
        "hit@5": round(float(np.mean(hits5) * 100), 2),
        "hit@10": round(float(np.mean(hits10) * 100), 2),
        "recall@5": round(float(np.mean(recalls5)), 4),
        "recall@10": round(float(np.mean(recalls10)), 4),
        "precision@5": round(float(np.mean(precisions5)), 4),
        "precision@10": round(float(np.mean(precisions10)), 4),
        "mrr": round(float(np.mean(mrrs)), 4),
        "latency_mean_ms": round(float(np.mean(latencies)), 2),
        "latency_p50_ms": round(float(np.percentile(latencies, 50)), 2),
        "latency_p95_ms": round(float(np.percentile(latencies, 95)), 2)
    }
    
    print(f"\n[+] Kết quả k={k_val}:")
    print(f"    Hit@1={sweep_results[f'k={k_val}']['hit@1']}%, Hit@5={sweep_results[f'k={k_val}']['hit@5']}%, Hit@10={sweep_results[f'k={k_val}']['hit@10']}%")
    print(f"    Recall@5={sweep_results[f'k={k_val}']['recall@5']}, Recall@10={sweep_results[f'k={k_val}']['recall@10']}")
    print(f"    Precision@5={sweep_results[f'k={k_val}']['precision@5']}, Precision@10={sweep_results[f'k={k_val}']['precision@10']}, MRR={sweep_results[f'k={k_val}']['mrr']}")
    print(f"    Mean Latency={sweep_results[f'k={k_val}']['latency_mean_ms']}ms, P50={sweep_results[f'k={k_val}']['latency_p50_ms']}ms, P95={sweep_results[f'k={k_val}']['latency_p95_ms']}ms")

output_payload = {
    "rrf_situations": rrf_situations,
    "k_parameter_sweep": sweep_results
}

os.makedirs("tests", exist_ok=True)
with open("tests/rrf_k_sweep_results.json", "w", encoding="utf-8") as f:
    json.dump(output_payload, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu toàn bộ kết quả RRF Sweep vào tests/rrf_k_sweep_results.json")
