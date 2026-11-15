import sys
import os
import json
import hashlib
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset
from src.passage_builder import build_passage
from src.cache_manager import compute_hash

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")

with open("embeddings/metadata.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

cached_hashes = meta.get("item_hashes", {})
mismatches = 0
for _, r in df.iterrows():
    bid = r['Book_ID']
    p = build_passage(r)
    h = compute_hash(p)
    if cached_hashes.get(bid) != h:
        mismatches += 1

print(f"Total books: {len(df)}")
print(f"Passage hash mismatches: {mismatches}")
if mismatches == 0:
    print("[+] Toàn bộ 3.000 passage của kho sách sạch hoàn toàn khớp 100% với cache hiện tại!")
else:
    print(f"[*] Có {mismatches} passage bị thay đổi hash.")
