# d:\TrainAI\src\embedding.py
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from src.passage_builder import build_passage
from src.cache_manager import CacheManager, compute_hash

DEFAULT_MODEL = "intfloat/multilingual-e5-small"

class EmbeddingEngine:
    def __init__(self, model_name: str = DEFAULT_MODEL, cache_dir: str = "embeddings"):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.cache_manager = CacheManager(cache_dir, model_name)
        print(f"[*] Đang khởi tạo mô hình embedding: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print(f"[+] Khởi tạo mô hình thành công. Chiều vector: 384")

    def encode_queries(self, queries: list) -> np.ndarray:
        # Chuẩn bị định dạng E5 cho query: prefix "query: " bắt buộc cho E5
        formatted = [f"query: {q.strip()}" for q in queries]
        return self.model.encode(formatted, normalize_embeddings=True)

    def get_or_build_embeddings(self, df: pd.DataFrame, force_rebuild: bool = False) -> tuple:
        if not force_rebuild:
            cached_emb, cached_ids, meta = self.cache_manager.load_cache()
            cached_hashes = meta.get("item_hashes", {}) if meta else {}
            
            current_passages = {}
            current_hashes = {}
            for _, row in df.iterrows():
                bid = row['Book_ID']
                passage = build_passage(row)
                current_passages[bid] = passage
                current_hashes[bid] = compute_hash(passage)

            if (cached_emb is not None and 
                len(cached_ids) == len(df) and 
                all(cached_ids[i] == df.iloc[i]['Book_ID'] for i in range(len(df))) and
                all(cached_hashes.get(bid) == current_hashes[bid] for bid in current_hashes)):
                print(f"[+] Toàn bộ {len(df)} embeddings khớp cache hoàn hảo, không cần tính lại!")
                return cached_emb, cached_ids
        else:
            current_passages = {}
            current_hashes = {}
            for _, row in df.iterrows():
                bid = row['Book_ID']
                passage = build_passage(row)
                current_passages[bid] = passage
                current_hashes[bid] = compute_hash(passage)

        print(f"[*] Đang tạo embeddings mới cho {len(df)} đầu sách bằng {self.model_name}...")
        ordered_passages = [current_passages[row['Book_ID']] for _, row in df.iterrows()]
        embeddings = self.model.encode(ordered_passages, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
        ordered_ids = list(df['Book_ID'])
        
        self.cache_manager.save_cache(embeddings, ordered_ids, current_hashes)
        return embeddings, ordered_ids
