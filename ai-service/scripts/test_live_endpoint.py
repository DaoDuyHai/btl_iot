import urllib.request
import urllib.parse
import json

queries = [
    "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông",
    "Mắt Biếc",
    "sách về nỗi đau chiến tranh và người lính trở về",
    "lập trình trí tuệ nhân tạo và học máy bằng python"
]

for query in queries:
    url = f"http://127.0.0.1:8000/api/search?q={urllib.parse.quote(query)}&mode=hybrid&top_k=2"
    req = urllib.request.urlopen(url)
    data = json.loads(req.read().decode())
    print(f"\n[QUERY]: '{query}' (Mode: {data['mode']}, Latency: {data['latency_ms']}ms)")
    for r in data['results']:
        print(f"  #{r['rank']} [Score: {r['score']:.4f}] {r['title']} - {r['author']}")
        print(f"     -> Kệ {r['shelf']}, Tầng {r['floor']}, Vị trí {r['position']} | Khả dụng: {r['available']}/{r['total']}")
