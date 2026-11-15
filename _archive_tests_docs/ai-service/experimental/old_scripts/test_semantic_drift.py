import sys
import os
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

print("[*] Khởi tạo các engine tìm kiếm cho kiểm thử Semantic Drift & Từ đa nghĩa...")
df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
work_mapping = get_work_catalog(df)

embedding_engine = EmbeddingEngine()
embeddings, book_ids = embedding_engine.get_or_build_embeddings(df)

bm25_engine = BM25SearchEngine(df, work_mapping=work_mapping)
semantic_engine = SemanticSearchEngine(df, embedding_engine, embeddings, book_ids, work_mapping=work_mapping)
hybrid_engine = HybridSearchEngine(bm25_engine, semantic_engine, k=60)

# Danh sách kiểm thử Semantic Drift và Từ đa nghĩa
drift_test_cases = [
    {
        "id": "SD01",
        "case": "Python (Lập trình vs Loài trăn)",
        "query": "Sách về loài trăn khổng lồ săn mồi trong rừng nhiệt đới",
        "intended_domain": "Sinh học / Động vật hoang dã",
        "expected_drift_trap": "Sách lập trình Python (Category: Công nghệ thông tin)",
        "drift_check": lambda r: "công nghệ thông tin" in str(r['category']).lower() or "lập trình" in str(r['title']).lower()
    },
    {
        "id": "SD02",
        "case": "Java (Lập trình vs Địa danh Đảo Java)",
        "query": "Văn hóa và lịch sử vùng đảo Java Indonesia",
        "intended_domain": "Lịch sử – Văn hóa / Địa lý du lịch",
        "expected_drift_trap": "Sách lập trình Java (Category: Công nghệ thông tin)",
        "drift_check": lambda r: "công nghệ thông tin" in str(r['category']).lower() or "lập trình" in str(r['title']).lower()
    },
    {
        "id": "SD03",
        "case": "Spring Boot (Framework lập trình vs Mùa xuân / Đôi giày)",
        "query": "Khởi đầu mùa xuân tươi đẹp và tràn đầy sức sống",
        "intended_domain": "Văn học / Thơ ca / Kỹ năng sống",
        "expected_drift_trap": "Sách kỹ thuật công nghệ",
        "drift_check": lambda r: "công nghệ thông tin" in str(r['category']).lower()
    },
    {
        "id": "SD04",
        "case": "Ove (Nhân vật tiểu thuyết vs Trầm cảm / Tự sát)",
        "query": "ông già khó tính cộc cằn nhưng có trái tim ấm áp luôn muốn tự tử",
        "intended_domain": "Tiểu thuyết Người Đàn Ông Mang Tên Ove (W0001 / B0001)",
        "expected_drift_trap": "Sách tâm lý học trầm cảm, y khoa trị liệu",
        "target_book": "Người Đàn Ông Mang Tên Ove",
        "drift_check": lambda r: "người đàn ông mang tên ove" not in str(r['title']).lower() and "tâm lý" in str(r['category']).lower()
    },
    {
        "id": "SD05",
        "case": "AI (Trí tuệ nhân tạo vs Từ cảm thán / Ai đó)",
        "query": "Có ai cùng tôi đi qua những năm tháng thanh xuân cô đơn",
        "intended_domain": "Văn học – Tiểu thuyết / Tản văn tình cảm",
        "expected_drift_trap": "Sách Trí tuệ nhân tạo AI (Category: Công nghệ thông tin)",
        "drift_check": lambda r: "công nghệ thông tin" in str(r['category']).lower() or "ai" in str(r['title']).lower().split()
    },
    {
        "id": "SD06",
        "case": "Tên riêng nước ngoài ít dữ liệu: Fredrik Backman",
        "query": "Tác phẩm của tác giả Fredrik Backman",
        "intended_domain": "Sách của Fredrik Backman (Người Đàn Ông Mang Tên Ove, Anxious People, Beartown)",
        "expected_drift_trap": "Sách dịch giả / tiểu thuyết nước ngoài khác",
        "drift_check": lambda r: "fredrik backman" not in str(r['author']).lower()
    }
]

results = []
for tc in drift_test_cases:
    query = tc['query']
    print(f"\n==========================================")
    print(f"[{tc['id']}] Case: {tc['case']}")
    print(f"Truy vấn: '{query}'")
    print(f"Miền mong đợi: {tc['intended_domain']}")
    print(f"Bẫy trôi dạt ngữ nghĩa: {tc['expected_drift_trap']}")
    
    bm25_res = bm25_engine.search(query, top_k=5)
    sem_res = semantic_engine.search(query, top_k=5)
    hyb_res = hybrid_engine.search(query, top_k=5, fetch_k=200)
    
    def analyze_drift(res_list):
        if not res_list:
            return {"top1": "None", "score": 0.0, "has_drift_top1": False, "drift_count_top5": 0, "titles": []}
        top1 = res_list[0]
        has_drift_top1 = tc['drift_check'](top1)
        drift_count = sum(1 for r in res_list if tc['drift_check'](r))
        return {
            "top1": f"[{top1['book_id']}] {top1['title']} ({top1['author']}) - {top1['category']}",
            "score": float(top1['score']),
            "has_drift_top1": bool(has_drift_top1),
            "drift_count_top5": int(drift_count),
            "titles": [f"[{r['book_id']}] {r['title']} ({r['category']}) [Score: {r['score']:.4f}]" for r in res_list]
        }
        
    bm25_analysis = analyze_drift(bm25_res)
    sem_analysis = analyze_drift(sem_res)
    hyb_analysis = analyze_drift(hyb_res)
    
    print(f"BM25 Top 1    : {bm25_analysis['top1']} | Drift Top 1? {bm25_analysis['has_drift_top1']}")
    print(f"Semantic Top 1: {sem_analysis['top1']} | Drift Top 1? {sem_analysis['has_drift_top1']}")
    print(f"Hybrid Top 1  : {hyb_analysis['top1']} | Drift Top 1? {hyb_analysis['has_drift_top1']}")
    
    results.append({
        "id": tc['id'],
        "case": tc['case'],
        "query": query,
        "intended_domain": tc['intended_domain'],
        "expected_drift_trap": tc['expected_drift_trap'],
        "bm25": bm25_analysis,
        "semantic": sem_analysis,
        "hybrid": hyb_analysis
    })

os.makedirs("tests", exist_ok=True)
with open("tests/semantic_drift_eval.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu kết quả kiểm thử Semantic Drift vào tests/semantic_drift_eval.json")
