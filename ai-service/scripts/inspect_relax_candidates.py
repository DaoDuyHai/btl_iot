import pandas as pd
df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')
for bid in ['B0027', 'B0458', 'B0036', 'B0108']:
    row = df[df['Book_ID'] == bid]
    if len(row) > 0:
        r = row.iloc[0]
        print(f"=== [{r['Book_ID']}] {r['Title']} ===")
        print(f"Subcategory: {r['Subcategory']}")
        print(f"Desc: {r['Description'][:250]}\n")
