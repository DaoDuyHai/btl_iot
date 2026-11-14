import json
import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.query_understanding import QueryAnalyzer
from src.hybrid_search_v2 import HybridSearchEngineV2
from src.embedding import EmbeddingEngine

with open(os.path.join(BASE_DIR, "dataset", "test_set_150.json"), "r", encoding="utf-8") as f:
    tdata = json.load(f)

df = pd.read_csv(os.path.join(BASE_DIR, "dataset", "books_enriched.csv"))
qa = QueryAnalyzer(catalog_df=df)

print("=" * 80)
print("1. KIỂM TRA 10 CÂU OOD VỚI QUERY ANALYZER:")
print("=" * 80)
for q in tdata["out_of_domain_queries"]:
    analysis = qa.analyze(q["query"])
    intent = analysis.get("intent")
    print(f"[{q['id']}] '{q['query']}'")
    print(f"     -> Intent: {intent}")

print("\n" + "=" * 80)
print("2. KIỂM TRA 3 CÂU EMOTIONAL BỊ BAD-HIT:")
print("=" * 80)
# Tải benchmark_results_150.json
with open(os.path.join(BASE_DIR, "benchmark_results_150.json"), "r", encoding="utf-8") as f:
    bdata = json.load(f)

for fail in bdata.get("failure_samples", []):
    if fail.get("config") == "Hybrid Engine V2 (Proposed)" and fail.get("category") == "EMOTIONAL":
        print(f"Query: \"{fail.get('query')}\"")
        print(f"  -> Top 1: {fail.get('top1_returned')} (Category: {fail.get('top1_cat')})")
        print(f"  -> Reason: {fail.get('reason')}")
