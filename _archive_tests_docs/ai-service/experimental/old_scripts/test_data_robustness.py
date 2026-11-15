import sys
import os
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.passage_builder import build_passage
from src.bm25_search import tokenize_vietnamese, tokenize_query_optimized, BM25SearchEngine
from src.work_mapping import extract_base_title, strip_accents, get_work_catalog
from src.embedding import EmbeddingEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine

print("[*] Bắt đầu kiểm thử Dữ liệu đầu vào không hoàn chỉnh & Edge Cases (Hạng mục D)...")

# Tạo DataFrame thử nghiệm độc lập (KHÔNG sửa dữ liệu gốc)
edge_case_records = [
    {
        "test_name": "D1_Missing_Description",
        "Book_ID": "TEST_D1",
        "Title": "Sách Thử Nghiệm Không Mô Tả",
        "Author": "Nguyễn Văn A",
        "Category": "Công nghệ thông tin",
        "Subcategory": "Lập trình",
        "Description": "", # Rỗng
        "Keywords": "python, lập trình",
        "Shelf": "A", "Floor": 1, "Position": "A1-01", "Available_Copies": 1, "Total_Copies": 1
    },
    {
        "test_name": "D2_Missing_Author",
        "Book_ID": "TEST_D2",
        "Title": "Sách Không Có Tác Giả Rõ Ràng",
        "Author": "", # Rỗng
        "Category": "Khoa học – Công nghệ",
        "Subcategory": "Vũ trụ",
        "Description": "Cuốn sách khám phá các hố đen và bí ẩn vũ trụ sâu thẳm.",
        "Keywords": "vũ trụ, thiên văn",
        "Shelf": "B", "Floor": 2, "Position": "B2-01", "Available_Copies": 1, "Total_Copies": 1
    },
    {
        "test_name": "D3_Empty_Title",
        "Book_ID": "TEST_D3",
        "Title": "", # Tiêu đề rỗng
        "Author": "Trần Thị B",
        "Category": "Văn học – Tiểu thuyết",
        "Subcategory": "Tiểu thuyết",
        "Description": "Tác phẩm tiểu thuyết hiện đại kể về cuộc sống đô thị.",
        "Keywords": "văn học, đô thị",
        "Shelf": "C", "Floor": 1, "Position": "C1-01", "Available_Copies": 1, "Total_Copies": 1
    },
    {
        "test_name": "D4_Null_NaN_Fields",
        "Book_ID": "TEST_D4",
        "Title": "Sách Chứa Giá Trị Null",
        "Author": None, # Null
        "Category": np.nan, # NaN
        "Subcategory": None,
        "Description": np.nan,
        "Keywords": None,
        "Shelf": None, "Floor": np.nan, "Position": None, "Available_Copies": np.nan, "Total_Copies": np.nan
    },
    {
        "test_name": "D5_Very_Short_Description",
        "Book_ID": "TEST_D5",
        "Title": "Sách Mô Tả Siêu Ngắn",
        "Author": "Lê Văn C",
        "Category": "Kỹ năng sống – Phát triển bản thân",
        "Subcategory": "Tự lực",
        "Description": "Hay.", # 1 từ
        "Keywords": "kỹ năng",
        "Shelf": "D", "Floor": 3, "Position": "D3-01", "Available_Copies": 2, "Total_Copies": 2
    },
    {
        "test_name": "D6_Near_Duplicate_Title_1",
        "Book_ID": "TEST_D6_1",
        "Title": "Lập Trình Python Cơ Bản",
        "Author": "Phạm Văn D",
        "Category": "Công nghệ thông tin",
        "Subcategory": "Lập trình",
        "Description": "Hướng dẫn cú pháp Python cho người bắt đầu.",
        "Keywords": "python, cơ bản",
        "Shelf": "A", "Floor": 1, "Position": "A1-02", "Available_Copies": 1, "Total_Copies": 1
    },
    {
        "test_name": "D6_Near_Duplicate_Title_2",
        "Book_ID": "TEST_D6_2",
        "Title": "Lập Trình Python Cơ Bản - Tập 2",
        "Author": "Phạm Văn D",
        "Category": "Công nghệ thông tin",
        "Subcategory": "Lập trình",
        "Description": "Nối tiếp phần cơ bản với các bài tập nâng cao.",
        "Keywords": "python, nâng cao",
        "Shelf": "A", "Floor": 1, "Position": "A1-03", "Available_Copies": 1, "Total_Copies": 1
    },
    {
        "test_name": "D7_Special_Characters_HTML_XSS",
        "Book_ID": "TEST_D7",
        "Title": "Sách Hack Não & Ký Tự Lạ: @#$%^&*()_+ <>?!\"'",
        "Author": "Author <script>alert('xss')</script>",
        "Category": "Khoa học & Kỹ thuật 🚀📚",
        "Subcategory": "An toàn thông tin'; DROP TABLE books; --",
        "Description": "Mô tả có HTML: <b>Đậm</b>, <i>Nghiêng</i> &amp; ký hiệu Toán học: $\\int_0^\\infty e^{-x} dx = 1$.",
        "Keywords": "@hack, #cyber, $money, %sale",
        "Shelf": "X#1", "Floor": 99, "Position": "X99-@#$", "Available_Copies": 5, "Total_Copies": 5
    },
    {
        "test_name": "D8_Accented_Vs_Unaccented",
        "Book_ID": "TEST_D8",
        "Title": "tieng viet khong dau hoan toan",
        "Author": "nguyen nhat anh khong dau",
        "Category": "van hoc",
        "Subcategory": "truyen ngan",
        "Description": "day la cuon sach viet bang tieng viet khong he co dau thanh de kiem tra tokenizer.",
        "Keywords": "khong dau, tieng viet",
        "Shelf": "E", "Floor": 2, "Position": "E2-05", "Available_Copies": 1, "Total_Copies": 1
    }
]

df_edge = pd.DataFrame(edge_case_records)

robustness_results = []

# Kiểm tra từng giai đoạn trên tập dữ liệu này:
# 1. Build passage
print("\n--- Giai đoạn 1: Build Passage ---")
passages = []
for idx, row in df_edge.iterrows():
    t_name = row['test_name']
    try:
        p = build_passage(row)
        passages.append(p)
        robustness_results.append({
            "stage": "build_passage",
            "test_case": t_name,
            "status": "SUCCESS",
            "output_preview": p[:80] + "..."
        })
        print(f"[PASS] {t_name}: Build passage thành công.")
    except Exception as e:
        robustness_results.append({
            "stage": "build_passage",
            "test_case": t_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"[FAIL] {t_name}: Lỗi {e}")

# 2. Tokenize (BM25)
print("\n--- Giai đoạn 2: Tokenize (BM25) ---")
for p, t_name in zip(passages, df_edge['test_name']):
    try:
        toks = tokenize_vietnamese(p)
        toks_opt = tokenize_query_optimized(p)
        robustness_results.append({
            "stage": "tokenize",
            "test_case": t_name,
            "status": "SUCCESS",
            "token_count": len(toks),
            "opt_token_count": len(toks_opt)
        })
        print(f"[PASS] {t_name}: Tokenize thành công ({len(toks)} tokens).")
    except Exception as e:
        robustness_results.append({
            "stage": "tokenize",
            "test_case": t_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"[FAIL] {t_name}: Lỗi {e}")

# 3. Work Mapping / Catalog
print("\n--- Giai đoạn 3: Work Catalog Mapping ---")
try:
    edge_catalog = get_work_catalog(df_edge)
    robustness_results.append({
        "stage": "work_catalog",
        "test_case": "ALL_EDGE_CASES",
        "status": "SUCCESS",
        "unique_works_generated": len(edge_catalog)
    })
    print(f"[PASS] Work Catalog sinh thành công: {len(edge_catalog)} works từ {len(df_edge)} bản ghi.")
    for wid, info in edge_catalog.items():
        print(f"       -> {wid}: '{info['base_title']}' ({info['author']}) - Copies: {len(info['copies'])}")
except Exception as e:
    robustness_results.append({
        "stage": "work_catalog",
        "test_case": "ALL_EDGE_CASES",
        "status": "FAILED",
        "error": str(e)
    })
    print(f"[FAIL] Work Catalog lỗi: {e}")

# 4. Embedding Generation
print("\n--- Giai đoạn 4: E5 Embedding Generation ---")
try:
    embedding_engine = EmbeddingEngine()
    emb_edge = embedding_engine.model.encode(passages, normalize_embeddings=True)
    robustness_results.append({
        "stage": "embedding",
        "test_case": "ALL_EDGE_CASES",
        "status": "SUCCESS",
        "embedding_shape": list(emb_edge.shape),
        "norms": [float(np.linalg.norm(v)) for v in emb_edge]
    })
    print(f"[PASS] Embedding thành công: Shape {emb_edge.shape}, L2 norms = {[round(float(n), 4) for n in np.linalg.norm(emb_edge, axis=1)]}")
except Exception as e:
    robustness_results.append({
        "stage": "embedding",
        "test_case": "ALL_EDGE_CASES",
        "status": "FAILED",
        "error": str(e)
    })
    print(f"[FAIL] Embedding lỗi: {e}")

# 5. Khởi tạo Engine tìm kiếm mini và truy vấn thử
print("\n--- Giai đoạn 5: Tìm kiếm thực tế trên Index Edge Case ---")
try:
    bm25_edge = BM25SearchEngine(df_edge, work_mapping=edge_catalog)
    sem_edge = SemanticSearchEngine(df_edge, embedding_engine, emb_edge, list(df_edge['Book_ID']), work_mapping=edge_catalog)
    hyb_edge = HybridSearchEngine(bm25_edge, sem_edge, k=60)
    
    test_queries = [
        "Sách không mô tả",
        "Vũ trụ hố đen",
        "Tiểu thuyết đô thị",
        "Hay",
        "Lập trình Python",
        "alert xss",
        "tieng viet khong dau"
    ]
    
    query_evals = []
    for q in test_queries:
        res = hyb_edge.search(q, top_k=3)
        query_evals.append({
            "query": q,
            "top1": res[0]['title'] if res else "None",
            "top1_score": res[0]['score'] if res else 0.0
        })
        print(f"[PASS] Query '{q}' -> Top 1: '{res[0]['title'] if res else 'None'}'")
        
    robustness_results.append({
        "stage": "search_execution",
        "test_case": "QUERY_RUNS",
        "status": "SUCCESS",
        "queries": query_evals
    })
except Exception as e:
    robustness_results.append({
        "stage": "search_execution",
        "test_case": "QUERY_RUNS",
        "status": "FAILED",
        "error": str(e)
    })
    print(f"[FAIL] Tìm kiếm lỗi: {e}")

with open("tests/data_robustness_eval.json", "w", encoding="utf-8") as f:
    json.dump(robustness_results, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu kết quả kiểm thử dữ liệu đầu vào vào tests/data_robustness_eval.json")
