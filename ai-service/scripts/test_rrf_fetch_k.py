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

df = load_and_verify_dataset('dataset/cleaned_books_dataset.csv')
work_mapping = get_work_catalog(df)

with open('tests/verified_ground_truth_110.json', 'r', encoding='utf-8') as f:
    gt_cases = json.load(f)

in_domain_cases = [tc for tc in gt_cases if len(tc['rel_ids']) > 0]

emb_engine = EmbeddingEngine(cache_dir="embeddings")
embeddings, book_ids = emb_engine.get_or_build_embeddings(df)

bm25 = BM25SearchEngine(df, work_mapping)
semantic = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)

fetch_k_values = [40, 100, 200, 300]
results_by_fetch_k = {}

print("=" * 70)
print("THỬ NGHIỆM ĐỘ SÂU RRF FETCH_K (40 / 100 / 200 / 300)")
print("=" * 70)

for fk in fetch_k_values:
    hybrid = HybridSearchEngine(bm25, semantic, k=60)
    
    hit1, hit5, hit10 = 0, 0, 0
    rec5, rec10 = [], []
    prec5 = []
    rr_list = []
    lats = []
    
    for tc in in_domain_cases:
        q = tc['query']
        target_ids = set(tc['rel_ids'])
        
        t0 = time.time()
        # Custom fetch_k search
        top_results = hybrid.search(q, top_k=10, fetch_k=fk)
        lats.append((time.time() - t0) * 1000)
        
        retrieved_bids = [r['book_id'] for r in top_results]
        
        hit_1 = 1 if len(set(retrieved_bids[:1]) & target_ids) > 0 else 0
        hit_5 = 1 if len(set(retrieved_bids[:5]) & target_ids) > 0 else 0
        hit_10 = 1 if len(set(retrieved_bids[:10]) & target_ids) > 0 else 0
        
        hit1 += hit_1
        hit5 += hit_5
        hit10 += hit_10
        
        r5 = len(set(retrieved_bids[:5]) & target_ids) / len(target_ids)
        r10 = len(set(retrieved_bids[:10]) & target_ids) / len(target_ids)
        rec5.append(r5)
        rec10.append(r10)
        
        p5 = len(set(retrieved_bids[:5]) & target_ids) / 5.0
        prec5.append(p5)
        
        rr = 0.0
        for rank, bid in enumerate(retrieved_bids, 1):
            if bid in target_ids:
                rr = 1.0 / rank
                break
        rr_list.append(rr)
        
    n = len(in_domain_cases)
    results_by_fetch_k[f"fetch_k={fk}"] = {
        "Hit@1": round(hit1 / n, 4),
        "Hit@5": round(hit5 / n, 4),
        "Hit@10": round(hit10 / n, 4),
        "Recall@5": round(float(np.mean(rec5)), 4),
        "Recall@10": round(float(np.mean(rec10)), 4),
        "Precision@5": round(float(np.mean(prec5)), 4),
        "MRR": round(float(np.mean(rr_list)), 4),
        "Avg_Latency_ms": round(float(np.mean(lats)), 2),
        "P95_Latency_ms": round(float(np.percentile(lats, 95)), 2)
    }

summary_df = pd.DataFrame(results_by_fetch_k).T
print("\n" + summary_df.to_string())

with open('tests/rrf_fetch_k_comparison.json', 'w', encoding='utf-8') as f:
    json.dump(results_by_fetch_k, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu kết quả thử nghiệm vào tests/rrf_fetch_k_comparison.json!")
