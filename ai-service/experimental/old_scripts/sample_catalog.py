import pandas as pd

df = pd.read_csv('dataset/cleaned_books_dataset.csv')
print("=== CATEGORY DISTRIBUTION ===")
print(df['Category'].value_counts())

print("\n=== SAMPLE BOOKS PER CATEGORY ===")
for cat, grp in df.groupby('Category'):
    print(f"\n--- {cat} ({len(grp)} cuốn) ---")
    for _, r in grp.head(3).iterrows():
        print(f"  [{r['Book_ID']}] {r['Title']} | TG: {r['Author']} | Sub: {r['Subcategory']}")
