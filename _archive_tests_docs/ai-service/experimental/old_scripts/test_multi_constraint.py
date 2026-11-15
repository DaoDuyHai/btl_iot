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

print("[*] Khởi tạo các engine tìm kiếm cho kiểm thử Multi-Constraint...")
df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
work_mapping = get_work_catalog(df)

embedding_engine = EmbeddingEngine()
embeddings, book_ids = embedding_engine.get_or_build_embeddings(df)

bm25_engine = BM25SearchEngine(df, work_mapping=work_mapping)
semantic_engine = SemanticSearchEngine(df, embedding_engine, embeddings, book_ids, work_mapping=work_mapping)
hybrid_engine = HybridSearchEngine(bm25_engine, semantic_engine, k=60)

# Định nghĩa các truy vấn kiểm thử đa điều kiện (Multi-Constraint)
# Mỗi truy vấn có:
# - query: câu hỏi
# - constraints: các điều kiện cụ thể
# - full_match_criteria: điều kiện để một cuốn sách thỏa mãn HOÀN TOÀN
# - partial_match_criteria: điều kiện chỉ thỏa mãn 1 phần
multi_constraint_tests = [
    {
        "id": "MC01",
        "query": "Sách Python dành cho người mới bắt đầu",
        "constraints": ["Chủ đề: Lập trình Python", "Đối tượng: Người mới bắt đầu / Cơ bản / Nhập môn"],
        "filter_full": lambda r: ("python" in str(r['Title']).lower() or "python" in str(r['Keywords']).lower() or "python" in str(r['Description']).lower()) and any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["cơ bản", "mới bắt đầu", "nhập môn", "căn bản", "tự học"]),
        "filter_topic_only": lambda r: "python" in (str(r['Title']) + " " + str(r['Keywords']) + " " + str(r['Description'])).lower()
    },
    {
        "id": "MC02",
        "query": "Sách của Nguyễn Nhật Ánh viết về tuổi học trò",
        "constraints": ["Tác giả: Nguyễn Nhật Ánh", "Chủ đề: Tuổi học trò / Tuổi thơ"],
        "filter_full": lambda r: "nguyễn nhật ánh" in str(r['Author']).lower() and any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["tuổi thơ", "học trò", "nhớ", "hàng xóm", "mùa hè", "đi qua hoa cúc", "mắt biếc", "bàn có năm chỗ ngồi", "kính vạn hoa", "cô gái đến từ hôm qua", "vé đi tuổi thơ"]),
        "filter_author_only": lambda r: "nguyễn nhật ánh" in str(r['Author']).lower(),
        "filter_topic_only": lambda r: any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["tuổi học trò", "tuổi thơ"]) and "nguyễn nhật ánh" not in str(r['Author']).lower()
    },
    {
        "id": "MC03",
        "query": "Sách tiếng Anh về trí tuệ nhân tạo",
        "constraints": ["Chủ đề: Trí tuệ nhân tạo (AI)", "Đặc điểm: Tiếng Anh / Ứng dụng tiếng Anh"],
        "filter_full": lambda r: any(w in (str(r['Title']) + " " + str(r['Keywords']) + " " + str(r['Description'])).lower() for w in ["ai", "trí tuệ nhân tạo"]) and any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["tiếng anh", "english"]),
        "filter_topic_only": lambda r: any(w in (str(r['Title']) + " " + str(r['Keywords']) + " " + str(r['Description'])).lower() for w in ["ai", "trí tuệ nhân tạo"])
    },
    {
        "id": "MC04",
        "query": "Sách lập trình Java có ví dụ thực hành",
        "constraints": ["Chủ đề: Lập trình Java", "Nội dung: Có ví dụ / Bài tập / Thực hành"],
        "filter_full": lambda r: "java" in (str(r['Title']) + " " + str(r['Keywords']) + " " + str(r['Description'])).lower() and any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["thực hành", "bài tập", "bài toán", "dự án", "thuật toán"]),
        "filter_topic_only": lambda r: "java" in (str(r['Title']) + " " + str(r['Keywords']) + " " + str(r['Description'])).lower()
    },
    {
        "id": "MC05",
        "query": "Sách về tâm lý trẻ em dành cho phụ huynh",
        "constraints": ["Chủ đề: Tâm lý trẻ em / Nuôi dạy con", "Đối tượng: Cha mẹ / Phụ huynh"],
        "filter_full": lambda r: any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["nuôi dạy con", "trẻ em", "con trẻ", "con cái"]) and any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["cha mẹ", "phụ huynh", "gia đình"]),
        "filter_topic_only": lambda r: any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["tâm lý", "trẻ em"])
    },
    {
        "id": "MC06",
        "query": "Sách kinh doanh dành cho người chưa có kinh nghiệm",
        "constraints": ["Lĩnh vực: Kinh doanh / Khởi nghiệp", "Đối tượng: Người chưa có kinh nghiệm / Mới bắt đầu"],
        "filter_full": lambda r: any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["kinh doanh", "khởi nghiệp", "doanh nghiệp"]) and any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["bắt đầu", "cơ bản", "nhập môn", "từ con số 0", "chưa có kinh nghiệm", "vỡ lòng", "đầu tiên"]),
        "filter_topic_only": lambda r: any(w in (str(r['Title']) + " " + str(r['Description'])).lower() for w in ["kinh doanh", "khởi nghiệp"])
    }
]

# Tìm ground truth thực tế trong dataframe
results = []
for tc in multi_constraint_tests:
    query = tc['query']
    full_matches = []
    topic_matches = []
    author_matches = []
    
    for _, row in df.iterrows():
        bid = str(row['Book_ID'])
        if tc.get('filter_full') and tc['filter_full'](row):
            full_matches.append(bid)
        if tc.get('filter_topic_only') and tc['filter_topic_only'](row):
            topic_matches.append(bid)
        if tc.get('filter_author_only') and tc['filter_author_only'](row):
            author_matches.append(bid)
            
    print(f"\n==========================================")
    print(f"[{tc['id']}] Truy vấn: '{query}'")
    print(f"Ràng buộc: {tc['constraints']}")
    print(f"Tổng sách thỏa mãn ĐẦY ĐỦ các điều kiện: {len(full_matches)} cuốn")
    if len(full_matches) > 0:
        sample_bids = full_matches[:3]
        samples = df[df['Book_ID'].isin(sample_bids)][['Book_ID', 'Title', 'Author']].to_dict(orient='records')
        print(f"Ví dụ sách thỏa mãn đầy đủ: {samples}")
        
    # Chạy BM25, Semantic, Hybrid
    bm25_res = bm25_engine.search(query, top_k=5)
    sem_res = semantic_engine.search(query, top_k=5)
    hyb_res = hybrid_engine.search(query, top_k=5, fetch_k=200)
    
    def evaluate_res(res_list):
        hits_full = [r for r in res_list if r['book_id'] in full_matches]
        hits_topic = [r for r in res_list if r['book_id'] in topic_matches]
        top1_is_full = res_list[0]['book_id'] in full_matches if res_list else False
        top1_title = res_list[0]['title'] if res_list else "None"
        top1_author = res_list[0]['author'] if res_list else "None"
        return {
            "top1_title": top1_title,
            "top1_author": top1_author,
            "top1_is_full": top1_is_full,
            "full_in_top5": len(hits_full),
            "topic_in_top5": len(hits_topic),
            "top5_titles": [f"[{r['book_id']}] {r['title']} ({r['author']})" for r in res_list]
        }
        
    bm25_eval = evaluate_res(bm25_res)
    sem_eval = evaluate_res(sem_res)
    hyb_eval = evaluate_res(hyb_res)
    
    print(f"--- KẾT QUẢ TOP 1 ---")
    print(f"BM25    : {bm25_eval['top1_title']} ({bm25_eval['top1_author']}) | Thỏa mãn đầy đủ? {bm25_eval['top1_is_full']}")
    print(f"Semantic: {sem_eval['top1_title']} ({sem_eval['top1_author']}) | Thỏa mãn đầy đủ? {sem_eval['top1_is_full']}")
    print(f"Hybrid  : {hyb_eval['top1_title']} ({hyb_eval['top1_author']}) | Thỏa mãn đầy đủ? {hyb_eval['top1_is_full']}")
    
    results.append({
        "id": tc['id'],
        "query": query,
        "constraints": tc['constraints'],
        "total_full_matches": len(full_matches),
        "total_topic_matches": len(topic_matches),
        "bm25": bm25_eval,
        "semantic": sem_eval,
        "hybrid": hyb_eval
    })

os.makedirs("tests", exist_ok=True)
with open("tests/multi_constraint_eval.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu kết quả kiểm thử Multi-Constraint vào tests/multi_constraint_eval.json")
