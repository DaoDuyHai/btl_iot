import pandas as pd
from typing import List, Dict
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine

class HybridSearchEngine:
    """
    Kết hợp kết quả tìm kiếm BM25 và Semantic Search bằng thuật toán 
    Reciprocal Rank Fusion (RRF).
    Formula: RRF_Score(w) = sum( 1 / (k + rank_i(w)) ) với k = 60.
    """
    def __init__(self, bm25_engine: BM25SearchEngine, semantic_engine: SemanticSearchEngine, k: int = 60):
        self.bm25_engine = bm25_engine
        self.semantic_engine = semantic_engine
        self.k = k
        self.work_mapping = semantic_engine.work_mapping

    def search_raw(self, query: str, top_k: int = 10, fetch_k: int = 30) -> List[Dict]:
        bm25_raw = self.bm25_engine.search_raw(query, top_k=fetch_k)
        sem_raw = self.semantic_engine.search_raw(query, top_k=fetch_k)
        
        scores = {}
        book_info = {}
        for rank, res in enumerate(bm25_raw, 1):
            bid = res['book_id']
            scores[bid] = scores.get(bid, 0.0) + (1.0 / (self.k + rank))
            if bid not in book_info:
                book_info[bid] = res
                
        for rank, res in enumerate(sem_raw, 1):
            bid = res['book_id']
            scores[bid] = scores.get(bid, 0.0) + (1.0 / (self.k + rank))
            if bid not in book_info:
                book_info[bid] = res
                
        sorted_bids = sorted(scores.keys(), key=lambda b: scores[b], reverse=True)[:top_k]
        results = []
        for rank, bid in enumerate(sorted_bids, 1):
            item = dict(book_info[bid])
            item['score'] = float(scores[bid])
            item['rank'] = int(rank)
            results.append(item)
        return results

    def search(self, query: str, top_k: int = 10, fetch_k: int = 200) -> List[Dict]:
        """Tìm kiếm Hybrid CÓ GỘP theo work_id (Độ sâu tối ưu fetch_k = 200)."""
        bm25_works = self.bm25_engine.search(query, top_k=fetch_k)
        sem_works = self.semantic_engine.search(query, top_k=fetch_k)
        
        scores = {}
        for rank, res in enumerate(bm25_works, 1):
            wid = res['work_id']
            scores[wid] = scores.get(wid, 0.0) + (1.0 / (self.k + rank))
            
        for rank, res in enumerate(sem_works, 1):
            wid = res['work_id']
            scores[wid] = scores.get(wid, 0.0) + (1.0 / (self.k + rank))
            
        sorted_wids = sorted(scores.keys(), key=lambda w: scores[w], reverse=True)[:top_k]
        
        results = []
        for rank, wid in enumerate(sorted_wids, 1):
            w_info = self.work_mapping[wid]
            first_copy = w_info['copies'][0] if w_info['copies'] else {}
            results.append({
                'book_id': first_copy.get('book_id', wid),
                'work_id': wid,
                'title': w_info['base_title'],
                'author': w_info['author'],
                'category': w_info['category'],
                'subcategory': w_info['subcategory'],
                'description': w_info['description'],
                'keywords': w_info.get('keywords', ''),
                'score': float(scores[wid]),
                'rank': int(rank),
                'position': first_copy.get('position', 'A1-01'),
                'floor': first_copy.get('floor', 1),
                'shelf': first_copy.get('shelf', 'A'),
                'available': sum(c.get('available', 0) for c in w_info['copies']),
                'total': sum(c.get('total', 0) for c in w_info['copies']),
                'copies': w_info['copies']
            })
        return results
