# d:\TrainAI\src\evaluation.py
import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List

def calculate_metrics(retrieved_ids: List[str], ground_truth: List[str]) -> Dict[str, float]:
    """
    Tính các chỉ số:
    - Hit@5: = 1 nếu có ít nhất 1 ground_truth xuất hiện trong top 5, ngược lại = 0.
    - Hit@10: = 1 nếu có ít nhất 1 ground_truth xuất hiện trong top 10, ngược lại = 0.
    - Recall@5: tỷ lệ số lượng ground_truth lấy được trong top 5 trên tổng số ground_truth.
    - Recall@10: tỷ lệ số lượng ground_truth lấy được trong top 10 trên tổng số ground_truth.
    - MRR (Mean Reciprocal Rank): 1 / thứ hạng xuất hiện đầu tiên của ground_truth trong danh sách.
    """
    if not ground_truth:
        return {"hit@5": 0.0, "hit@10": 0.0, "recall@5": 0.0, "recall@10": 0.0, "mrr": 0.0}
        
    top5 = retrieved_ids[:5]
    top10 = retrieved_ids[:10]
    
    gt_set = set(ground_truth)
    hits_5 = set(top5).intersection(gt_set)
    hits_10 = set(top10).intersection(gt_set)
    
    hit_at_5 = 1.0 if len(hits_5) > 0 else 0.0
    hit_at_10 = 1.0 if len(hits_10) > 0 else 0.0
    recall_at_5 = len(hits_5) / len(gt_set)
    recall_at_10 = len(hits_10) / len(gt_set)
    
    # MRR
    mrr = 0.0
    for rank, bid in enumerate(top10, 1):
        if bid in gt_set:
            mrr = 1.0 / rank
            break
            
    return {
        "hit@5": hit_at_5,
        "hit@10": hit_at_10,
        "recall@5": recall_at_5,
        "recall@10": recall_at_10,
        "mrr": mrr
    }

def evaluate_all_engines(test_csv_path: str, bm25_engine, semantic_engine, hybrid_engine) -> pd.DataFrame:
    test_df = pd.read_csv(test_csv_path, encoding='utf-8-sig')
    
    engines = {
        "BM25": bm25_engine,
        "Semantic (E5)": semantic_engine,
        "Hybrid (RRF)": hybrid_engine
    }
    
    summary = {name: {"hit@5": [], "hit@10": [], "recall@5": [], "recall@10": [], "mrr": []} for name in engines}
    
    for _, row in test_df.iterrows():
        query = str(row['Query'])
        gt_raw = str(row['Expected_Book_IDs'])
        ground_truth = [bid.strip() for bid in gt_raw.split(';') if bid.strip()]
        if not ground_truth:
            continue
            
        for name, engine in engines.items():
            results = engine.search(query, top_k=10)
            retrieved_ids = [r['book_id'] for r in results]
            metrics = calculate_metrics(retrieved_ids, ground_truth)
            for m_k, m_v in metrics.items():
                summary[name][m_k].append(m_v)
                
    # Tính trung bình cộng
    report_rows = []
    for name in engines:
        row_data = {
            "Phương pháp": name,
            "Hit Rate@5": np.mean(summary[name]["hit@5"]),
            "Hit Rate@10": np.mean(summary[name]["hit@10"]),
            "Recall@5": np.mean(summary[name]["recall@5"]),
            "Recall@10": np.mean(summary[name]["recall@10"]),
            "MRR": np.mean(summary[name]["mrr"])
        }
        report_rows.append(row_data)
        
    report_df = pd.DataFrame(report_rows)
    return report_df

def plot_comparison_chart(report_df: pd.DataFrame, save_path: str = "static/benchmark_comparison.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    metrics = ["Hit Rate@5", "Hit Rate@10", "Recall@5", "Recall@10", "MRR"]
    methods = report_df["Phương pháp"].tolist()
    
    x = np.arange(len(metrics))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#4A90E2', '#50E3C2', '#F5A623']
    for idx, method in enumerate(methods):
        values = report_df[report_df["Phương pháp"] == method][metrics].values[0]
        ax.bar(x + idx * width, values, width, label=method, color=colors[idx % len(colors)])
        
    ax.set_ylabel('Điểm số (0.0 - 1.0)')
    ax.set_title('So Sánh Hiệu Năng: BM25 vs Semantic Search vs Hybrid (RRF)')
    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1.1)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[+] Đã lưu biểu đồ so sánh kết quả tại: {save_path}")
