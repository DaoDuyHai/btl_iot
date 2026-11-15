import os
import sys
import io
import time
import json
import psutil
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.work_mapping import get_work_catalog
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SEED = 42
np.random.seed(SEED)

def calculate_work_metrics(retrieved_wids: list, ground_truth_wids: list):
    """
    Tính chỉ số tìm kiếm tại cấp độ work_id:
    - Hit@1: = 1 nếu top 1 là sách đúng
    - Hit@5: = 1 nếu có ít nhất 1 sách đúng trong top 5
    - Hit@10: = 1 nếu có ít nhất 1 sách đúng trong top 10
    - Recall@5: tỷ lệ số lượng work_id đúng lấy được trong top 5 / tổng số work_id đúng
    - Recall@10: tỷ lệ số lượng work_id đúng lấy được trong top 10 / tổng số work_id đúng
    - MRR: 1 / rank xuất hiện đầu tiên của work_id đúng
    - nDCG@10: chuẩn hóa điểm chiết khấu độ lợi tích lũy
    """
    if not ground_truth_wids:
        return {"hit@1": 0.0, "hit@5": 0.0, "hit@10": 0.0, "recall@5": 0.0, "recall@10": 0.0, "mrr": 0.0, "ndcg@10": 0.0}
        
    gt_set = set(ground_truth_wids)
    top1 = retrieved_wids[:1]
    top5 = retrieved_wids[:5]
    top10 = retrieved_wids[:10]
    
    hits_1 = set(top1).intersection(gt_set)
    hits_5 = set(top5).intersection(gt_set)
    hits_10 = set(top10).intersection(gt_set)
    
    hit_1 = 1.0 if len(hits_1) > 0 else 0.0
    hit_5 = 1.0 if len(hits_5) > 0 else 0.0
    hit_10 = 1.0 if len(hits_10) > 0 else 0.0
    
    recall_5 = len(hits_5) / len(gt_set)
    recall_10 = len(hits_10) / len(gt_set)
    
    # MRR
    mrr = 0.0
    for rank, wid in enumerate(top10, 1):
        if wid in gt_set:
            mrr = 1.0 / rank
            break
            
    # nDCG@10
    dcg = 0.0
    for rank, wid in enumerate(top10, 1):
        rel = 1.0 if wid in gt_set else 0.0
        dcg += rel / np.log2(rank + 1)
        
    idcg = 0.0
    for rank in range(1, min(len(gt_set), 10) + 1):
        idcg += 1.0 / np.log2(rank + 1)
    ndcg = (dcg / idcg) if idcg > 0 else 0.0
    
    return {
        "hit@1": hit_1,
        "hit@5": hit_5,
        "hit@10": hit_10,
        "recall@5": recall_5,
        "recall@10": recall_10,
        "mrr": mrr,
        "ndcg@10": ndcg
    }

def bootstrap_ci(values, n_boot=1000, ci=95):
    """Tính 95% Confidence Interval bằng Non-parametric Bootstrap."""
    if len(values) == 0:
        return 0.0, 0.0, 0.0
    values = np.array(values)
    means = []
    n = len(values)
    for _ in range(n_boot):
        sample = np.random.choice(values, size=n, replace=True)
        means.append(np.mean(sample))
    lower = np.percentile(means, (100 - ci) / 2)
    upper = np.percentile(means, 100 - (100 - ci) / 2)
    return float(np.mean(values)), float(lower), float(upper)

def paired_bootstrap_test(vals_a, vals_b, n_boot=1000):
    """Kiểm định Bootstrap bắt cặp (Paired Bootstrap Hypothesis Test)."""
    vals_a = np.array(vals_a)
    vals_b = np.array(vals_b)
    obs_diff = np.mean(vals_a) - np.mean(vals_b)
    diffs = []
    n = len(vals_a)
    for _ in range(n_boot):
        idx = np.random.choice(n, size=n, replace=True)
        diffs.append(np.mean(vals_a[idx]) - np.mean(vals_b[idx]))
    p_val = np.mean(np.array(diffs) <= 0) if obs_diff > 0 else np.mean(np.array(diffs) >= 0)
    return float(obs_diff), float(p_val)
