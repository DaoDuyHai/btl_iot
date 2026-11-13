import os
import re
import pandas as pd

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')

def check_author_relevance(author, cat):
    subset = df[df['Author'] == author]
    print(f"\n======================================")
    print(f"KIỂM TRA TÁC GIẢ: {author} ({len(subset)} sách)")
    print(f"======================================")
    
    # Kiểm tra xem tên tác giả có xuất hiện trong Title hoặc Description không
    has_mention = 0
    mentions = []
    for _, row in subset.iterrows():
        title = str(row['Title']).lower()
        desc = str(row['Description']).lower()
        # Chuẩn hóa tên để tìm
        author_tokens = [t.lower() for t in author.split() if len(t) > 2]
        if any(tok in title for tok in author_tokens) or any(tok in desc for tok in author_tokens):
            has_mention += 1
            mentions.append(row['Title'])
            
    print(f"Số sách thực sự có liên quan/nhắc đến {author}: {has_mention} / {len(subset)}")
    if mentions:
        print(f"Ví dụ sách có nhắc đến: {mentions[:5]}")

for a in ["Stephen Hawking", "Daniel Kahneman", "Nguyễn Hiến Lê", "Alpha Books", "NXB Kim Đồng", "Nhiều tác giả", "WeupBooks"]:
    check_author_relevance(a, None)
