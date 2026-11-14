import sys
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "venv", "Lib", "site-packages"))

from src.hybrid_search_v2 import HybridSearchEngineV2
from src.query_understanding import QueryAnalyzer
from src.embedding import EmbeddingEngine

df = pd.read_csv(os.path.join(BASE_DIR, 'dataset', 'books_enriched.csv'))
embs = np.load(os.path.join(BASE_DIR, 'embeddings', 'embeddings_enriched.npy'))
embed_engine = EmbeddingEngine()
qa = QueryAnalyzer(catalog_df=df)
engine = HybridSearchEngineV2(df, embs, embed_engine, qa)

query = "nay tôi tâm trạng không tốt, tôi cần 1 cuốn truyện hài"
res = engine.search(query, top_k=5)
print(f"QUERY: '{query}'")
print(f"INTENT: {res['analysis']['intent']}")
print(f"TARGET MOODS: {res['analysis']['target_moods']}")
print("-" * 75)
for r in res['results']:
    author = r['author'] if r['author'] else "Nhiều tác giả"
    print(f"[{r['book_id']}] {r['title']} - Tác giả: {author}")
    print(f"   Thể loại: {r['category']} - {r['subcategory']}")
    print(f"   Mood: [{r['mood_tags']}] | Effort: [{r['reading_effort']}] | Điểm: {r['score']}")
    print(f"   Vị trí: Tầng {r['floor']}, Kệ {r['shelf']}, Ô {r['position']} (Sẵn có: {r['available_copies']})")
    print(f"   Lý do: {r['match_reason']}")
    print()
