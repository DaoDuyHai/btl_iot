import os
import sys
import json
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from rank_bm25 import BM25Okapi
from src.work_mapping import extract_base_title, strip_accents, get_work_catalog
from src.data_processing import load_and_verify_dataset

df = load_and_verify_dataset('dataset/cleaned_books_dataset.csv')
work_mapping = get_work_catalog(df)

with open('tests/verified_ground_truth_110.json', 'r', encoding='utf-8') as f:
    gt_cases = json.load(f)

QUERY_STOPWORDS = {
    'tôi', 'em', 'mình', 'bạn', 'muốn', 'tìm', 'sách', 'cuốn', 'những', 'các', 
    'cho', 'về', 'ở', 'đang', 'xin', 'hỏi', 'có', 'nào', 'gì', 'một', 'được', 
    'này', 'ấy', 'nhé', 'giúp', 'thư', 'viện'
}

def tokenize_basic(text: str) -> list:
    text = text.lower()
    return re.findall(r'\b\w+\b', text)

def tokenize_with_stopwords(text: str) -> list:
    tokens = tokenize_basic(text)
    filtered = [t for t in tokens if t not in QUERY_STOPWORDS]
    # If all tokens were filtered out (rare), fallback to original tokens
    return filtered if filtered else tokens

print(">>> Xây dựng 2 bộ BM25: Gốc (Basic) vs Đã lọc Stopwords (Optimized)...")

# Corpus preparation
corpus = []
for _, row in df.iterrows():
    content = f"{row.get('Title', '')} {row.get('Author', '')} {row.get('Category', '')} {row.get('Subcategory', '')} {row.get('Keywords', '')} {row.get('Description', '')}"
    unaccented_content = f"{strip_accents(str(row.get('Title', '')))} {strip_accents(str(row.get('Author', '')))} {strip_accents(str(row.get('Keywords', '')))}"
    full_text = f"{content} {unaccented_content}"
    corpus.append(tokenize_basic(full_text))

bm25_model = BM25Okapi(corpus)

# Run benchmark on 100 In-Domain test queries
def eval_bm25(use_stopwords=False):
    hit1, hit5, hit10 = 0, 0, 0
    rec5, rec10 = [], []
    prec5 = []
    rr_list = []
    
    in_domain_cases = [tc for tc in gt_cases if len(tc['rel_ids']) > 0]
    
    for tc in in_domain_cases:
        q = tc['query']
        target_ids = set(tc['rel_ids'])
        
        if use_stopwords:
            tokens = tokenize_with_stopwords(q)
            unacc = tokenize_with_stopwords(strip_accents(q))
        else:
            tokens = tokenize_basic(q)
            unacc = tokenize_basic(strip_accents(q))
            
        all_tokens = list(set(tokens + unacc))
        scores = bm25_model.get_scores(all_tokens)
        top_indices = scores.argsort()[::-1][:10]
        
        retrieved_bids = [df.iloc[idx]['Book_ID'] for idx in top_indices if scores[idx] > 0]
        
        # Hit@K
        hit_1 = 1 if len(set(retrieved_bids[:1]) & target_ids) > 0 else 0
        hit_5 = 1 if len(set(retrieved_bids[:5]) & target_ids) > 0 else 0
        hit_10 = 1 if len(set(retrieved_bids[:10]) & target_ids) > 0 else 0
        
        hit1 += hit_1
        hit5 += hit_5
        hit10 += hit_10
        
        # Recall@K: retrieved relevant in top K / total relevant
        r5 = len(set(retrieved_bids[:5]) & target_ids) / len(target_ids)
        r10 = len(set(retrieved_bids[:10]) & target_ids) / len(target_ids)
        rec5.append(r5)
        rec10.append(r10)
        
        # Precision@5: retrieved relevant in top 5 / 5
        p5 = len(set(retrieved_bids[:5]) & target_ids) / 5.0
        prec5.append(p5)
        
        # RR
        rr = 0.0
        for rank, bid in enumerate(retrieved_bids, 1):
            if bid in target_ids:
                rr = 1.0 / rank
                break
        rr_list.append(rr)
        
    n = len(in_domain_cases)
    return {
        "Hit@1": round(hit1 / n, 4),
        "Hit@5": round(hit5 / n, 4),
        "Hit@10": round(hit10 / n, 4),
        "Recall@5": round(float(np.mean(rec5)), 4),
        "Recall@10": round(float(np.mean(rec10)), 4),
        "Precision@5": round(float(np.mean(prec5)), 4),
        "MRR": round(float(np.mean(rr_list)), 4)
    }

res_before = eval_bm25(use_stopwords=False)
res_after = eval_bm25(use_stopwords=True)

print("\n" + "=" * 70)
print("SO SÁNH HIỆU NĂNG BM25: TRƯỚC VÀ SAU KHI LỌC STOPWORDS")
print("=" * 70)
comp_df = pd.DataFrame([res_before, res_after], index=["BM25 (Gốc)", "BM25 (+Stopwords Query Filter)"])
print(comp_df.to_string())
