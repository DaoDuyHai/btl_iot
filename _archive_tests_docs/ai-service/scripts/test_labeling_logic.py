import re
import pandas as pd
from collections import Counter

df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')
print(f"Tổng số sách: {len(df)}")
