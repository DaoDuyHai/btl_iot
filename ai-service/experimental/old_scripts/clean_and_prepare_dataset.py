import re
import html
import pandas as pd
import numpy as np

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    # Unescape HTML entities (&nbsp;, &amp;, etc.)
    text = html.unescape(text)
    # Replace non-breaking spaces and extra whitespace
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def main():
    print(">>> Loading dataset/books_dataset.csv...")
    df = pd.read_csv('dataset/books_dataset.csv')
    print(f"Original shape: {df.shape}")

    # Clean all string columns
    str_cols = ['Title', 'Author', 'Category', 'Subcategory', 'Description', 'Keywords', 'Publisher', 'Language', 'Shelf', 'Position']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    # Clean Author anomalies
    def fix_author(auth):
        if not auth or auth.lower() in ['', ' ', '&nbsp;', 'none', 'nan']:
            return "Nhiều tác giả"
        if auth.lower() in ['nhieu tac gia', 'nhiều tác giả']:
            return "Nhiều tác giả"
        return auth

    df['Author'] = df['Author'].apply(fix_author)

    # Clean Description disclaimer (Tiki / Fahasa shipping disclaimer)
    disclaimer_pattern = "theo luật hiện hành"
    fixed_desc_count = 0
    for idx, row in df.iterrows():
        desc = row['Description']
        if disclaimer_pattern in desc.lower() or len(desc.split()) < 15:
            # Generate rich contextual description
            kw_cleaned = ", ".join([k.strip() for k in row['Keywords'].split(',') if k.strip() and k.strip().lower() not in ['sách tiếng việt']])
            new_desc = (
                f"Cuốn sách '{row['Title']}' của tác giả {row['Author']}, thuộc thể loại {row['Category']} "
                f"({row['Subcategory']}), do {row['Publisher']} phát hành. Tác phẩm mang đến cho bạn đọc những kiến thức sâu sắc, "
                f"hữu ích xoay quanh các chủ đề: {kw_cleaned}."
            )
            df.at[idx, 'Description'] = new_desc
            fixed_desc_count += 1

    print(f"Fixed {fixed_desc_count} boilerplate/short descriptions.")

    # Validate numbers
    df['Total_Copies'] = pd.to_numeric(df['Total_Copies'], errors='coerce').fillna(1).astype(int)
    df['Available_Copies'] = pd.to_numeric(df['Available_Copies'], errors='coerce').fillna(1).astype(int)
    df['Available_Copies'] = df[['Total_Copies', 'Available_Copies']].min(axis=1)
    df['Publication_Year'] = pd.to_numeric(df['Publication_Year'], errors='coerce').fillna(2023).astype(int)
    df['Floor'] = pd.to_numeric(df['Floor'], errors='coerce').fillna(1).astype(int)

    # Check Book_ID uniqueness
    assert df['Book_ID'].nunique() == len(df), "Book_ID must be unique!"

    # Save cleaned versions
    out_csv = 'dataset/cleaned_books_dataset.csv'
    df.to_csv(out_csv, index=False, encoding='utf-8-sig')
    print(f">>> Cleaned dataset saved to {out_csv} ({len(df)} rows).")

    # Audit summary
    print("\n--- Summary After Cleaning ---")
    print(f"Total Rows: {len(df)}")
    print(f"Unique Titles: {df['Title'].nunique()}")
    print(f"Unique Authors: {df['Author'].nunique()}")
    print(f"Null values:\n{df.isnull().sum()}")

if __name__ == '__main__':
    main()
