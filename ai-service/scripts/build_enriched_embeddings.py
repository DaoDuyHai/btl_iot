import os
import sys
import time
import json
import hashlib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Thêm đường dẫn ai-service vào sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

DATASET_PATH = os.path.join(BASE_DIR, "dataset", "books_enriched.csv")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "embeddings")
EMB_FILE = os.path.join(EMBEDDINGS_DIR, "embeddings_enriched.npy")
IDS_FILE = os.path.join(EMBEDDINGS_DIR, "book_ids_enriched.json")
META_FILE = os.path.join(EMBEDDINGS_DIR, "metadata_enriched.json")

MODEL_NAME = "intfloat/multilingual-e5-small"

def compute_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def main():
    start_time = time.time()
    print(f"[*] Đọc dataset đã làm giàu: {DATASET_PATH}")
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Không tìm thấy file: {DATASET_PATH}")
        
    df = pd.read_csv(DATASET_PATH)
    total_books = len(df)
    print(f"[+] Đã tải {total_books} sách từ dataset.")
    
    # Chuẩn bị passages theo chuẩn E5 ("passage: ...")
    print("[*] Chuẩn bị passages từ cột search_text...")
    passages = []
    item_hashes = {}
    book_ids = []
    
    for _, row in df.iterrows():
        bid = str(row['Book_ID'])
        st = str(row.get('search_text', '')).strip()
        passage = f"passage: {st}"
        passages.append(passage)
        item_hashes[bid] = compute_hash(passage)
        book_ids.append(bid)
        
    print(f"[*] Ví dụ passage đầu tiên (B0001):\n{passages[0][:160]}...")
    
    # Tải mô hình
    print(f"[*] Đang tải mô hình embedding: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    # Tiến hành encode
    print(f"[*] Bắt đầu sinh vector embedding cho {total_books} sách (batch_size=64, normalize_embeddings=True)...")
    enc_start = time.time()
    embeddings = model.encode(
        passages,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    enc_duration = time.time() - enc_start
    print(f"[+] Mã hóa hoàn tất trong {enc_duration:.2f}s (~{total_books / enc_duration:.1f} sách/giây).")
    
    # Kiểm tra kích thước và chuẩn L2
    assert embeddings.shape == (total_books, 384), f"Shape không đúng: {embeddings.shape}"
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), f"Embeddings chưa được chuẩn hóa L2!"
    print(f"[+] Kiểm tra tính hợp lệ thành công: Shape {embeddings.shape}, tất cả norm L2 = 1.0.")
    
    # Lưu cache
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    np.save(EMB_FILE, embeddings)
    with open(IDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(book_ids, f, ensure_ascii=False, indent=2)
        
    metadata = {
        "model_name": MODEL_NAME,
        "total_books": total_books,
        "vector_dim": int(embeddings.shape[1]),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_dataset": "dataset/books_enriched.csv",
        "item_hashes": item_hashes
    }
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
        
    total_duration = time.time() - start_time
    print(f"[+] Đã lưu file cache thành công:")
    print(f"    - Embeddings: {EMB_FILE} ({os.path.getsize(EMB_FILE) / 1024 / 1024:.2f} MB)")
    print(f"    - Book IDs:   {IDS_FILE}")
    print(f"    - Metadata:   {META_FILE}")
    print(f"[+] Tổng thời gian hoàn thành: {total_duration:.2f} giây.")

if __name__ == "__main__":
    main()
