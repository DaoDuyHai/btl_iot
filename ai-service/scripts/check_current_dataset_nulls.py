import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
print("Null count per column in cleaned_books_dataset.csv:")
for col in ['Title', 'Author', 'Category', 'Subcategory', 'Description', 'Keywords']:
    null_cnt = df[col].isna().sum()
    nan_str_cnt = (df[col].astype(str).str.lower().isin(['nan', 'none', 'null'])).sum()
    empty_cnt = (df[col].astype(str).str.strip() == '').sum()
    print(f"- {col}: {null_cnt} nulls, {nan_str_cnt} 'nan' strings, {empty_cnt} empty strings")
