import json
import re
import pandas as pd
import numpy as np

# Load cleaned dataset
df = pd.read_csv('dataset/cleaned_books_dataset.csv')
print(f"Total books loaded: {len(df)}")

# Helper to find matching book IDs
def find_books_by_title(title_sub):
    return df[df['Title'].str.contains(title_sub, case=False, na=False)]['Book_ID'].tolist()

def find_books_by_author(auth):
    return df[df['Author'].str.contains(auth, case=False, na=False)]['Book_ID'].tolist()

def find_books_by_kw(keywords, subcats=None, cats=None):
    mask = pd.Series(False, index=df.index)
    for kw in keywords:
        kw_mask = (df['Title'].str.contains(kw, case=False, na=False) |
                   df['Description'].str.contains(kw, case=False, na=False) |
                   df['Keywords'].str.contains(kw, case=False, na=False))
        mask = mask | kw_mask
    if subcats:
        sub_mask = df['Subcategory'].isin(subcats)
        mask = mask & sub_mask
    if cats:
        cat_mask = df['Category'].isin(cats)
        mask = mask & cat_mask
    return df[mask]['Book_ID'].tolist()

# Load the 110 queries from previous script
from scripts.run_comprehensive_evaluation_100 import run_evaluation
# We will inspect how each query should have its full relevant set defined
