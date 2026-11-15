import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np

# Load test data records
with open('tests/verified_ground_truth_110.json', 'r', encoding='utf-8') as f:
    gt_cases = json.load(f)

# Let's inspect the distribution of margin_cos and top1_cos
from scripts.test_ood_detection import data

in_d = data[data['is_ood'] == 0]
ood = data[data['is_ood'] == 1]

print("=== DETAILED OOD ANALYSIS ===")
print("OOD Margin values:")
for _, r in ood.iterrows():
    print(f"  {r['id']}: Cos={r['top1_cos']:.4f}, Margin={r['margin_cos']:.4f} | '{r['query']}'")

print("\nIn-Domain Margin values distribution:")
print(in_d['margin_cos'].describe())

# Check how many in-domain have margin < 0.012 and cos < 0.84
ambiguous_in_d = in_d[(in_d['margin_cos'] <= 0.0115) & (in_d['top1_cos'] < 0.84)]
print(f"\nIn-Domain cases that fall into (Margin <= 0.0115 and Cos < 0.84): {len(ambiguous_in_d)}/100")
for _, r in ambiguous_in_d.iterrows():
    print(f"  {r['id']}: Cos={r['top1_cos']:.4f}, Margin={r['margin_cos']:.4f} | '{r['query']}'")
