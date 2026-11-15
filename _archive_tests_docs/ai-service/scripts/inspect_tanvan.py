import pandas as pd
df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')
tv = df[df['Subcategory'] == 'Truyện ngắn - Tản văn - Tạp Văn']
print(f"Tổng số sách Tản văn: {len(tv)}")
for idx, row in tv.head(10).iterrows():
    print(f"[{row['Book_ID']}] {row['Title']} - {row['Author']}")
