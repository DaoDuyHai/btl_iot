import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.passage_builder import build_passage, clean_field
from src.bm25_search import BM25SearchEngine, tokenize_vietnamese
from src.work_mapping import get_work_catalog, clean_str

print("======================================================================")
print("TESTING NULL/NAN FIX VERIFICATION (6 REQUIRED SCENARIOS)")
print("======================================================================")

test_records = [
    {
        "case_name": "Case 1: Author bị None",
        "Book_ID": "T01",
        "Title": "Sách Toán Học Cao Cấp",
        "Author": None,
        "Category": "Khoa học – Công nghệ",
        "Subcategory": "Toán học",
        "Description": "Giáo trình toán cao cấp đại học dành cho sinh viên.",
        "Keywords": "toán, giải tích",
        "Shelf": "A", "Floor": 1, "Position": "A1-01"
    },
    {
        "case_name": "Case 2: Description bị NaN",
        "Book_ID": "T02",
        "Title": "Lập Trình Go Căn Bản",
        "Author": "Nguyễn Văn An",
        "Category": "Công nghệ thông tin",
        "Subcategory": "Lập trình",
        "Description": np.nan,
        "Keywords": "golang, lập trình",
        "Shelf": "B", "Floor": 2, "Position": "B2-01"
    },
    {
        "case_name": "Case 3: Category và Subcategory bị thiếu (NaN/None)",
        "Book_ID": "T03",
        "Title": "Hạt Giống Tâm Hồn",
        "Author": "Nhiều tác giả",
        "Category": np.nan,
        "Subcategory": None,
        "Description": "Những câu chuyện truyền cảm hứng sống ý nghĩa.",
        "Keywords": "tâm hồn, cảm hứng",
        "Shelf": "C", "Floor": 1, "Position": "C1-01"
    },
    {
        "case_name": "Case 4: Nhiều trường cùng thiếu (Chỉ có Title)",
        "Book_ID": "T04",
        "Title": "Cuốn Sách Kỳ Bí",
        "Author": None,
        "Category": np.nan,
        "Subcategory": None,
        "Description": np.nan,
        "Keywords": None,
        "Shelf": None, "Floor": np.nan, "Position": None
    },
    {
        "case_name": "Case 5: Một dòng đầy đủ dữ liệu",
        "Book_ID": "T05",
        "Title": "Lập Trình Python Chuyên Nghiệp",
        "Author": "Lê Văn Bình",
        "Category": "Công nghệ thông tin",
        "Subcategory": "Phần mềm",
        "Description": "Hướng dẫn xây dựng kiến trúc phần mềm với Python.",
        "Keywords": "python, kiến trúc",
        "Shelf": "D", "Floor": 3, "Position": "D3-05"
    },
    {
        "case_name": "Case 6: Một dòng có chuỗi rỗng và chuỗi 'nan'/'none'",
        "Book_ID": "T06",
        "Title": "Sách Thử Chuỗi Rác",
        "Author": "   ",
        "Category": "nan",
        "Subcategory": "None",
        "Description": "null",
        "Keywords": "",
        "Shelf": "E", "Floor": 1, "Position": "E1-01"
    }
]

df_test = pd.DataFrame(test_records)

# 1. Kiểm tra build_passage
print("\n--- 1. KIỂM TRA BUILD_PASSAGE ---")
all_clean = True
for idx, r in df_test.iterrows():
    c_name = r['case_name']
    p = build_passage(r)
    toks = tokenize_vietnamese(p)
    has_nan = 'nan' in toks
    has_none = 'none' in toks
    has_null = 'null' in toks
    
    status = "PASS" if not (has_nan or has_none or has_null) else "FAIL (LEAKAGE DETECTED)"
    if has_nan or has_none or has_null:
        all_clean = False
        
    print(f"[{status}] {c_name}:")
    print(f"       Passage: {repr(p)}")
    print(f"       Tokens : {toks}")
    print(f"       Có 'nan'? {has_nan} | Có 'none'? {has_none} | Có 'null'? {has_null}")

# 2. Kiểm tra Work Catalog
print("\n--- 2. KIỂM TRA WORK CATALOG ---")
catalog = get_work_catalog(df_test)
catalog_clean = True
for wid, info in catalog.items():
    author = info['author']
    cat = info['category']
    desc = info['description']
    has_nan_val = any(v.lower() in ['nan', 'none', 'null'] for v in [author, cat, desc] if v)
    if has_nan_val:
        catalog_clean = False
    print(f"[{'PASS' if not has_nan_val else 'FAIL'}] {wid} ('{info['base_title']}'): Author='{author}', Cat='{cat}', Desc='{desc}'")

# 3. Kiểm tra BM25 Corpus
print("\n--- 3. KIỂM TRA BM25 CORPUS INDEX ---")
bm25_test = BM25SearchEngine(df_test, work_mapping=catalog)
bm25_clean = True
for idx, doc_toks in enumerate(bm25_test.corpus):
    has_nan = 'nan' in doc_toks
    has_none = 'none' in doc_toks
    has_null = 'null' in doc_toks
    if has_nan or has_none or has_null:
        bm25_clean = False
        print(f"[FAIL] Doc {idx} có token rác: {[t for t in doc_toks if t in ['nan', 'none', 'null']]}")
    else:
        print(f"[PASS] Doc {idx} hoàn toàn sạch ({len(doc_toks)} tokens).")

print("\n" + "=" * 70)
print(f"TỔNG KẾT KIỂM THỬ SỬA LỖI:")
print(f"- Passage Builder không còn token 'nan'/'none': {all_clean}")
print(f"- Work Catalog không còn chuỗi 'nan'/'none'    : {catalog_clean}")
print(f"- BM25 Corpus không còn token rác             : {bm25_clean}")
print("======================================================================")
