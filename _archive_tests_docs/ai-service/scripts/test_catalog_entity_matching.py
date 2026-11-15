import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.query_understanding import QueryAnalyzer, strip_accents

# Load catalog
df = pd.read_csv('ai-service/dataset/books_enriched.csv')

# Extract all unique valid authors and base titles
valid_authors = [a for a in df['valid_author'].dropna().unique() if a.strip()]
titles = df['Title'].unique().tolist()

print(f"Tổng số tác giả hợp lệ trong catalog: {len(valid_authors)}")
print(f"Tổng số tựa sách trong catalog: {len(titles)}")
