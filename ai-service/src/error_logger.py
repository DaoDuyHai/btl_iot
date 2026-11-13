# d:\TrainAI\src\error_logger.py
import os
import json
from datetime import datetime

LOG_FILE = "search_errors.jsonl"

def log_search_interaction(query: str, ground_truth: list, top_results: list, error_label: str = None, log_dir: str = "logs"):
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, LOG_FILE)
    
    retrieved_ids = [r['book_id'] for r in top_results]
    ranks = {}
    for target in ground_truth:
        if target in retrieved_ids:
            ranks[target] = retrieved_ids.index(target) + 1
        else:
            ranks[target] = -1 # Không tìm thấy trong top_k
            
    record = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "ground_truth": ground_truth,
        "retrieved_ids": retrieved_ids,
        "ranks": ranks,
        "error_label": error_label or ("Thành công" if any(r > 0 for r in ranks.values()) else "Không tìm thấy kết quả phù hợp")
    }
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
