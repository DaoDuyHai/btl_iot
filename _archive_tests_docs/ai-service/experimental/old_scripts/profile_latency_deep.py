import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine, tokenize_query_optimized
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog, strip_accents

df = load_and_verify_dataset('dataset/cleaned_books_dataset.csv')
work_mapping = get_work_catalog(df)
emb_engine = EmbeddingEngine(cache_dir="embeddings")
embeddings, book_ids = emb_engine.get_or_build_embeddings(df)

bm25 = BM25SearchEngine(df, work_mapping)
semantic = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
hybrid = HybridSearchEngine(bm25, semantic, k=60)

with open('tests/verified_ground_truth_110.json', 'r', encoding='utf-8') as f:
    gt_cases = json.load(f)

queries = [tc['query'] for tc in gt_cases[:100]]

# Warm-up (10 queries)
print("[*] Running 10 warm-up queries...")
for q in queries[:10]:
    _ = hybrid.search(q, top_k=5, fetch_k=200)

print("[*] Profiling atomic latency on 100 queries...")
records = []

for q in queries:
    t_start = time.perf_counter()
    
    # Step 1: BM25
    t0 = time.perf_counter()
    q_tokens = tokenize_query_optimized(q)
    q_unacc = tokenize_query_optimized(strip_accents(q))
    all_toks = list(set(q_tokens + q_unacc))
    t_tok = time.perf_counter() - t0
    
    t0 = time.perf_counter()
    bm25_scores = bm25.bm25.get_scores(all_toks)
    top_bm25_idx = bm25_scores.argsort()[::-1][:200]
    t_bm25 = time.perf_counter() - t0
    
    # Step 2: Semantic
    t0 = time.perf_counter()
    q_vec = emb_engine.encode_queries([q])
    t_embed = time.perf_counter() - t0
    
    t0 = time.perf_counter()
    cos_scores = np.dot(embeddings, q_vec[0])
    top_sem_idx = cos_scores.argsort()[::-1][:200]
    t_cos = time.perf_counter() - t0
    
    # Step 3: RRF Fusion
    t0 = time.perf_counter()
    scores = {}
    for rank, idx in enumerate(top_bm25_idx, 1):
        wid = bm25.df.iloc[idx]['work_id']
        scores[wid] = scores.get(wid, 0.0) + (1.0 / (60 + rank))
    for rank, idx in enumerate(top_sem_idx, 1):
        wid = semantic.df.iloc[idx]['work_id']
        scores[wid] = scores.get(wid, 0.0) + (1.0 / (60 + rank))
    sorted_wids = sorted(scores.keys(), key=lambda w: scores[w], reverse=True)[:5]
    t_rrf = time.perf_counter() - t0
    
    # Step 4: Formatting
    t0 = time.perf_counter()
    results = []
    for rank, wid in enumerate(sorted_wids, 1):
        w_info = work_mapping[wid]
        first_copy = w_info['copies'][0] if w_info['copies'] else {}
        results.append({
            'work_id': wid,
            'title': w_info['base_title'],
            'score': float(scores[wid]),
            'rank': int(rank)
        })
    t_fmt = time.perf_counter() - t0
    
    t_total = time.perf_counter() - t_start
    
    records.append({
        "tok_ms": t_tok * 1000,
        "bm25_ms": t_bm25 * 1000,
        "embed_ms": t_embed * 1000,
        "cos_ms": t_cos * 1000,
        "rrf_ms": t_rrf * 1000,
        "fmt_ms": t_fmt * 1000,
        "total_ms": t_total * 1000
    })

lat_df = pd.DataFrame(records)

print("\n" + "=" * 70)
print("CHI TIẾT ĐỘ TRỄ TỪNG GIAI ĐOẠN (ATOMIC LATENCY BREAKDOWN - 100 QUERIES)")
print("=" * 70)
stats_df = pd.DataFrame({
    "Mean (ms)": lat_df.mean(),
    "Std (ms)": lat_df.std(),
    "Min (ms)": lat_df.min(),
    "P25 (ms)": lat_df.quantile(0.25),
    "P50/Median (ms)": lat_df.median(),
    "P75 (ms)": lat_df.quantile(0.75),
    "P95 (ms)": lat_df.quantile(0.95),
    "Max (ms)": lat_df.max()
})
print(stats_df.round(3).to_string())

sum_of_means = lat_df[['tok_ms', 'bm25_ms', 'embed_ms', 'cos_ms', 'rrf_ms', 'fmt_ms']].mean().sum()
total_mean = lat_df['total_ms'].mean()
print(f"\nTổng trung bình các thành phần: {sum_of_means:.3f} ms")
print(f"Thời gian tổng đo được:        {total_mean:.3f} ms")
print(f"Độ lệch không giải thích:      {abs(total_mean - sum_of_means):.3f} ms (Chênh lệch siêu nhỏ)")

# Save latency records for analysis
lat_df.to_csv('tests/latency_atomic_profile.csv', index=False)
