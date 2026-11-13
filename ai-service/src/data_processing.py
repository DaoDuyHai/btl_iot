# d:\TrainAI\src\data_processing.py
import os
import pandas as pd

REQUIRED_COLUMNS = [
    'Book_ID', 'Title', 'Author', 'Category', 'Subcategory',
    'Description', 'Keywords', 'Publisher', 'Publication_Year',
    'Language', 'Shelf', 'Floor', 'Position', 'Total_Copies', 'Available_Copies'
]

def load_and_verify_dataset(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Không tìm thấy dataset tại {csv_path}")
    
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # Kiểm tra cột bắt buộc
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset thiếu các cột bắt buộc: {missing_cols}")
        
    # Loại bỏ bản ghi có trường thiết yếu rỗng
    essential = ['Book_ID', 'Title', 'Author', 'Category', 'Description']
    initial_len = len(df)
    df = df.dropna(subset=essential)
    
    # Ép kiểu dữ liệu
    df['Book_ID'] = df['Book_ID'].astype(str).str.strip()
    df['Title'] = df['Title'].astype(str).str.strip()
    df['Author'] = df['Author'].astype(str).str.strip()
    df['Category'] = df['Category'].astype(str).str.strip()
    df['Subcategory'] = df['Subcategory'].astype(str).str.strip()
    df['Description'] = df['Description'].astype(str).str.strip()
    df['Keywords'] = df['Keywords'].astype(str).str.strip()
    df['Publisher'] = df['Publisher'].astype(str).str.strip()
    df['Publication_Year'] = pd.to_numeric(df['Publication_Year'], errors='coerce').fillna(2020).astype(int)
    df['Total_Copies'] = pd.to_numeric(df['Total_Copies'], errors='coerce').fillna(1).astype(int)
    df['Available_Copies'] = pd.to_numeric(df['Available_Copies'], errors='coerce').fillna(1).astype(int)
    
    # Đảm bảo Available_Copies <= Total_Copies
    df['Available_Copies'] = df[['Available_Copies', 'Total_Copies']].min(axis=1)
    
    print(f"[*] Dataset đã xử lý xong: {len(df)}/{initial_len} bản ghi hợp lệ.")
    return df
