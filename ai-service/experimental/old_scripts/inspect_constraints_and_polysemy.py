import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")

print(f"Total books: {len(df)}")
print("Categories:", df['Category'].value_counts().to_dict())

# Check Nguyen Nhat Anh books
nna_books = df[df['Author'].str.contains('Nguyễn Nhật Ánh', case=False, na=False)]
print(f"\nNguyễn Nhật Ánh books count: {len(nna_books)}")
print("Sample titles:", nna_books['Title'].head(5).tolist())

# Check Python books
python_books = df[df['Title'].str.contains('Python', case=False, na=False) | df['Description'].str.contains('Python', case=False, na=False)]
print(f"\nPython books count: {len(python_books)}")
print("Sample Python titles:", python_books[['Book_ID', 'Title', 'Author']].head(5).to_dict(orient='records'))

# Check Java books
java_books = df[df['Title'].str.contains('Java', case=False, na=False) | df['Description'].str.contains('Java', case=False, na=False)]
print(f"\nJava books count: {len(java_books)}")
print("Sample Java titles:", java_books[['Book_ID', 'Title', 'Author']].head(5).to_dict(orient='records'))

# Check Spring Boot books
spring_books = df[df['Title'].str.contains('Spring', case=False, na=False) | df['Description'].str.contains('Spring', case=False, na=False)]
print(f"\nSpring books count: {len(spring_books)}")
print("Sample Spring titles:", spring_books[['Book_ID', 'Title', 'Author']].head(5).to_dict(orient='records'))

# Check Ove book
ove_books = df[df['Title'].str.contains('Ove', case=False, na=False) | df['Description'].str.contains('Ove', case=False, na=False)]
print(f"\nOve books count: {len(ove_books)}")
print("Sample Ove titles:", ove_books[['Book_ID', 'Title', 'Author']].head(5).to_dict(orient='records'))

# Check Psychology for kids / parents
kid_psych_books = df[df['Description'].str.contains('trẻ em|phụ huynh|cha mẹ|con cái', case=False, na=False) & df['Category'].str.contains('Tâm lý|Gia đình|Nuôi dạy', case=False, na=False)]
print(f"\nKid/Parent psychology books count: {len(kid_psych_books)}")
print("Sample Kid/Parent titles:", kid_psych_books[['Book_ID', 'Title', 'Author']].head(5).to_dict(orient='records'))

# Check AI books
ai_books = df[df['Title'].str.contains('Trí Tuệ Nhân Tạo|AI', case=False, na=False)]
print(f"\nAI books count: {len(ai_books)}")
print("Sample AI titles:", ai_books[['Book_ID', 'Title', 'Author']].head(5).to_dict(orient='records'))
