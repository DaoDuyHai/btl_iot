import json
import re
import numpy as np
import pandas as pd

print("=" * 70)
print("IN-DEPTH CODE AUDIT: GIAI ĐOẠN 1")
print("=" * 70)

# 1. Dataset & Embedding Alignment
df = pd.read_csv('dataset/cleaned_books_dataset.csv')
with open('embeddings/book_ids.json', 'r', encoding='utf-8') as f:
    cached_ids = json.load(f)
with open('embeddings/metadata.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)
embeddings = np.load('embeddings/embeddings.npy')

print(f"1. Dataset rows: {len(df)}")
print(f"   Cached IDs: {len(cached_ids)}")
print(f"   Embedding shape: {embeddings.shape}")
print(f"   Are IDs in exact order? {list(df['Book_ID']) == cached_ids}")

# 2. Check L2 Norms
norms = np.linalg.norm(embeddings, axis=1)
print(f"2. Embedding norms: min={norms.min():.6f}, max={norms.max():.6f}, mean={norms.mean():.6f}")

# 3. Check Tokenizer with Vietnamese
sample_texts = [
    "Tôi muốn học lập trình Python từ con số 0!",
    "Người đàn ông mang tên Ô-vê",
    "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông",
    "khong gia dinh hector malot",
    "Totto-chan bên cửa sổ"
]

def tokenize_vietnamese(text: str) -> list:
    text = text.lower()
    return re.findall(r'\b\w+\b', text)

print("\n3. Tokenization test:")
for st in sample_texts:
    tokens = tokenize_vietnamese(st)
    print(f"   Original: '{st}'")
    print(f"   Tokens:   {tokens}")

# 4. Check Ground Truth definition in eval_110_results.json
with open('tests/eval_110_results.json', 'r', encoding='utf-8') as f:
    eval_results = json.load(f)

print(f"\n4. Total test cases recorded: {len(eval_results)}")
sample_tc = eval_results[22] # TC023
print(f"   Sample TC: ID={sample_tc['test_id']}, Query='{sample_tc['query']}', Group='{sample_tc['group']}'")
print(f"   Rank found BM25: {sample_tc['modes']['bm25']['rank_found']}")
print(f"   Rank found Semantic: {sample_tc['modes']['semantic']['rank_found']}")
print(f"   Rank found Hybrid: {sample_tc['modes']['hybrid']['rank_found']}")
