import json
import random
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_PATH = os.path.join(BASE_DIR, "dataset", "test_set_150.json")

with open(TEST_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 80)
print("BƯỚC 5: THỐNG KÊ CHI TIẾT TẬP TEST 150 CÂU & 30 CÂU MẪU (SEED 2026)")
print("=" * 80)

print("\n1. Phân bố theo Nhóm chính:")
for k, v in data.items():
    print(f"   - {k:25s}: {len(v)} câu")

# Thống kê Persona
personas = {}
types = {}
categories = {}
all_items = []

for k, v in data.items():
    for item in v:
        item["group"] = k
        all_items.append(item)
        p = item.get("persona", "hệ thống")
        personas[p] = personas.get(p, 0) + 1
        t = item.get("type", item.get("state", "other"))
        types[t] = types.get(t, 0) + 1
        c = item.get("category", item.get("target_category", "Đa thể loại / Ngoài phạm vi"))
        categories[c] = categories.get(c, 0) + 1

print("\n2. Phân bố theo Đối tượng người đọc (Persona):")
for p, count in sorted(personas.items(), key=lambda x: -x[1]):
    print(f"   - {p:25s}: {count:2d} câu ({count/1.5:.1f}%)")

print("\n3. Phân bố theo Thể loại (Category):")
for c, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"   - {c:35s}: {count:2d} câu ({count/1.5:.1f}%)")

random.seed(2026)
sample_30 = random.sample(all_items, 30)

print("\n4. 30 Câu ngẫu nhiên kiểm tra (Seed 2026) phủ rộng các nhóm:")
print("-" * 80)
for i, item in enumerate(sample_30, 1):
    q = item["query"]
    grp = item["group"]
    typ = item.get("type", item.get("state", "N/A"))
    persona = item.get("persona", "N/A")
    cat = item.get("category", item.get("target_category", "N/A"))
    print(f"{i:02d}. [{item['id']}] [{grp:18s}] ({persona:13s}) | \"{q}\"")
    print(f"    -> Thể loại/Mục tiêu: {cat} | Kiểu hỏi/Trạng thái: {typ}")
print("-" * 80)
