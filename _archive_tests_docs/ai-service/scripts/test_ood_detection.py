import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.work_mapping import get_work_catalog

df = load_and_verify_dataset('dataset/cleaned_books_dataset.csv')
work_mapping = get_work_catalog(df)

with open('tests/verified_ground_truth_110.json', 'r', encoding='utf-8') as f:
    gt_cases = json.load(f)

emb_engine = EmbeddingEngine(cache_dir="embeddings")
embeddings, book_ids = emb_engine.get_or_build_embeddings(df)

bm25 = BM25SearchEngine(df, work_mapping)
semantic = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)

records = []
for tc in gt_cases:
    q = tc['query']
    is_ood = 1 if len(tc['rel_ids']) == 0 else 0
    
    # BM25 scores
    bm25_res = bm25.search_raw(q, top_k=5)
    top1_bm25 = bm25_res[0]['score'] if len(bm25_res) > 0 else 0.0
    bm25_has_match = 1 if top1_bm25 > 5.0 else 0
    
    # Semantic scores
    sem_res = semantic.search_raw(q, top_k=5)
    top1_cos = sem_res[0]['score'] if len(sem_res) > 0 else 0.0
    top2_cos = sem_res[1]['score'] if len(sem_res) > 1 else 0.0
    margin_cos = top1_cos - top2_cos
    
    records.append({
        "id": tc['id'],
        "group": tc['group'],
        "query": q,
        "is_ood": is_ood,
        "top1_cos": round(top1_cos, 4),
        "top2_cos": round(top2_cos, 4),
        "margin_cos": round(margin_cos, 4),
        "top1_bm25": round(top1_bm25, 2)
    })

data = pd.DataFrame(records)

print("=" * 70)
print("PHÂN PHỐI ĐẶC TRƯNG IN-DOMAIN VS OUT-OF-DOMAIN")
print("=" * 70)
in_d = data[data['is_ood'] == 0]
ood = data[data['is_ood'] == 1]

print("\n--- IN-DOMAIN (100 câu) ---")
print(f"Top 1 Cosine : Min={in_d['top1_cos'].min():.4f}, Mean={in_d['top1_cos'].mean():.4f}, Max={in_d['top1_cos'].max():.4f}")
print(f"Margin Cos   : Min={in_d['margin_cos'].min():.4f}, Mean={in_d['margin_cos'].mean():.4f}, Max={in_d['margin_cos'].max():.4f}")
print(f"Top 1 BM25   : Min={in_d['top1_bm25'].min():.2f}, Mean={in_d['top1_bm25'].mean():.2f}, Max={in_d['top1_bm25'].max():.2f}")
print(f"Số câu BM25 == 0: {len(in_d[in_d['top1_bm25'] == 0])}/100")

print("\n--- OUT-OF-DOMAIN (10 câu) ---")
print(f"Top 1 Cosine : Min={ood['top1_cos'].min():.4f}, Mean={ood['top1_cos'].mean():.4f}, Max={ood['top1_cos'].max():.4f}")
print(f"Margin Cos   : Min={ood['margin_cos'].min():.4f}, Mean={ood['margin_cos'].mean():.4f}, Max={ood['margin_cos'].max():.4f}")
print(f"Top 1 BM25   : Min={ood['top1_bm25'].min():.2f}, Mean={ood['top1_bm25'].mean():.2f}, Max={ood['top1_bm25'].max():.2f}")
print(f"Số câu BM25 == 0: {len(ood[ood['top1_bm25'] == 0])}/10")

print("\nChi tiết 10 câu OOD:")
for _, r in ood.iterrows():
    print(f"  [{r['id']}] '{r['query']}' -> Cos: {r['top1_cos']}, Margin: {r['margin_cos']}, BM25: {r['top1_bm25']}")

# Test Decision Rules
print("\n" + "=" * 70)
print("ĐÁNH GIÁ CÁC QUY TẮC PHÁT HIỆN OOD")
print("=" * 70)

def eval_rule(name, rule_fn):
    # rule_fn returns True if classified as OOD, False if In-Domain
    pred_ood = data.apply(rule_fn, axis=1)
    
    # False Reject: is_ood == 0 but predicted as OOD
    false_reject = ((data['is_ood'] == 0) & (pred_ood == True)).sum()
    false_reject_rate = false_reject / len(in_d)
    
    # False Accept: is_ood == 1 but predicted as In-Domain
    false_accept = ((data['is_ood'] == 1) & (pred_ood == False)).sum()
    false_accept_rate = false_accept / len(ood)
    
    # True Detect OOD: is_ood == 1 and predicted as OOD
    true_ood_detect = len(ood) - false_accept
    
    print(f"\n[Quy tắc: {name}]")
    print(f"  OOD phát hiện đúng : {true_ood_detect}/10 ({true_ood_detect/10*100:.1f}%)")
    print(f"  False Accept (Lọt OOD): {false_accept}/10 ({false_accept_rate*100:.1f}%)")
    print(f"  False Reject (Từ chối nhầm In-Domain): {false_reject}/100 ({false_reject_rate*100:.1f}%)")
    return {
        "rule": name,
        "true_detect": int(true_ood_detect),
        "false_accept_pct": round(false_accept_rate * 100, 1),
        "false_reject_pct": round(false_reject_rate * 100, 1)
    }

rules_summary = []

# Rule 1: Cosine Threshold đơn thuần T=0.82
rules_summary.append(eval_rule("1. Cosine đơn thuần (< 0.82)", lambda r: r['top1_cos'] < 0.82))

# Rule 2: Cosine Threshold đơn thuần T=0.84
rules_summary.append(eval_rule("2. Cosine đơn thuần (< 0.84)", lambda r: r['top1_cos'] < 0.84))

# Rule 3: Cosine < 0.835 VÀ Margin < 0.02
rules_summary.append(eval_rule("3. Cosine < 0.835 VÀ Margin < 0.02", lambda r: (r['top1_cos'] < 0.835) and (r['margin_cos'] < 0.02)))

# Rule 4: Multi-signal kết hợp: BM25 < 5.0 VÀ Cosine < 0.835 VÀ Margin < 0.02
rules_summary.append(eval_rule(
    "4. Đa tín hiệu: BM25 < 5.0 VÀ (Cosine < 0.835 VÀ Margin < 0.02)",
    lambda r: (r['top1_bm25'] < 5.0) and (r['top1_cos'] < 0.835) and (r['margin_cos'] < 0.02)
))

# Rule 5: Đa tín hiệu thích ứng: (BM25 == 0 VÀ Cosine < 0.84) HOẶC (Cosine < 0.80)
rules_summary.append(eval_rule(
    "5. Đa tín hiệu thích ứng: (BM25 == 0 VÀ Cosine < 0.84) HOẶC Cosine < 0.80",
    lambda r: ((r['top1_bm25'] == 0) and (r['top1_cos'] < 0.84)) or (r['top1_cos'] < 0.80)
))

with open('tests/ood_rules_evaluation.json', 'w', encoding='utf-8') as f:
    json.dump(rules_summary, f, ensure_ascii=False, indent=2)
