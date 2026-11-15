from inspect_full_filtered_moods import relax_records, healing_records

print("=" * 80)
print(f"DANH SÁCH TOÀN BỘ {len(relax_records)} SÁCH THƯ GIÃN:")
print("=" * 80)
for r in relax_records:
    print(f"[{r['book_id']}] {r['title']} | {r['category']} | {r['mood_tags']}")
    print(f"   -> 1 câu đầu: {r['first_sentence']}\n")

print("=" * 80)
print(f"DANH SÁCH TOÀN BỘ {len(healing_records)} SÁCH CHỮA LÀNH:")
print("=" * 80)
for h in healing_records:
    print(f"[{h['book_id']}] {h['title']} | {h['category']} | {h['mood_tags']}")
    print(f"   -> 1 câu đầu: {h['first_sentence']}\n")
