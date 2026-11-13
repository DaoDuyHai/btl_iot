import pandas as pd
df = pd.read_csv('ai-service/dataset/cleaned_books_dataset.csv')
b = df[df['Book_ID'] == 'B0024'].iloc[0]
print("B0024 Description:")
print(b['Description'])
