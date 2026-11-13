import os
import sys
import json
import time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine, tokenize_vietnamese, tokenize_query_optimized
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog, strip_accents

print("=" * 80)
print("RUNNING BENCHMARK POST NULL/NAN FIX")
print("=" * 80)

# Load dataset & Ground Truth
df = load_and_verify_dataset('dataset/cleaned_books_dataset.csv')
work_mapping = get_work_catalog(df)

with open('tests/verified_ground_truth_110.json', 'r', encoding='utf-8') as f:
    gt_cases = json.load(f)

in_domain_cases = [tc for tc in gt_cases if len(tc.get('rel_ids', [])) > 0]
print(f"Total In-Domain evaluation cases: {len(in_domain_cases)}")

emb_engine = EmbeddingEngine(cache_dir="embeddings")
embeddings, book_ids = emb_engine.get_or_build_embeddings(df)

bm25 = BM25SearchEngine(df, work_mapping)
semantic = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
# Giữ nguyên cấu hình cũ: k=60, fetch_k=200
hybrid = HybridSearchEngine(bm25, semantic, k=60)

modes = ['bm25', 'semantic', 'hybrid']
mode_results = {m: {"hit1": 0, "hit5": 0, "hit10": 0, "rec5": [], "rec10": [], "prec5": [], "rr": [], "lats": []} for m in modes}
detailed_case_results = []

for idx, tc in enumerate(in_domain_cases, 1):
    q = tc['query']
    target_ids = set(tc['rel_ids'])
    
    case_record = {
        "id": tc['id'],
        "group": tc['group'],
        "query": q,
        "total_relevant": len(target_ids),
        "modes": {}
    }
    
    for m in modes:
        t0 = time.perf_counter()
        if m == 'bm25':
            q_tokens = tokenize_query_optimized(q)
            q_unacc = tokenize_query_optimized(strip_accents(q))
            all_toks = list(set(q_tokens + q_unacc))
            scores = bm25.bm25.get_scores(all_toks)
            top_indices = scores.argsort()[::-1][:10]
            top_bids = [df.iloc[i]['Book_ID'] for i in top_indices if scores[i] > 0]
            lat = (time.perf_counter() - t0) * 1000.0
            
        elif m == 'semantic':
            sem_res = semantic.search(q, top_k=10)
            top_bids = [r['book_id'] for r in sem_res]
            lat = (time.perf_counter() - t0) * 1000.0
            
        else: # hybrid
            hyb_res = hybrid.search(q, top_k=10, fetch_k=200)
            top_bids = [r['book_id'] for r in hyb_res]
            lat = (time.perf_counter() - t0) * 1000.0
            
        mode_results[m]["lats"].append(lat)
        
        # Hits
        h1 = 1 if len(set(top_bids[:1]) & target_ids) > 0 else 0
        h5 = 1 if len(set(top_bids[:5]) & target_ids) > 0 else 0
        h10 = 1 if len(set(top_bids[:10]) & target_ids) > 0 else 0
        
        mode_results[m]["hit1"] += h1
        mode_results[m]["hit5"] += h5
        mode_results[m]["hit10"] += h10
        
        # Recalls
        r5 = len(set(top_bids[:5]) & target_ids) / len(target_ids)
        r10 = len(set(top_bids[:10]) & target_ids) / len(target_ids)
        
        # Precision@5
        p5 = len(set(top_bids[:5]) & target_ids) / 5.0
        
        mode_results[m]["rec5"].append(r5)
        mode_results[m]["rec10"].append(r10)
        mode_results[m]["prec5"].append(p5)
        
        # MRR
        rr = 0.0
        for rank, bid in enumerate(top_bids, 1):
            if bid in target_ids:
                rr = 1.0 / rank
                break
        mode_results[m]["rr"].append(rr)
        
        case_record["modes"][m] = {
            "top1_hit": bool(h1),
            "top5_hit": bool(h5),
            "top10_hit": bool(h10),
            "recall@5": round(r5, 4),
            "precision@5": round(p5, 4),
            "mrr": round(rr, 4),
            "latency_ms": round(lat, 2)
        }
    detailed_case_results.append(case_record)

summary = {}
n_total = len(in_domain_cases)

for m in modes:
    lats = mode_results[m]["lats"]
    summary[m] = {
        "Hit@1": round(mode_results[m]["hit1"] / n_total, 4),
        "Hit@5": round(mode_results[m]["hit5"] / n_total, 4),
        "Hit@10": round(mode_results[m]["hit10"] / n_total, 4),
        "Recall@5": round(float(np.mean(mode_results[m]["rec5"])), 4),
        "Recall@10": round(float(np.mean(mode_results[m]["rec10"])), 4),
        "Precision@5": round(float(np.mean(mode_results[m]["prec5"])), 4),
        "MRR": round(float(np.mean(mode_results[m]["rr"])), 4),
        "Avg_Latency_ms": round(float(np.mean(lats)), 2),
        "P50_Latency_ms": round(float(np.percentile(lats, 50)), 2),
        "P95_Latency_ms": round(float(np.percentile(lats, 95)), 2)
    }

output = {
    "summary": summary,
    "detailed": detailed_case_results
}

os.makedirs('tests', exist_ok=True)
with open('tests/post_null_fix_metrics.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("FINAL BENCHMARK COMPARISON TABLE (POST NULL/NAN FIX)")
print("=" * 80)
for m in modes:
    print(f"\n--- {m.upper()} ---")
    print(f"Hit@1: {summary[m]['Hit@1']*100:.1f}% | Hit@5: {summary[m]['Hit@5']*100:.1f}% | Hit@10: {summary[m]['Hit@10']*100:.1f}%")
    print(f"Recall@5: {summary[m]['Recall@5']:.4f} | Recall@10: {summary[m]['Recall@10']:.4f} | Precision@5: {summary[m]['Precision@5']:.4f} | MRR: {summary[m]['MRR']:.4f}")
    print(f"Latency: Mean={summary[m]['Avg_Latency_ms']:.2f}ms | P50={summary[m]['P50_Latency_ms']:.2f}ms | P95={summary[m]['P95_Latency_ms']:.2f}ms")
