import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from src.embedding import EmbeddingEngine
from src.data_processing import load_and_verify_dataset

def main():
    print("=" * 60)
    print("AI SEMANTIC SEARCH: EMBEDDING & INDEXING PIPELINE")
    print("Senior AI Engineer Implementation")
    print("=" * 60)

    dataset_path = "dataset/cleaned_books_dataset.csv"
    print(f"[*] Loading cleaned dataset: {dataset_path}...")
    df = load_and_verify_dataset(dataset_path)
    print(f"[+] Loaded {len(df)} books successfully.")

    t0 = time.time()
    emb_engine = EmbeddingEngine(model_name="intfloat/multilingual-e5-small", cache_dir="embeddings")
    
    print("[*] Generating dense embeddings (E5 format: 'passage: ...')...")
    embeddings, book_ids = emb_engine.get_or_build_embeddings(df, force_rebuild=True)
    
    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print("INDEXING PIPELINE COMPLETED")
    print("=" * 60)
    print(f"Total Books Indexed: {len(book_ids)}")
    print(f"Embedding Shape: {embeddings.shape}")
    print(f"Vector Dimensions: {embeddings.shape[1]}")
    print(f"Time Elapsed: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
    
    # Check L2 normalization
    norms = np.linalg.norm(embeddings, axis=1)
    print(f"Embedding L2 norm min/max/mean: {norms.min():.4f} / {norms.max():.4f} / {norms.mean():.4f}")
    assert np.allclose(norms, 1.0, atol=1e-3), "Embeddings should be unit length (L2 normalized)!"
    print("[+] All sanity checks passed perfectly!")

if __name__ == '__main__':
    main()
