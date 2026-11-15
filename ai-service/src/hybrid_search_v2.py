import os
import sys

# Ensure ai-service and venv site-packages are accessible
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base_dir not in sys.path:
    sys.path.append(_base_dir)
_venv_site = os.path.join(_base_dir, "venv", "Lib", "site-packages")
if os.path.exists(_venv_site) and _venv_site not in sys.path:
    sys.path.append(_venv_site)

import re
import unicodedata
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

from src.query_understanding import QueryAnalyzer, strip_accents, clean_text
from src.work_mapping import extract_base_title, clean_str

QUERY_STOPWORDS = {
    'tôi', 'em', 'mình', 'bạn', 'muốn', 'tìm', 'sách', 'cuốn', 'những', 'các', 
    'cho', 'về', 'ở', 'đang', 'xin', 'hỏi', 'có', 'nào', 'gì', 'một', 'được', 
    'này', 'ấy', 'nhé', 'giúp', 'thư', 'viện', 'cần'
}

SHELF_INFO = {
    "A": {"floor": 1, "category": "Văn học – Tiểu thuyết, Thiếu nhi"},
    "B": {"floor": 1, "category": "Kinh tế – Kinh doanh"},
    "C": {"floor": 2, "category": "Công nghệ thông tin, Khoa học – Công nghệ"},
    "D": {"floor": 2, "category": "Giáo dục – Ngoại ngữ"},
    "E": {"floor": 3, "category": "Kỹ năng sống – Phát triển bản thân, Tâm lý học"},
    "F": {"floor": 3, "category": "Lịch sử – Văn hóa"}
}

def tokenize_vietnamese(text: str) -> List[str]:
    text = clean_text(text).lower()
    return re.findall(r'\b\w+\b', text)

def tokenize_query_optimized(text: str) -> List[str]:
    tokens = tokenize_vietnamese(text)
    filtered = [t for t in tokens if t not in QUERY_STOPWORDS]
    return filtered if filtered else tokens

def normalize_title_for_dedup(title: str) -> str:
    """Chuẩn hóa tiêu đề để khử trùng lặp các ấn bản na ná nhau."""
    t = clean_text(title).lower()
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'\[.*?\]', '', t)
    t = re.sub(r'[-–:]\s*(tập|bản quyền|stk|tác giả|quyển|cuốn|phần).*$', '', t, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip()
    return strip_accents(t)

def is_title_matched(target_str: str, candidate_title: str) -> bool:
    """Kiểm tra xem candidate_title có khớp thực sự với target_str hay không."""
    if not target_str or not candidate_title:
        return False
    t_norm = strip_accents(target_str).lower().strip()
    c_norm = strip_accents(candidate_title).lower().strip()
    
    # 1. Khớp chính xác hoàn toàn
    if t_norm == c_norm:
        return True
        
    # 2. Khớp chuỗi con
    if len(t_norm) >= 4 and (t_norm in c_norm or c_norm in t_norm):
        if len(t_norm) / max(len(c_norm), 1) > 0.4 or c_norm.startswith(t_norm):
            return True

    # 3. Kiểm tra công nghệ / từ khóa độc quyền tránh nhầm lẫn (vd: Rust vs C++, Golang vs Java)
    tech_keywords = ['rust', 'golang', 'go', 'python', 'java', 'c++', 'c#', 'sql server', 'mongodb', 'docker', 'kubernetes', 'android', 'react', 'flutter']
    for tk in tech_keywords:
        if tk in t_norm and tk not in c_norm:
            return False

    # 4. Loại bỏ các cụm từ đệm thông dụng
    boilerplate = ['tu co ban den nang cao', 'co ban va nang cao', 'can ban va nang cao', 'thuc chien', 'giao trinh', 'tap 1', 'tap 2', 'bo sach']
    t_core = t_norm
    c_core = c_norm
    for bp in boilerplate:
        t_core = t_core.replace(bp, ' ')
        c_core = c_core.replace(bp, ' ')

    t_words = set(re.findall(r'\b\w+\b', t_core))
    c_words = set(re.findall(r'\b\w+\b', c_core))
    if not t_words:
        return False

    overlap = len(t_words & c_words) / len(t_words)
    # Nếu tựa ngắn (<= 3 từ như "Đắc nhân tâm"), yêu cầu khớp chặt chẽ >= 0.85
    if len(t_words) <= 3:
        return overlap >= 0.85
    return overlap >= 0.70

class HybridSearchEngineV2:
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
        
        self.df['base_title'] = self.df['Title'].apply(extract_base_title)
        self.work_catalog = self._build_work_catalog(self.df)
        self.title_to_wid = {info['base_title']: wid for wid, info in self.work_catalog.items()}
        self.df['work_id'] = self.df['base_title'].map(self.title_to_wid)
        
        if query_analyzer is None:
            self.query_analyzer = QueryAnalyzer(catalog_df=self.df)
        else:
            self.query_analyzer = query_analyzer
            if not self.query_analyzer.valid_authors:
                self.query_analyzer._index_catalog(self.df)
                
        self._build_bm25_index()
        
    def _build_work_catalog(self, df: pd.DataFrame) -> Dict[str, Dict]:
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
        print("[*] Đang xây dựng chỉ mục BM25 từ search_text đã làm giàu...")
        corpus = []
        for _, row in self.df.iterrows():
            title = clean_str(row.get('Title', ''))
            author = clean_str(row.get('valid_author', ''))
            cat = clean_str(row.get('Category', ''))
            subcat = clean_str(row.get('Subcategory', ''))
            search_text = clean_str(row.get('search_text', ''))
            
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
        q_norm = q_vec / (np.linalg.norm(q_vec, axis=1, keepdims=True) + 1e-9)
        emb_norm = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-9)
        sims = np.dot(emb_norm, q_norm[0])
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
        
        # 1. Điểm thưởng tâm trạng
        matched_moods_cnt = sum(1 for m in target_moods if m.lower() in book_moods)
        if matched_moods_cnt > 0:
            delta += min(0.50, matched_moods_cnt * 0.25)
            
        # 2. Điểm nỗ lực đọc
        if target_effort == 'nhẹ':
            if book_effort == 'nhẹ':
                delta += 0.15
            elif book_effort == 'nặng':
                delta -= 0.35
        elif target_effort == 'nặng':
            if book_effort == 'nặng':
                delta += 0.15
                
        # 3. Phạt từ khóa cần tránh từ mệnh đề phủ định (Phạt nặng)
        for ak in avoid_keywords:
            ak_lower = ak.lower().strip()
            if len(ak_lower) < 2:
                continue
            if ak_lower in title_lower:
                delta -= 5.00
                break
            elif ak_lower in desc_lower:
                delta -= 3.00
                break
            elif ak_lower in cat.lower():
                delta -= 4.00
                break
                
        # 4. Điều chỉnh theo đối tượng độc giả
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

        # 5. Ưu tiên thể loại phù hợp
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
            
        # 6. Ưu tiên sách còn hàng
        if work_info.get('available', 0) > 0:
            delta += 0.35
        else:
            delta -= 0.30
            
        # 7. Khớp thực thể cứng
        target_t = filters.get('title') or filters.get('target_title') or filters.get('quoted_title')
        if target_t:
            if is_title_matched(target_t, work_info.get('base_title', '')):
                delta += 3.00
                
        if filters.get('author'):
            f_auth = filters['author'].lower()
            b_auth = work_info.get('author', '').lower()
            if f_auth in b_auth or b_auth in f_auth:
                delta += 1.50

        # 8. Phân lập ngôn ngữ ngoại ngữ
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

        # 9. Ranh giới miền tri thức
        q_norm = analysis.get('positive_query', '') or analysis.get('normalized_query', '')
        
        if any(w in q_norm for w in ["cơ sở dữ liệu", "sql", "database", "csdl"]):
            if cat != "Công nghệ thông tin":
                delta -= 6.00
            if any(w in title_lower for w in ["thi đấu", "chuẩn đoán", "sửa chữa", "ô tô", "plc", "scratch"]):
                delta -= 4.00
            elif any(w in title_lower or w in desc_lower for w in ["dữ liệu", "data", "thuật toán", "clean code", "python", "lập trình"]):
                delta += 1.50

        if any(w in q_norm for w in ["microservices", "vi dịch vụ", "microservice"]):
            if cat != "Công nghệ thông tin":
                delta -= 6.00
            if any(w in title_lower for w in ["ngành kinh doanh dịch vụ", "nâng tầm dịch vụ", "marketing dịch vụ", "kiến trúc dân dụng", "dịch vụ khách hàng"]):
                delta -= 8.00
            elif any(w in title_lower or w in desc_lower for w in ["phần mềm", "lập trình", "hệ thống", "cloud", "api"]):
                delta += 2.50

        if any(w in q_norm for w in ["ôn thi", "giáo trình", "đại học", "cao cấp", "toán rời rạc"]):
            if any(w in title_lower for w in ["mẫu giáo", "mầm non", "cho bé", "thiếu nhi", "trục số", "ươm mầm"]) or book_audience == 'trẻ em':
                delta -= 8.00
            if "toán rời rạc" in q_norm and any(w in title_lower or w in desc_lower for w in ["rời rạc", "cấu trúc dữ liệu", "thuật toán", "toán"]):
                delta += 2.00

        if any(w in q_norm for w in ["kỳ ảo", "fantasy", "thoát ly thực tại", "phép thuật"]):
            if any(w in title_lower for w in ["tài chính", "làm giàu", "chứng khoán", "kinh doanh", "bán hàng"]):
                delta -= 6.00
            elif cat == "Văn học – Tiểu thuyết" or any(w in title_lower or w in desc_lower for w in ["kỳ ảo", "phiêu lưu", "phép thuật", "harry potter"]):
                delta += 2.50

        if any(w in q_norm for w in ["liều thuốc tinh thần", "thuốc tinh thần"]):
            if any(w in title_lower for w in ["chữ hán", "hsk", "y học", "dược"]):
                delta -= 6.00
            elif any(w in title_lower or w in desc_lower for w in ["bình yên", "chữa lành", "an yên", "tâm hồn"]):
                delta += 2.50

        return delta

    def _generate_match_reason(self, work_info: Dict, analysis: Dict) -> str:
        intent = analysis.get('intent', 'EXACT_BOOK')
        book_moods = work_info.get('mood_tags', '')
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
            else:
                return f"Tác phẩm dung dị, dung lượng vừa phải, thích hợp đọc để thư giãn và phục hồi năng lượng."
        elif intent == 'CATEGORY_TOPIC':
            return f"Đầu sách tiêu biểu thuộc lĩnh vực {subcat or cat}, cung cấp kiến thức nền tảng và hữu ích."
        elif intent == 'LOCATION_STATUS':
            avail = work_info.get('available', 0)
            status_str = f"còn {avail} cuốn" if avail > 0 else "hiện tạm hết trên kệ"
            return f"Thông tin vị trí lưu trữ: {status_str}."
        else:
            return f"Tác phẩm nổi bật của {author} trong mảng {cat}."

    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        analysis = self.query_analyzer.analyze(query)
        intent = analysis.get('intent', 'EXACT_BOOK')
        filters = analysis.get('filters', {})
        
        # 1. OUT OF DOMAIN
        if intent == 'OUT_OF_DOMAIN':
            return {
                "query": query,
                "analysis": analysis,
                "results": [],
                "book_found": False,
                "message": "Câu hỏi của bạn không thuộc phạm vi tra cứu sách hoặc thư viện. Bạn vui lòng hỏi về các đầu sách, tác giả, thể loại hoặc nhờ gợi ý sách nhé!"
            }

        # 2. XỬ LÝ ĐẶC THÙ CHO LOCATION_STATUS
        target_loc_name = filters.get("title") or filters.get("target_title") or filters.get("quoted_title")
        if intent == 'LOCATION_STATUS':
            if target_loc_name:
                # Tìm tác phẩm chính xác trong catalog
                matched_wids = []
                for wid, winfo in self.work_catalog.items():
                    if is_title_matched(target_loc_name, winfo["base_title"]):
                        matched_wids.append((wid, winfo))
                
                if matched_wids:
                    best_wid, best_winfo = matched_wids[0]
                    first_copy = best_winfo['copies'][0] if best_winfo['copies'] else {}
                    analysis["target_location"] = {
                        "title": best_winfo["base_title"],
                        "author": best_winfo["author"],
                        "shelf": first_copy.get("shelf", "A"),
                        "floor": first_copy.get("floor", 1),
                        "position": first_copy.get("position", "A1-01"),
                        "available": best_winfo["available"],
                        "total": best_winfo["total"]
                    }
                    loc_result = [{
                        "work_id": best_wid,
                        "book_id": first_copy.get("book_id", best_wid),
                        "title": best_winfo["base_title"],
                        "author": best_winfo["author"],
                        "category": best_winfo["category"],
                        "subcategory": best_winfo["subcategory"],
                        "description": best_winfo["description"],
                        "mood_tags": best_winfo["mood_tags"],
                        "reading_effort": best_winfo["reading_effort"],
                        "floor": first_copy.get("floor", 1),
                        "shelf": first_copy.get("shelf", "A"),
                        "position": first_copy.get("position", "A1-01"),
                        "available_copies": best_winfo["available"],
                        "total_copies": best_winfo["total"],
                        "score": 1.0,
                        "match_reason": self._generate_match_reason(best_winfo, analysis)
                    }]
                    return {
                        "query": query,
                        "analysis": analysis,
                        "results": loc_result,
                        "book_found": True,
                        "total_found": 1
                    }
                else:
                    # Sách không có trong thư viện
                    return {
                        "query": query,
                        "analysis": analysis,
                        "results": [],
                        "book_found": False,
                        "requested_title": target_loc_name,
                        "message": f"Rất tiếc, cuốn sách '{target_loc_name}' hiện không có trong hệ thống thư viện."
                    }
            elif filters.get("shelf"):
                s_letter = filters["shelf"].upper()
                s_info = SHELF_INFO.get(s_letter, {"floor": 1, "category": "Kho sách chung"})
                analysis["shelf_location"] = {
                    "shelf": s_letter,
                    "floor": s_info["floor"],
                    "category": s_info["category"]
                }
                return {
                    "query": query,
                    "analysis": analysis,
                    "results": [],
                    "book_found": True,
                    "message": f"Khu vực Kệ {s_letter} nằm tại Tầng {s_info['floor']}."
                }

        # 3. CHẠY TRUY VẤN VỚI POSITIVE QUERY
        pos_query = analysis.get('positive_query') or query
        queries_to_run = [(pos_query, 1.0)]
        if intent == 'EMOTIONAL_CONTEXT':
            for eq in analysis.get('expanded_queries', []):
                if eq != pos_query:
                    queries_to_run.append((eq, 0.75))
                    
        rrf_scores = {}
        for q_text, q_weight in queries_to_run:
            bm25_res = self._search_bm25_single(q_text, top_k=60)
            e5_res = self._search_e5_single(q_text, top_k=60)
            
            seen_bm25_works = {}
            for item in bm25_res:
                wid = item['work_id']
                if wid not in seen_bm25_works:
                    seen_bm25_works[wid] = item['rank']
                    
            for wid, rank in seen_bm25_works.items():
                contrib = q_weight * (1.0 / (self.k + rank))
                rrf_scores[wid] = rrf_scores.get(wid, 0.0) + contrib
                
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
                "book_found": False,
                "message": "Thư viện hiện chưa tìm thấy đầu sách nào phù hợp với yêu cầu của bạn."
            }

        # Áp dụng Soft Reranking
        scored_candidates = []
        for wid, base_rrf in rrf_scores.items():
            w_info = self.work_catalog[wid]
            soft_delta = self._calculate_soft_rerank(w_info, analysis)
            final_score = base_rrf + (soft_delta * 0.08)
            scored_candidates.append((wid, final_score, base_rrf, soft_delta))
            
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Lọc danh mục cho EMOTIONAL_CONTEXT
        if intent == 'EMOTIONAL_CONTEXT':
            non_tech = [
                c for c in scored_candidates 
                if self.work_catalog[c[0]].get('category') not in ['Công nghệ thông tin', 'Khoa học – Công nghệ']
            ]
            if len(non_tech) >= top_k:
                scored_candidates = non_tech
                
            pref_cats = analysis.get('preferred_categories', [])
            if pref_cats:
                pref_matches = [
                    c for c in scored_candidates 
                    if any(pc in self.work_catalog[c[0]].get('category', '') for pc in pref_cats)
                ]
                if len(pref_matches) >= top_k:
                    scored_candidates = pref_matches

        # Lọc Category rõ ràng
        target_cat = analysis.get('filters', {}).get('category')
        is_exact = bool(analysis.get('filters', {}).get('title') or analysis.get('filters', {}).get('target_title'))
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

        # 4. KIỂM TRA ĐỘ KHỚP THỰC TẾ (CONFIDENCE MATCHING CHO EXACT_BOOK)
        target_book_name = filters.get("title") or filters.get("target_title") or filters.get("quoted_title")
        target_author_name = filters.get("target_author") or filters.get("author")
        
        book_found = True
        matched_work_wid = None
        
        if target_book_name:
            # Rà soát xem trong top kết quả có cuốn nào thực sự khớp tiêu đề không
            for wid, final_score, base_rrf, soft_delta in scored_candidates[:20]:
                w_info = self.work_catalog[wid]
                if is_title_matched(target_book_name, w_info["base_title"]):
                    matched_work_wid = wid
                    book_found = True
                    break
            else:
                book_found = False
                
        elif target_author_name and not filters.get("author"):
            # Người dùng tìm tác giả nhưng tác giả không có trong catalog
            book_found = False

        # Nếu tìm thấy cuốn khớp đích danh, đưa cuốn đó lên Top 1
        if matched_work_wid:
            matched_tuple = next(c for c in scored_candidates if c[0] == matched_work_wid)
            scored_candidates.remove(matched_tuple)
            scored_candidates.insert(0, matched_tuple)

        # 5. KHỬ TRÙNG LẶP ẤN BẢN VÀ LẮP RÁP KẾT QUẢ
        seen_title_keys = set()
        author_counts = {}
        filtered_results = []
        allow_author_flood = bool(analysis.get('filters', {}).get('author'))
        
        for wid, final_score, base_rrf, soft_delta in scored_candidates:
            w_info = self.work_catalog[wid]
            auth = w_info.get('author', 'Unknown')
            raw_title = w_info.get('base_title', '')
            
            # Khử trùng lặp các ấn bản na ná nhau (vd: combo, STK, bản quyền)
            title_key = normalize_title_for_dedup(raw_title)
            if title_key in seen_title_keys and len(filtered_results) < top_k:
                continue
            seen_title_keys.add(title_key)
            
            if not allow_author_flood and auth not in ['Không rõ tác giả', 'Nhiều tác giả', 'Unknown']:
                current_cnt = author_counts.get(auth, 0)
                if current_cnt >= 2 and len(filtered_results) < top_k:
                    continue
                author_counts[auth] = current_cnt + 1
                
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
            "book_found": book_found,
            "requested_title": target_book_name,
            "requested_author": target_author_name,
            "total_found": len(rrf_scores)
        }
