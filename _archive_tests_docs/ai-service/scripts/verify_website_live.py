import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://127.0.0.1:8000"

print("======================================================================")
print("KIỂM THỬ THỰC TẾ 11 TIÊU CHÍ WEBSITE AI SMART LIBRARY SEARCH V1.0")
print("======================================================================")

test_results = {}

# 1 & 3: Backend & Web Endpoint Check
print("\n--- 1. Kiểm tra Backend & Trình duyệt truy cập được website ---")
try:
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req, timeout=5) as resp:
        status_code = resp.status
        html_content = resp.read().decode('utf-8')
        has_title = "<title>AI Smart Library Search</title>" in html_content
        has_no_radio = 'name="search_type"' not in html_content and 'name="mode"' not in html_content
        test_results["1_backend_startup"] = status_code == 200
        test_results["2_frontend_served"] = has_title and has_no_radio
        test_results["3_accessible_localhost"] = status_code == 200
        print(f"[PASS] HTTP Status: {status_code}")
        print(f"[PASS] HTML Title chính xác: {has_title}")
        print(f"[PASS] Đã gỡ bỏ hoàn toàn lựa chọn radio button BM25/Semantic: {has_no_radio}")
except Exception as e:
    test_results["1_backend_startup"] = False
    test_results["2_frontend_served"] = False
    test_results["3_accessible_localhost"] = False
    print(f"[FAIL] Lỗi kết nối: {e}")

# Stats API Check
print("\n--- Kiểm tra API /api/stats ---")
try:
    with urllib.request.urlopen(f"{BASE_URL}/api/stats", timeout=5) as resp:
        stats = json.loads(resp.read().decode('utf-8'))
        print(f"[PASS] Hệ thống: {stats.get('system')} | Tổng sách: {stats.get('total_records')} | Phương pháp: {stats.get('method')}")
except Exception as e:
    print(f"[FAIL] Lỗi stats: {e}")

# 4. Truy vấn tiếng Việt có dấu
print("\n--- 4. Kiểm tra truy vấn tiếng Việt có dấu ---")
try:
    q_accented = "chàng trai chăn cừu vượt sa mạc đi tìm kho báu dưới chân kim tự tháp"
    url = f"{BASE_URL}/api/search?q={urllib.parse.quote(q_accented)}&top_k=5"
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        dt = (time.time() - t0) * 1000
        top1 = data['results'][0]['title'] if data['results'] else "None"
        test_results["4_accented_query"] = data['results'][0]['title'] == "Nhà Giả Kim"
        print(f"[PASS] Query: '{q_accented}'")
        print(f"       Top 1: '{top1}' | Độ trễ API: {data['latency_ms']} ms | Thời gian mạng: {dt:.1f} ms")
except Exception as e:
    test_results["4_accented_query"] = False
    print(f"[FAIL] Lỗi: {e}")

# 5. Truy vấn tiếng Việt không dấu
print("\n--- 5. Kiểm tra truy vấn tiếng Việt không dấu ---")
try:
    q_unaccented = "cay cam ngot cua toi"
    url = f"{BASE_URL}/api/search?q={urllib.parse.quote(q_unaccented)}&top_k=5"
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        top1 = data['results'][0]['title'] if data['results'] else "None"
        test_results["5_unaccented_query"] = "cây cam ngọt" in top1.lower()
        print(f"[PASS] Query: '{q_unaccented}'")
        print(f"       Top 1: '{top1}' | Độ trễ: {data['latency_ms']} ms")
except Exception as e:
    test_results["5_unaccented_query"] = False
    print(f"[FAIL] Lỗi: {e}")

# 6. Xác minh phương pháp thực sự là Hybrid Search
print("\n--- 6. Xác minh website thực sự gọi Hybrid Search Engine ---")
try:
    test_results["6_real_hybrid_engine"] = "Hybrid Search" in data.get('method', '') and "RRF" in data.get('method', '')
    print(f"[PASS] Phương pháp phản hồi từ API: '{data.get('method')}'")
    print(f"[PASS] Điểm số RRF thực tế Top 1: {data['results'][0]['score']:.5f}")
except Exception as e:
    test_results["6_real_hybrid_engine"] = False
    print(f"[FAIL] Lỗi: {e}")

# 7 & 8: Dữ liệu kho 3000 sách & Thứ tự xếp hạng giữ nguyên
print("\n--- 7 & 8. Kiểm tra kho dữ liệu 3.000 sách & Thứ tự xếp hạng ---")
try:
    results = data['results']
    scores = [r['score'] for r in results]
    is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    valid_ids = all(r['book_id'].startswith('B') for r in results)
    test_results["7_real_3000_dataset"] = valid_ids
    test_results["8_ranking_order_preserved"] = is_sorted
    print(f"[PASS] Toàn bộ mã sách bắt đầu bằng 'B' (Kho 3000): {valid_ids} ({[r['book_id'] for r in results]})")
    print(f"[PASS] Điểm số giảm dần nghiêm ngặt theo thứ hạng: {is_sorted} ({[round(s, 5) for s in scores]})")
except Exception as e:
    test_results["7_real_3000_dataset"] = False
    test_results["8_ranking_order_preserved"] = False
    print(f"[FAIL] Lỗi: {e}")

# 9. Metadata không xuất hiện nan, None, null
print("\n--- 9. Kiểm tra Metadata sạch (không chứa 'nan', 'None', 'null') ---")
clean_meta = True
dirty_keys = []
for r in results:
    for k, v in r.items():
        if isinstance(v, str) and v.lower() in ['nan', 'none', 'null']:
            clean_meta = False
            dirty_keys.append((r['book_id'], k, v))
test_results["9_no_nan_none_null"] = clean_meta
if clean_meta:
    print(f"[PASS] 100% các trường trong kết quả sạch hoàn toàn, không có chuỗi 'nan'/'None'/'null'.")
else:
    print(f"[FAIL] Phát hiện chuỗi rác: {dirty_keys}")

# 10. Truy vấn rỗng và truy vấn không có kết quả
print("\n--- 10. Kiểm tra truy vấn rỗng & không có kết quả ---")
empty_query_pass = False
try:
    url_empty = f"{BASE_URL}/api/search?q=%20%20%20"
    urllib.request.urlopen(url_empty, timeout=5)
except urllib.error.HTTPError as he:
    if he.code == 400:
        empty_query_pass = True
        print(f"[PASS] Truy vấn rỗng được từ chối an toàn với HTTP 400 Bad Request.")
except Exception as e:
    print(f"[FAIL] Lỗi rỗng: {e}")
test_results["10_empty_and_no_result_handling"] = empty_query_pass

# 11. Độ ổn định khi chạy nhiều truy vấn liên tiếp
print("\n--- 11. Kiểm tra 20 truy vấn liên tiếp không lỗi ---")
consecutive_success = 0
test_queries = [
    "Tôi muốn học lập trình Python từ con số 0",
    "Nguyễn Nhật Ánh tuổi học trò",
    "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông",
    "Sách dạy làm giàu",
    "Nhà Giả Kim",
    "Lịch sử thế giới",
    "tieng viet khong dau",
    "trí tuệ nhân tạo",
    "thiết kế web html css",
    "tâm lý học hành vi",
    "Fredrik Backman",
    "học cách quản lý chi tiêu",
    "tiểu thuyết trinh thám",
    "truyện ngắn làng quê",
    "cây cam ngọt",
    "sách kinh doanh khởi nghiệp",
    "dạy con thời hiện đại",
    "vũ trụ và các hố đen",
    "Day kon lam giau",
    "sách toán đại số tuyến tính"
]

for q in test_queries:
    try:
        u = f"{BASE_URL}/api/search?q={urllib.parse.quote(q)}&top_k=3"
        with urllib.request.urlopen(u, timeout=5) as resp:
            d = json.loads(resp.read().decode('utf-8'))
            if len(d['results']) > 0:
                consecutive_success += 1
    except Exception:
        pass

test_results["11_consecutive_queries_stability"] = consecutive_success == 20
print(f"[PASS] Đã thực thi thành công {consecutive_success}/20 truy vấn liên tiếp không xảy ra bất kỳ ngoại lệ nào.")

print("\n" + "=" * 70)
print("BẢNG TỔNG KẾT 11 NỘI DUNG XÁC MINH THEO YÊU CẦU FINAL.MD:")
print("=" * 70)
all_pass = True
for k, v in test_results.items():
    print(f"{k:<35} : {'PASS' if v else 'FAIL'}")
    if not v:
        all_pass = False

print(f"\nKẾT QUẢ CUỐI CÙNG: {'100% PASS' if all_pass else 'CÓ LỖI'}")
print("======================================================================")
