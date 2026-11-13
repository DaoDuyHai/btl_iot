# d:\TrainAI\src\cache_manager.py
import os
import json
import hashlib
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List

METADATA_FILE = "metadata.json"
BOOK_IDS_FILE = "book_ids.json"
EMBEDDINGS_FILE = "embeddings.npy"

def compute_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

class CacheManager:
    def __init__(self, cache_dir: str, model_name: str):
        self.cache_dir = cache_dir
        self.model_name = model_name
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.meta_path = os.path.join(self.cache_dir, METADATA_FILE)
        self.ids_path = os.path.join(self.cache_dir, BOOK_IDS_FILE)
        self.emb_path = os.path.join(self.cache_dir, EMBEDDINGS_FILE)

    def load_cache(self) -> Tuple[np.ndarray, List[str], Dict]:
        if (os.path.exists(self.meta_path) and 
            os.path.exists(self.ids_path) and 
            os.path.exists(self.emb_path)):
            try:
                with open(self.meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                with open(self.ids_path, 'r', encoding='utf-8') as f:
                    book_ids = json.load(f)
                embeddings = np.load(self.emb_path)
                return embeddings, book_ids, meta
            except Exception as e:
                print(f"[!] Lỗi đọc cache: {e}")
        return None, [], {}

    def save_cache(self, embeddings: np.ndarray, book_ids: List[str], item_hashes: Dict[str, str]):
        meta = {
            "model_name": self.model_name,
            "total_books": len(book_ids),
            "vector_dim": embeddings.shape[1] if embeddings is not None and len(embeddings) > 0 else 0,
            "item_hashes": item_hashes
        }
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        with open(self.ids_path, 'w', encoding='utf-8') as f:
            json.dump(book_ids, f, ensure_ascii=False, indent=2)
        np.save(self.emb_path, embeddings)
        print(f"[+] Đã lưu cache thành công ({len(book_ids)} vectors) vào {self.cache_dir}")
