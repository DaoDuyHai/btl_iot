import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from src.embedding import EmbeddingEngine
from src.work_mapping import extract_base_title, get_work_catalog

class SemanticSearchEngine:
    def __init__(self, df: pd.DataFrame, embedding_engine: EmbeddingEngine, embeddings: np.ndarray, book_ids: list, work_mapping: dict = None):
        self.df = df.reset_index(drop=True)
        self.embedding_engine = embedding_engine
        self.embeddings = embeddings
        self.book_ids = book_ids
        if work_mapping is None:
            self.work_mapping = get_work_catalog(self.df)
        else:
            self.work_mapping = work_mapping
        
        # Ánh xạ base_title -> work_id
        self.title_to_wid = {info['base_title']: wid for wid, info in self.work_mapping.items()}
        self.df['base_title'] = self.df['Title'].apply(extract_base_title)
        self.df['work_id'] = self.df['base_title'].map(self.title_to_wid)
        self.row_work_ids = list(self.df['work_id'])

    def search_raw(self, query: str, top_k: int = 100) -> list:
        query_vector = self.embedding_engine.encode_queries([query])
        similarities = cosine_similarity(query_vector, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            bid = self.book_ids[idx]
            wid = self.row_work_ids[idx]
            row = self.df.iloc[idx]
            results.append({
                'book_id': str(bid),
                'work_id': str(wid),
                'base_title': str(row['base_title']),
                'title': str(row['Title']),
                'author': str(row['Author']),
                'score': float(similarities[idx]),
                'rank': int(rank)
            })
        return results

    def search(self, query: str, top_k: int = 10) -> list:
        """Tìm kiếm có GỘP kết quả theo work_id."""
        raw_results = self.search_raw(query, top_k=200)
        
        seen_works = {}
        for item in raw_results:
            wid = item['work_id']
            if wid not in seen_works:
                seen_works[wid] = item
                
        aggregated = []
        for rank, (wid, item) in enumerate(list(seen_works.items())[:top_k], 1):
            w_info = self.work_mapping[wid]
            first_copy = w_info['copies'][0] if w_info['copies'] else {}
            aggregated.append({
                'book_id': first_copy.get('book_id', wid),
                'work_id': wid,
                'title': w_info['base_title'],
                'author': w_info['author'],
                'category': w_info['category'],
                'subcategory': w_info['subcategory'],
                'description': w_info['description'],
                'keywords': w_info.get('keywords', ''),
                'score': float(item['score']),
                'rank': int(rank),
                'position': first_copy.get('position', 'A1-01'),
                'floor': first_copy.get('floor', 1),
                'shelf': first_copy.get('shelf', 'A'),
                'available': sum(c.get('available', 0) for c in w_info['copies']),
                'total': sum(c.get('total', 0) for c in w_info['copies']),
                'copies': w_info['copies']
            })
        return aggregated
