import sys
import os
import re
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")

def find_books(pattern, cols=['Title', 'Author', 'Category', 'Subcategory', 'Keywords', 'Description']):
    matches = []
    regex = re.compile(pattern, re.IGNORECASE)
    for idx, row in df.iterrows():
        combined = " ".join([str(row[c]) for c in cols])
        if regex.search(combined):
            matches.append(row)
    return pd.DataFrame(matches)

print("=== REAL AI BOOKS ===")
res_ai = find_books(r'\b(trí tuệ nhân tạo|artificial intelligence|học máy|machine learning|deep learning)\b')
print(f"Found {len(res_ai)} books.")
for _, r in res_ai.head(5).iterrows():
    print(f"- [{r['Book_ID']}] {r['Title']} | {r['Author']} | {r['Category']}")

print("\n=== REAL PARENTING / PSYCHOLOGY BOOKS ===")
res_parent = find_books(r'\b(nuôi dạy con|cha mẹ|phụ huynh|dạy con)\b')
print(f"Found {len(res_parent)} books.")
for _, r in res_parent.head(5).iterrows():
    print(f"- [{r['Book_ID']}] {r['Title']} | {r['Author']} | {r['Category']}")

print("\n=== REAL BUSINESS / STARTUP BOOKS ===")
res_biz = find_books(r'\b(kinh doanh|khởi nghiệp|doanh nghiệp|làm giàu)\b')
print(f"Found {len(res_biz)} books.")
for _, r in res_biz.head(5).iterrows():
    print(f"- [{r['Book_ID']}] {r['Title']} | {r['Author']} | {r['Category']}")

print("\n=== REAL ENGLISH BOOKS ===")
res_eng = find_books(r'\b(tiếng anh|english|ielts|toeic)\b')
print(f"Found {len(res_eng)} books.")
for _, r in res_eng.head(5).iterrows():
    print(f"- [{r['Book_ID']}] {r['Title']} | {r['Author']} | {r['Category']}")

print("\n=== JAVA / PROGRAMMING BOOKS ===")
res_prog = find_books(r'\b(lập trình|thuật toán|code|c\+\+|java|python)\b')
print(f"Found {len(res_prog)} books.")
for _, r in res_prog.head(5).iterrows():
    print(f"- [{r['Book_ID']}] {r['Title']} | {r['Author']} | {r['Category']}")
