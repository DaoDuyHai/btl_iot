import json
import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "venv", "Lib", "site-packages"))

from src.hybrid_search_v2 import HybridSearchEngineV2
from src.query_understanding import QueryAnalyzer
from src.embedding import EmbeddingEngine

with open(os.path.join(BASE_DIR, "dataset", "test_set_150.json"), "r", encoding="utf-8") as f:
    tdata = json.load(f)

df = pd.read_csv(os.path.join(BASE_DIR, "dataset", "books_enriched.csv"))
embs = np = __import__("numpy").load(os.path.join(BASE_DIR, "embeddings", "embeddings_enriched.npy"))
embed_engine = EmbeddingEngine()
qa = QueryAnalyzer(catalog_df=df)
engine = HybridSearchEngineV2(df, embs, embed_engine, qa)

print("=== KIỂM TRA TỪNG CÂU EMOTIONAL VỚI HYBRID V2 ===")
for q in tdata["emotional_queries"]:
    res = engine.search(q["query"], top_k=5)
    books = res.get("results", [])
    
    bad_cats = [c.lower() for c in q.get("bad_categories", [])]
    bad_keywords = [k.lower() for k in q.get("bad_keywords", [])]
    
    bad_books = []
    for b in books:
        b_cat = b["category"].lower()
        b_t = b["title"].lower()
        b_d = b["description"].lower()
        
        is_bad = False
        reason = ""
        if b_cat in bad_cats:
            is_bad = True
            reason = f"bad category: {b['category']}"
        else:
            for bk in bad_keywords:
                if bk in b_t or bk in b_d:
                    is_bad = True
                    reason = f"bad keyword '{bk}' in {b['title']}"
                    break
        if is_bad:
            bad_books.append((b["title"], b["category"], reason))
            
    if bad_books:
        print(f"\n[BAD HIT] ID: {q['id']} | Query: \"{q['query']}\"")
        for bt, bc, br in bad_books:
            print(f"   -> Bad book: {bt} ({bc}) - {br}")
