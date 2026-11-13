import json
import pandas as pd
import numpy as np

with open('tests/verified_ground_truth_110.json', 'r', encoding='utf-8') as f:
    gt_cases = json.load(f)

df = pd.read_csv('dataset/cleaned_books_dataset.csv')

print("=" * 70)
print("KIỂM TOÁN TẬP GROUND TRUTH (VERIFIED RELEVANCE CHECK)")
print("=" * 70)

high_count_cases = []
for tc in gt_cases:
    cnt = len(tc['rel_ids'])
    if cnt > 20:
        high_count_cases.append((tc['id'], tc['query'], cnt, tc['group']))

print(f"Số câu hỏi có > 20 sách gán nhãn: {len(high_count_cases)}")
for qid, q, cnt, grp in high_count_cases:
    print(f"  [{qid}] '{q}' ({grp}) -> {cnt} sách liên quan")
