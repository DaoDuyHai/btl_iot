import re
import pandas as pd
from rank_bm25 import BM25Okapi
from src.work_mapping import extract_base_title, strip_accents, get_work_catalog, clean_str

QUERY_STOPWORDS = {
    'tôi', 'em', 'mình', 'bạn', 'muốn', 'tìm', 'sách', 'cuốn', 'những', 'các', 
    'cho', 'về', 'ở', 'đang', 'xin', 'hỏi', 'có', 'nào', 'gì', 'một', 'được', 
    'này', 'ấy', 'nhé', 'giúp', 'thư', 'viện'
}

def tokenize_vietnamese(text: str) -> list:
    text = text.lower()
    return re.findall(r'\b\w+\b', text)

def tokenize_query_optimized(text: str) -> list:
    """Lọc từ dừng đàm thoại, giữ nguyên từ khóa mục đích tìm kiếm (học, làm, cách, website...)."""
    tokens = tokenize_vietnamese(text)
    filtered = [t for t in tokens if t not in QUERY_STOPWORDS]
    return filtered if filtered else tokens

class BM25SearchEngine:
    def __init__(self, df: pd.DataFrame, work_mapping: dict = None):
        self.df = df.reset_index(drop=True)
        if work_mapping is None:
            self.work_mapping = get_work_catalog(self.df)
        else:
            self.work_mapping = work_mapping
        
        # Ánh xạ base_title -> work_id
        self.title_to_wid = {info['base_title']: wid for wid, info in self.work_mapping.items()}
        
        # Gán work_id cho từng dòng của df
        self.df['base_title'] = self.df['Title'].apply(extract_base_title)
        self.df['work_id'] = self.df['base_title'].map(self.title_to_wid)
        
        print("[*] Đang xây dựng chỉ mục BM25 (hỗ trợ cả có dấu và không dấu)...")
        corpus = []
        for _, row in self.df.iterrows():
            title = clean_str(row.get('Title', ''))
            author = clean_str(row.get('Author', ''))
            cat = clean_str(row.get('Category', ''))
            subcat = clean_str(row.get('Subcategory', ''))
            keywords = clean_str(row.get('Keywords', ''))
            desc = clean_str(row.get('Description', ''))
            
            content_parts = [p for p in [title, author, cat, subcat, keywords, desc] if p]
            content = " ".join(content_parts)
            
            unacc_parts = [strip_accents(p) for p in [title, author, keywords] if p]
            unaccented_content = " ".join(unacc_parts)
            
            full_text = f"{content} {unaccented_content}".strip()
            corpus.append(tokenize_vietnamese(full_text))
            
        self.corpus = corpus
        self.bm25 = BM25Okapi(corpus)
        print(f"[+] Đã lập chỉ mục BM25 xong cho {len(corpus)} tài liệu.")

    def search_raw(self, query: str, top_k: int = 100) -> list:
        tokenized_query = tokenize_query_optimized(query)
        # Bổ sung tokens không dấu vào query nếu query có dấu
        unacc_tokens = tokenize_query_optimized(strip_accents(query))
        all_tokens = list(set(tokenized_query + unacc_tokens))
        
        if not all_tokens:
            return []
        scores = self.bm25.get_scores(all_tokens)
        top_indices = scores.argsort()[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            if scores[idx] <= 0:
                continue
            row = self.df.iloc[idx]
            results.append({
                'book_id': str(row['Book_ID']),
                'work_id': str(row['work_id']),
                'base_title': str(row['base_title']),
                'title': str(row['Title']),
                'author': str(row['Author']),
                'score': float(scores[idx]),
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
