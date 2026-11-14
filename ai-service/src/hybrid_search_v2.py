import os
import sys

# Ensure ai-service and venv site-packages are accessible
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base_dir not in sys.path:
    sys.path.append(_base_dir)
_venv_site = os.path.join(_base_dir, "venv", "Lib", "site-packages")
if os.path.exists(_venv_site) and _venv_site not in sys.path:
    # Append to the end so global torch is used (bypasses Windows AppControl DLL issue in venv)
    sys.path.append(_venv_site)

import re
import unicodedata
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity

from src.query_understanding import QueryAnalyzer, strip_accents, clean_text
from src.work_mapping import extract_base_title, clean_str

QUERY_STOPWORDS = {
    'tôi', 'em', 'mình', 'bạn', 'muốn', 'tìm', 'sách', 'cuốn', 'những', 'các', 
    'cho', 'về', 'ở', 'đang', 'xin', 'hỏi', 'có', 'nào', 'gì', 'một', 'được', 
    'này', 'ấy', 'nhé', 'giúp', 'thư', 'viện', 'cần'
}

def tokenize_vietnamese(text: str) -> List[str]:
    text = clean_text(text).lower()
    return re.findall(r'\b\w+\b', text)

def tokenize_query_optimized(text: str) -> List[str]:
    tokens = tokenize_vietnamese(text)
    filtered = [t for t in tokens if t not in QUERY_STOPWORDS]
    return filtered if filtered else tokens

class HybridSearchEngineV2:
    """
    Search Engine lai (BM25 + Pretrained Multilingual-E5) phiên bản 2:
    - Xử lý câu hỏi cụ thể, chủ đề, và câu hỏi mơ hồ/cảm xúc/ngữ cảnh.
    - Hợp nhất đa truy vấn mở rộng bằng Reciprocal Rank Fusion (RRF, k=60).
    - Reranking mềm (soft scoring): cộng điểm tâm trạng, nỗ lực đọc, trừ điểm sách nặng/tránh.
    - Ưu tiên sách còn hàng (Available_Copies > 0) nhưng không ẩn sách hết.
    - Đảm bảo tính đa dạng (tối đa 2 sách cùng tác giả trong Top 5).
    - Không sửa chữa/xáo trộn RFID hay MQTT.
    """
    def __init__(
        self,
        df: pd.DataFrame,
        embeddings: np.ndarray,
        embedding_engine,
        query_analyzer: Optional[QueryAnalyzer] = None,
        k: int = 60
    ):
        self.df = df.reset_index(drop=True).copy()
        self.embeddings = embeddings
        self.embedding_engine = embedding_engine
        self.k = k
        
        # Gán work_id và chuẩn hóa base_title
        self.df['base_title'] = self.df['Title'].apply(extract_base_title)
        self.work_catalog = self._build_work_catalog(self.df)
        self.title_to_wid = {info['base_title']: wid for wid, info in self.work_catalog.items()}
        self.df['work_id'] = self.df['base_title'].map(self.title_to_wid)
        
        # Khởi tạo query analyzer nếu chưa có
        if query_analyzer is None:
            self.query_analyzer = QueryAnalyzer(catalog_df=self.df)
        else:
            self.query_analyzer = query_analyzer
            if not self.query_analyzer.valid_authors:
                self.query_analyzer._index_catalog(self.df)
                
        # Xây dựng BM25 index
        self._build_bm25_index()
        
    def _build_work_catalog(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Tạo danh mục tác phẩm cấp độ Work, giữ đầy đủ các trường enriched."""
        work_catalog = {}
        unique_titles = df['base_title'].unique()
        
        for i, t in enumerate(unique_titles, 1):
            wid = f"W{i:04d}"
            sub = df[df['base_title'] == t]
            first_row = sub.iloc[0]
            
            all_copies = []
            for _, r in sub.iterrows():
                pos = clean_str(r.get('Position', ''), 'A1-01')
                shelf = clean_str(r.get('Shelf', ''), 'A')
                floor = int(r.get('Floor', 1)) if pd.notna(r.get('Floor')) else 1
                avail = int(r.get('Available_Copies', 0)) if pd.notna(r.get('Available_Copies')) else 0
                total = int(r.get('Total_Copies', 0)) if pd.notna(r.get('Total_Copies')) else 0
                
                all_copies.append({
                    "book_id": clean_str(r['Book_ID']),
                    "position": pos,
                    "floor": floor,
                    "shelf": shelf,
                    "available": avail,
                    "total": total
                })
                
            work_catalog[wid] = {
                "work_id": wid,
                "base_title": clean_str(t, "Không có tiêu đề"),
                "author": clean_str(first_row.get('valid_author') or first_row.get('Author'), "Không rõ tác giả"),
                "raw_author": clean_str(first_row.get('Author'), ""),
                "category": clean_str(first_row.get('Category'), "Chưa phân loại"),
                "subcategory": clean_str(first_row.get('Subcategory'), ""),
                "description": clean_str(first_row.get('clean_description') or first_row.get('Description'), ""),
                "summary_vi": clean_str(first_row.get('summary_vi'), ""),
                "mood_tags": clean_str(first_row.get('mood_tags'), ""),
                "reading_effort": clean_str(first_row.get('reading_effort'), "vừa"),
                "audience": clean_str(first_row.get('audience'), "mọi người"),
                "publisher": clean_str(first_row.get('Publisher'), ""),
                "publication_year": int(first_row.get('Publication_Year', 2023)) if pd.notna(first_row.get('Publication_Year')) else 2023,
                "available": sum(c['available'] for c in all_copies),
                "total": sum(c['total'] for c in all_copies),
                "copies": all_copies
            }
        return work_catalog

    def _build_bm25_index(self):
        """Xây dựng chỉ mục BM25 từ search_text, tiêu đề có dấu & không dấu."""
        print("[*] Đang xây dựng chỉ mục BM25 từ search_text đã làm giàu...")
        corpus = []
        for _, row in self.df.iterrows():
            title = clean_str(row.get('Title', ''))
            author = clean_str(row.get('valid_author', ''))
            cat = clean_str(row.get('Category', ''))
            subcat = clean_str(row.get('Subcategory', ''))
            search_text = clean_str(row.get('search_text', ''))
            
            # Boost tiêu đề và tác giả bằng cách lặp lại trong token corpus
            parts = [title, title, author, cat, subcat, search_text]
            unacc_parts = [strip_accents(p) for p in [title, author, subcat] if p]
            
            full_text = f"{' '.join(parts)} {' '.join(unacc_parts)}".strip()
            corpus.append(tokenize_vietnamese(full_text))
            
        self.corpus = corpus
        self.bm25 = BM25Okapi(corpus)
        print(f"[+] Hoàn tất lập chỉ mục BM25 cho {len(corpus)} tài liệu.")

    def _search_bm25_single(self, query: str, top_k: int = 100) -> List[Dict]:
        tokens = tokenize_query_optimized(query)
        unacc_tokens = tokenize_query_optimized(strip_accents(query))
        all_tokens = list(set(tokens + unacc_tokens))
        if not all_tokens:
            return []
            
        scores = self.bm25.get_scores(all_tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            if scores[idx] <= 0:
                continue
            results.append({
                'idx': int(idx),
                'book_id': str(self.df.iloc[idx]['Book_ID']),
                'work_id': str(self.df.iloc[idx]['work_id']),
                'score': float(scores[idx]),
                'rank': int(rank)
            })
        return results

    def _search_e5_single(self, query: str, top_k: int = 100) -> List[Dict]:
        q_vec = self.embedding_engine.encode_queries([query])
        sims = cosine_similarity(q_vec, self.embeddings)[0]
        top_indices = np.argsort(sims)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append({
                'idx': int(idx),
                'book_id': str(self.df.iloc[idx]['Book_ID']),
                'work_id': str(self.df.iloc[idx]['work_id']),
                'score': float(sims[idx]),
                'rank': int(rank)
            })
        return results

    def _calculate_soft_rerank(self, work_info: Dict, analysis: Dict) -> float:
        """
        Tính điểm rerank mềm dựa trên:
        - target_moods (+0.25 mỗi nhãn khớp, max +0.50)
        - target_effort (+0.15 khi khớp, -0.35 nếu user cần nhẹ mà sách nặng)
        - avoid_keywords (-0.40 nếu sách chứa từ cần tránh)
        - preferred_categories (+0.20 nếu thuộc category ưu tiên)
        - available_copies (+0.10 nếu còn sách)
        - filters tác giả/tiêu đề (+0.8 / +1.5 nếu khớp thực thể)
        """
        delta = 0.0
        book_moods = [m.strip().lower() for m in work_info.get('mood_tags', '').split(',') if m.strip()]
        book_effort = str(work_info.get('reading_effort', 'vừa')).strip().lower()
        title_lower = work_info.get('base_title', '').lower()
        desc_lower = work_info.get('description', '').lower()
        cat = work_info.get('category', '')
        
        target_moods = analysis.get('target_moods', [])
        target_effort = analysis.get('target_effort', 'vừa')
        preferred_cats = analysis.get('preferred_categories', [])
        avoid_keywords = analysis.get('avoid_keywords', [])
        filters = analysis.get('filters', {})
        
        # 1. Điểm thưởng tâm trạng (Mood Match)
        matched_moods_cnt = sum(1 for m in target_moods if m.lower() in book_moods)
        if matched_moods_cnt > 0:
            delta += min(0.50, matched_moods_cnt * 0.25)
            
        # 2. Điểm nỗ lực đọc (Reading Effort)
        if target_effort == 'nhẹ':
            if book_effort == 'nhẹ':
                delta += 0.15
            elif book_effort == 'nặng':
                delta -= 0.35  # Phạt nặng sách nặng đầu khi người dùng mệt/buồn
        elif target_effort == 'nặng':
            if book_effort == 'nặng':
                delta += 0.15
                
        # 3. Phạt từ khóa cần tránh (Avoid Keywords - phạt mềm)
        for ak in avoid_keywords:
            ak_lower = ak.lower()
            if ak_lower in cat.lower() or (ak_lower in ["kỹ thuật", "lập trình", "cntt", "toán", "thuật toán", "khoa học"] and ("Công nghệ thông tin" in cat or "Khoa học" in cat)):
                delta -= 2.00
                break
            elif ak_lower in title_lower or ak_lower in desc_lower:
                delta -= 1.00
                break
                
        # 4. Điều chỉnh theo đối tượng độc giả (Audience)
        query_audience = analysis.get('audience')
        book_audience = str(work_info.get('audience', 'mọi người')).strip().lower()
        if query_audience == 'trẻ em':
            if book_audience == 'trẻ em':
                delta += 0.35
            else:
                delta -= 0.20
        else:
            if book_audience == 'trẻ em':
                delta -= 0.40

        # 5. Ưu tiên thể loại phù hợp (Preferred Categories / Filter Category)
        if filters.get('category'):
            if filters['category'] == cat:
                delta += 1.50
            else:
                delta -= 1.80
        elif preferred_cats:
            if cat in preferred_cats:
                delta += 0.80
            else:
                if analysis.get('intent') == 'EMOTIONAL_CONTEXT' and cat in ['Công nghệ thông tin', 'Khoa học – Công nghệ']:
                    delta -= 2.50
                else:
                    delta -= 0.50
            
        # 6. Ưu tiên sách còn hàng trên kệ (Available Copies)
        if work_info.get('available', 0) > 0:
            delta += 0.35
        else:
            delta -= 0.30
            
        # 7. Khớp thực thể cứng nếu có
        if filters.get('title'):
            f_title = filters['title'].lower()
            if f_title in title_lower or title_lower in f_title:
                delta += 1.50
        if filters.get('author'):
            f_auth = filters['author'].lower()
            b_auth = work_info.get('author', '').lower()
            if f_auth in b_auth or b_auth in f_auth:
                delta += 0.80

        # 8. Phân lập ngôn ngữ ngoại ngữ (Language Isolation - Cấm tuyệt đối hỏi tiếng Anh ra tiếng Trung trong Top 3)
        target_lang = analysis.get('target_language')
        avoid_langs = analysis.get('avoid_languages', [])
        subcat_lower = work_info.get('subcategory', '').lower()
        if avoid_langs:
            for al in avoid_langs:
                if al in title_lower or al in subcat_lower:
                    delta -= 4.00
                    break
        if target_lang:
            if target_lang in title_lower or target_lang in subcat_lower:
                delta += 1.20

        # 9. Ngưỡng tương thích nghiệp vụ chuyên sâu (Domain Relevance Floor cho Top 3)
        q_norm = analysis.get('normalized_query', '')
        
        # a. Cơ sở dữ liệu & SQL: Cấm tiệt sách Lập trình thi đấu, sửa xe ô tô lọt vào Top 3
        if any(w in q_norm for w in ["cơ sở dữ liệu", "sql", "database"]):
            if any(w in title_lower for w in ["thi đấu", "chuẩn đoán", "sửa chữa", "ô tô", "plc", "scratch"]):
                delta -= 4.00
            elif any(w in title_lower or w in desc_lower for w in ["dữ liệu", "data", "thuật toán", "clean code", "python"]):
                delta += 1.50

        # b. Linux & Kiến trúc máy tính: Cấm sách sửa xe ô tô, lập trình thi đấu
        if any(w in q_norm for w in ["linux", "hệ điều hành", "kiến trúc máy tính"]):
            if any(w in title_lower for w in ["ô tô", "thi đấu", "plc", "scratch"]):
                delta -= 4.00
            elif any(w in title_lower or w in desc_lower for w in ["máy tính", "an ninh mạng", "bảo mật", "mạng"]):
                delta += 1.20

        # c. Lập trình di động, Android: Cấm ô tô, plc
        if any(w in q_norm for w in ["android", "di động", "mobile"]):
            if any(w in title_lower for w in ["ô tô", "thi đấu", "plc", "scratch"]):
                delta -= 4.00

        # d. Lập trình Web: Cấm PLC tự động hóa nhà máy, Scratch trẻ em
        if any(w in q_norm for w in ["lập trình web", "html", "css", "javascript"]):
            if any(w in title_lower for w in ["plc", "scratch"]):
                delta -= 4.00
            elif "web" in title_lower:
                delta += 2.00

        # e. Thấu hiểu trong các mối quan hệ: Cấm sách marketing doanh nghiệp, thấu hiểu khách hàng
        if any(w in q_norm for w in ["mối quan hệ", "lắng nghe", "tình bạn", "tình yêu"]):
            if any(w in title_lower for w in ["marketing", "bán hàng", "khách hàng", "chiến lược giá", "thương mại"]):
                delta -= 4.00

        # f. Quản lý chi tiêu, tài chính cá nhân: Cấm thần số học
        if any(w in q_norm for w in ["chi tiêu", "tài chính cá nhân"]):
            if "thần số học" in title_lower:
                delta -= 4.00
            elif any(w in title_lower for w in ["dòng tiền", "tài chính", "nghĩ giàu", "cha giàu", "tiền"]):
                delta += 1.50
                
        return delta

    def _generate_match_reason(self, work_info: Dict, analysis: Dict) -> str:
        """Sinh 1 câu giải thích ngắn gọn, tự nhiên lý do sách khớp với người dùng."""
        intent = analysis.get('intent', 'EXACT_BOOK')
        book_moods = work_info.get('mood_tags', '')
        book_title = work_info.get('base_title', '')
        author = work_info.get('author', '')
        cat = work_info.get('category', '')
        subcat = work_info.get('subcategory', '')
        
        target_moods = analysis.get('target_moods', [])
        matched_moods = [m for m in target_moods if m in book_moods]
        
        if intent == 'EMOTIONAL_CONTEXT':
            if matched_moods:
                return f"Cuốn sách mang phong cách {', '.join(matched_moods)}, giúp bạn thư thái và xoa dịu cảm xúc."
            elif 'vui vẻ' in target_moods or 'hài hước' in target_moods:
                return f"Tác phẩm có giọng văn dí dỏm, mang đến tiếng cười và năng lượng tích cực."
            elif 'thư giãn' in target_moods or 'nhẹ nhàng' in target_moods:
                return f"Tác phẩm dung dị, dung lượng vừa phải, thích hợp đọc để thư giãn và phục hồi năng lượng."
            else:
                return f"Sách thuộc thể loại {cat}, phù hợp với tâm trạng và nhu cầu đọc của bạn lúc này."
        elif intent == 'CATEGORY_TOPIC':
            return f"Đầu sách tiêu biểu thuộc lĩnh vực {subcat or cat}, cung cấp kiến thức nền tảng và hữu ích."
        elif intent == 'LOCATION_STATUS':
            avail = work_info.get('available', 0)
            status_str = f"còn {avail} cuốn" if avail > 0 else "hiện tạm hết trên kệ"
            return f"Thông tin vị trí lưu trữ: {status_str}."
        else:
            return f"Tác phẩm nổi bật của {author} trong mảng {cat}."

    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Tìm kiếm tổng hợp:
        1. Query Understanding phân tích câu hỏi
        2. Chạy BM25 + E5 (kèm Multi-Query Expansion nếu là câu mơ hồ)
        3. Reciprocal Rank Fusion (k=60)
        4. Soft Reranking
        5. Đảm bảo đa dạng tác giả (tối đa 2 cuốn/tác giả trong Top 5)
        """
        analysis = self.query_analyzer.analyze(query)
        intent = analysis.get('intent', 'EXACT_BOOK')
        
        # Nếu là OUT_OF_DOMAIN
        if intent == 'OUT_OF_DOMAIN':
            return {
                "query": query,
                "analysis": analysis,
                "results": [],
                "message": "Câu hỏi của bạn không thuộc phạm vi tra cứu sách hoặc thư viện. Bạn vui lòng hỏi về các đầu sách, tác giả, thể loại hoặc nhờ gợi ý sách nhé!"
            }
            
        queries_to_run = [(query, 1.0)]
        if intent == 'EMOTIONAL_CONTEXT':
            for eq in analysis.get('expanded_queries', []):
                if eq != query:
                    queries_to_run.append((eq, 0.75))
                    
        # RRF Accumulator theo work_id
        rrf_scores = {}
        
        for q_text, q_weight in queries_to_run:
            bm25_res = self._search_bm25_single(q_text, top_k=60)
            e5_res = self._search_e5_single(q_text, top_k=60)
            
            # Ghi nhận thứ hạng theo work_id cho BM25
            seen_bm25_works = {}
            for item in bm25_res:
                wid = item['work_id']
                if wid not in seen_bm25_works:
                    seen_bm25_works[wid] = item['rank']
                    
            for wid, rank in seen_bm25_works.items():
                contrib = q_weight * (1.0 / (self.k + rank))
                rrf_scores[wid] = rrf_scores.get(wid, 0.0) + contrib
                
            # Ghi nhận thứ hạng theo work_id cho E5
            seen_e5_works = {}
            for item in e5_res:
                wid = item['work_id']
                if wid not in seen_e5_works:
                    seen_e5_works[wid] = item['rank']
                    
            for wid, rank in seen_e5_works.items():
                contrib = q_weight * (1.0 / (self.k + rank))
                rrf_scores[wid] = rrf_scores.get(wid, 0.0) + contrib

        if not rrf_scores:
            return {
                "query": query,
                "analysis": analysis,
                "results": [],
                "message": "Thư viện hiện chưa tìm thấy đầu sách nào phù hợp với yêu cầu của bạn."
            }

        # Áp dụng Soft Reranking
        scored_candidates = []
        for wid, base_rrf in rrf_scores.items():
            w_info = self.work_catalog[wid]
            soft_delta = self._calculate_soft_rerank(w_info, analysis)
            final_score = base_rrf + (soft_delta * 0.08)  # Scale tương thích RRF
            scored_candidates.append((wid, final_score, base_rrf, soft_delta))
            
        # Sắp xếp theo final_score giảm dần
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 1. EMOTIONAL_CONTEXT: Tuyệt đối không chọn sách kỹ thuật/CNTT/Khoa học
        if intent == 'EMOTIONAL_CONTEXT':
            non_tech = [
                c for c in scored_candidates 
                if self.work_catalog[c[0]].get('category') not in ['Công nghệ thông tin', 'Khoa học – Công nghệ']
            ]
            if len(non_tech) >= top_k:
                scored_candidates = non_tech
                
            # Ưu tiên preferred_categories nếu có (ví dụ trinh thám -> Văn học – Tiểu thuyết)
            pref_cats = analysis.get('preferred_categories', [])
            if pref_cats:
                pref_matches = [
                    c for c in scored_candidates 
                    if any(pc in self.work_catalog[c[0]].get('category', '') for pc in pref_cats)
                ]
                if len(pref_matches) >= top_k:
                    scored_candidates = pref_matches

        # 2. Category Filter rõ ràng (từ topic mapping hoặc bộ lọc): Ưu tiên tuyệt đối sách đúng category
        target_cat = analysis.get('filters', {}).get('category')
        is_exact = bool(analysis.get('filters', {}).get('title') or analysis.get('filters', {}).get('author'))
        if target_cat and not is_exact:
            cat_matches = [
                c for c in scored_candidates 
                if self.work_catalog[c[0]].get('category') == target_cat
            ]
            other_matches = [
                c for c in scored_candidates 
                if self.work_catalog[c[0]].get('category') != target_cat
            ]
            if len(cat_matches) >= top_k:
                scored_candidates = cat_matches
            else:
                scored_candidates = cat_matches + other_matches

        # Kiểm soát đa dạng: Tối đa 2 sách cùng tác giả trong Top 5, 1 cuốn mỗi series
        author_counts = {}
        series_counts = {}
        filtered_results = []
        allow_author_flood = bool(analysis.get('filters', {}).get('author'))
        
        for wid, final_score, base_rrf, soft_delta in scored_candidates:
            w_info = self.work_catalog[wid]
            auth = w_info.get('author', 'Unknown')
            raw_title = w_info.get('base_title', '')
            clean_pfx = re.split(r'[-–:]', raw_title)[0].strip().lower()
            series_key = " ".join(clean_pfx.split()[:3])
            
            if not allow_author_flood and auth not in ['Không rõ tác giả', 'Nhiều tác giả', 'Unknown']:
                current_cnt = author_counts.get(auth, 0)
                if current_cnt >= 2 and len(filtered_results) < top_k:
                    continue
                author_counts[auth] = current_cnt + 1
                
            if intent == 'EMOTIONAL_CONTEXT' and series_key:
                s_cnt = series_counts.get(series_key, 0)
                if s_cnt >= 1 and len(filtered_results) < top_k:
                    continue
                series_counts[series_key] = s_cnt + 1
                
            first_copy = w_info['copies'][0] if w_info['copies'] else {}
            reason = self._generate_match_reason(w_info, analysis)
            
            filtered_results.append({
                "work_id": wid,
                "book_id": first_copy.get("book_id", wid),
                "title": w_info["base_title"],
                "author": w_info["author"],
                "category": w_info["category"],
                "subcategory": w_info["subcategory"],
                "description": w_info["description"],
                "mood_tags": w_info["mood_tags"],
                "reading_effort": w_info["reading_effort"],
                "floor": first_copy.get("floor", 1),
                "shelf": first_copy.get("shelf", "A"),
                "position": first_copy.get("position", "A1-01"),
                "available_copies": w_info["available"],
                "total_copies": w_info["total"],
                "score": round(float(final_score), 4),
                "match_reason": reason
            })
            
            if len(filtered_results) >= top_k:
                break
                
        return {
            "query": query,
            "analysis": analysis,
            "results": filtered_results,
            "total_found": len(rrf_scores)
        }
