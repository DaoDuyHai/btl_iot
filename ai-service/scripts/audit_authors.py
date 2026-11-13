import os
import pandas as pd

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')
vc = df['Author'].value_counts()
print("TOP AUTHORS BY COUNT:")
print("-" * 50)
for author, count in vc.head(25).items():
    cats = df[df['Author'] == author]['Category'].value_counts().to_dict()
    sample_titles = df[df['Author'] == author]['Title'].head(3).tolist()
    print(f"\n{author}: {count} sách")
    print(f"  Phân bố Category: {cats}")
    print(f"  Mẫu tựa sách: {sample_titles}")
