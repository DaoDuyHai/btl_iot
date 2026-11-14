import json

data = json.load(open('ai-service/step3_test_results.json', encoding='utf-8'))
for q in ['tiếng anh', 'tiếng nhật']:
    v = data[q]
    print(f"================================================================================")
    print(f"QUERY: '{q}'")
    print(f"Intent: {v['intent']} | Thời gian: {v['latency_ms']:.1f}ms")
    print(f"--------------------------------------------------------------------------------")
    for r in v['results']:
        author = r['author'] if r['author'] else "Nhiều tác giả"
        print(f"#{r['rank']} [{r['book_id']}] {r['title']} - Tác giả: {author}")
        print(f"   Thể loại: {r['category']} - {r['subcategory']}")
        print(f"   Nhãn: Mood=[{r['mood_tags']}] | Nỗ lực=[{r['reading_effort']}] | Điểm={r['score']}")
        print(f"   Vị trí: Tầng {r['floor']}, Kệ {r['shelf']}, Ô {r['position']} | Số bản sẵn có: {r['available_copies']}")
        print(f"   Lý do gợi ý: {r['match_reason']}")
        print()
