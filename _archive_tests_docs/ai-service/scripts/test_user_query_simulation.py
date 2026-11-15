import os
import sys
import json
import time
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("TEST THỰC TẾ: ĐỨNG TRÊN VAI TRÒ NGƯỜI DÙNG KIOSK")
print("CÂU HỎI: 'giờ tôi đang rất buồn, tôi cần 1 cuốn sách giúp tôi giải trí vui vẻ hơn'")
print("=" * 80)

DATASET_CLEAN = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'cleaned_books_dataset.csv')
DATASET_ENRICHED = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'books_enriched.csv')
EMB_PATH = os.path.join(os.path.dirname(__file__), '..', 'embeddings', 'embeddings.npy')
IDS_PATH = os.path.join(os.path.dirname(__file__), '..', 'embeddings', 'book_ids.json')

df_clean = pd.read_csv(DATASET_CLEAN)
df_clean['Book_ID'] = df_clean['Book_ID'].astype(str)
book_clean_dict = df_clean.set_index('Book_ID').to_dict(orient='index')

df_enriched = pd.read_csv(DATASET_ENRICHED)
df_enriched['Book_ID'] = df_enriched['Book_ID'].astype(str)
book_enriched_dict = df_enriched.set_index('Book_ID').to_dict(orient='index')

raw_embeddings = np.load(EMB_PATH)
with open(IDS_PATH, 'r', encoding='utf-8') as f:
    book_ids = json.load(f)

# Model
model = SentenceTransformer("intfloat/multilingual-e5-small")

user_query = "giờ tôi đang rất buồn, tôi cần 1 cuốn sách giúp tôi giải trí vui vẻ hơn"

# 1. BASELINE E5 THUẦN (HỆ THỐNG TRƯỚC ĐÂY KHI CHƯA LÀM GÌ)
q_emb = model.encode([f"query: {user_query}"], normalize_embeddings=True)[0]
raw_sims = cosine_similarity([q_emb], raw_embeddings)[0]
raw_top_indices = np.argsort(raw_sims)[::-1][:5]

print("\n--- 1. KẾT QUẢ TỪ BASELINE E5 CŨ (TRƯỚC KHI CẢI TIẾN) ---")
for rank, idx in enumerate(raw_top_indices, 1):
    bid = book_ids[idx]
    b = book_clean_dict[bid]
    print(f"Top {rank}: [{bid}] {b['Title']} - {b['Author']}")
    print(f"        Thể loại: {b['Category']} - {b['Subcategory']}")
    print(f"        Vị trí: Tầng {b['Floor']}, Kệ {b['Shelf']}, Ô {b['Position']} | Còn {b['Available_Copies']}/{b['Total_Copies']} cuốn")
    print(f"        Score E5: {round(float(raw_sims[idx]), 4)}")
    print(f"        Mô tả rút gọn: {str(b['Description'])[:100]}...\n")

# 2. XEM TRONG DATASET LÀM GIÀU (ENRICHED DATASET) CÓ NHỮNG CUỐN NÀO THỰC SỰ 'VUI VẺ', 'HÀI HƯỚC', 'GIẢI TRÍ'
print("\n--- 2. CÁC CUỐN SÁCH THỰC SỰ 'VUI VẺ / HÀI HƯỚC / GIẢI TRÍ' TRONG KHO SÁCH ENRICHED ---")
fun_books = df_enriched[
    df_enriched['mood_tags'].str.contains('vui vẻ|hài hước', na=False) &
    (df_enriched['Category'].isin(['Văn học – Tiểu thuyết', 'Kỹ năng sống – Phát triển bản thân', 'Thiếu nhi']))
]

# Tính thử độ tương đồng semantic của query với trường search_text đã làm giàu của các cuốn sách vui vẻ
fun_search_texts = fun_books['search_text'].tolist()
fun_passages = [f"passage: {t}" for t in fun_search_texts]
fun_embs = model.encode(fun_passages, normalize_embeddings=True)

fun_sims = cosine_similarity([q_emb], fun_embs)[0]
top_fun_idx = np.argsort(fun_sims)[::-1][:5]

for rank, idx in enumerate(top_fun_idx, 1):
    b = fun_books.iloc[idx]
    print(f"Gợi ý {rank}: [{b['Book_ID']}] {b['Title']} - {b['valid_author'] if pd.notna(b['valid_author']) and b['valid_author'] else b['Author']}")
    print(f"        Thể loại: {b['Category']} - {b['Subcategory']}")
    print(f"        Mood: {b['mood_tags']} | Nỗ lực: {b['reading_effort']} | Ý định: {b['reader_intent']}")
    print(f"        Vị trí: Tầng {b['Floor']}, Kệ {b['Shelf']}, Ô {b['Position']} | Còn {b['Available_Copies']}/{b['Total_Copies']} cuốn")
    print(f"        Nội dung: {b['summary_vi']}")
    print(f"        Score E5 trên search_text: {round(float(fun_sims[idx]), 4)}\n")
