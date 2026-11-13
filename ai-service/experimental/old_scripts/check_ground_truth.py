import json
import pandas as pd
import numpy as np

df = pd.read_csv('dataset/cleaned_books_dataset.csv')

print("--- KIỂM TRA GROUND TRUTH VÀ SỐ LƯỢNG SÁCH PHÙ HỢP ---")

# Kiểm tra câu tác giả
nna_books = df[df['Author'] == 'Nguyễn Nhật Ánh']
print(f"Số lượng sách của tác giả Nguyễn Nhật Ánh trong kho: {len(nna_books)}")

# Kiểm tra câu chủ đề Trí tuệ nhân tạo
ai_mask = df['Title'].str.contains('Trí Tuệ Nhân Tạo', case=False, na=False) | df['Description'].str.contains('trí tuệ nhân tạo', case=False, na=False)
ai_books = df[ai_mask]
print(f"Số lượng sách liên quan 'Trí tuệ nhân tạo' trong kho: {len(ai_books)}")

# Kiểm tra câu chủ đề Python
python_mask = df['Title'].str.contains('Python', case=False, na=False) | df['Keywords'].str.contains('Python', case=False, na=False)
python_books = df[python_mask]
print(f"Số lượng sách liên quan 'Python' trong kho: {len(python_books)}")

# Kiểm tra câu chủ đề HSK
hsk_mask = df['Title'].str.contains('HSK', case=False, na=False)
hsk_books = df[hsk_mask]
print(f"Số lượng sách liên quan 'HSK' trong kho: {len(hsk_books)}")
