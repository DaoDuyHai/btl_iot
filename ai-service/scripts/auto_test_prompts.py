# -*- coding: utf-8 -*-
"""
auto_test_prompts.py
Trình kiểm thử tự động 100 câu hỏi trong TEST_PROMPTS_100.md bằng Python AI Service.
Tự động gọi Thủ thư AI (E5 + BM25 + Query Understanding + Response Generator)
và tự động ghi nhận toàn bộ lịch sử Q&A vào CONVERSATION_HISTORY.md.
"""

import os
import sys
import io
import time
import json
import re
import urllib.request
import urllib.error

# Đảm bảo in UTF-8 trên console Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_ROOT = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
_venv_site = os.path.join(BASE_DIR, "venv", "Lib", "site-packages")
if os.path.exists(_venv_site) and _venv_site not in sys.path:
    sys.path.append(_venv_site)

PROMPTS_FILE = os.path.join(WORKSPACE_ROOT, "TEST_PROMPTS_100.md")
FASTAPI_URL = "http://127.0.0.1:8000"

def parse_prompts():
    """Phân tách 100 câu hỏi từ file Markdown."""
    if not os.path.exists(PROMPTS_FILE):
        print(f"[!] Không tìm thấy file {PROMPTS_FILE}")
        sys.exit(1)

    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    prompts = []
    current_group = "Chung"
    group_num = 0

    for line in lines:
        trimmed = line.strip()
        if trimmed.startswith("## "):
            current_group = re.sub(r"^##\s+", "", trimmed)
            g_match = re.search(r"NHÓM\s+(\d+)", current_group, re.IGNORECASE)
            group_num = int(g_match.group(1)) if g_match else (group_num + 1)
        else:
            match = re.match(r"^(\d+)\.\s+(.+)$", trimmed)
            if match:
                prompts.append({
                    "num": int(match.group(1)),
                    "group": current_group,
                    "group_num": group_num,
                    "text": match.group(2).strip()
                })
    return prompts

def check_fastapi_server():
    """Kiểm tra server FastAPI có đang chạy trên port 8000 không."""
    try:
        req = urllib.request.Request(f"{FASTAPI_URL}/api/stats", headers={"User-Agent": "AutoTester/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                return True
    except Exception:
        return False
    return False

def query_fastapi(query_str: str, top_k: int = 4):
    """Gửi câu hỏi tới server FastAPI đang chạy."""
    t0 = time.perf_counter()
    payload = json.dumps({
        "message": query_str,
        "top_k": top_k,
        "studentInfo": {"name": "Bạn đọc Kiểm thử Tự động", "department": "PTIT"}
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{FASTAPI_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return data, latency_ms

def main():
    print("=" * 80)
    print("  🚀 TRÌNH KIỂM THỬ TỰ ĐỘNG BỘ 100 CÂU HỎI SMART LIBRARY KIOSK AI (PYTHON)")
    print("=" * 80)

    prompts = parse_prompts()
    print(f"📋 Đã nạp thành công: {len(prompts)} câu hỏi từ TEST_PROMPTS_100.md\n")

    # Kiểm tra tham số dòng lệnh
    limit = 100
    group_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--limit=") or arg.startswith("-n="):
            limit = int(arg.split("=")[1])
        elif arg.startswith("--group=") or arg.startswith("-g="):
            group_filter = int(arg.split("=")[1])

    if group_filter:
        prompts = [p for p in prompts if p["group_num"] == group_filter]
        print(f"🎯 Lọc theo Nhóm {group_filter}: {len(prompts)} câu hỏi")
    if len(prompts) > limit:
        prompts = prompts[:limit]

    print(f"⚡ Đợt này sẽ thực thi: {len(prompts)} câu hỏi.")

    is_server_up = check_fastapi_server()
    if is_server_up:
        print(f"🔌 Kênh kết nối: [FastAPI Service online tại {FASTAPI_URL}]")
        mode = "online_http"
    else:
        print("⚙️ Server FastAPI chưa bật. Đang khởi tạo trực tiếp mô hình Hybrid E5 + BM25 trong bộ nhớ...")
        import pandas as pd
        import numpy as np
        from src.hybrid_search_v2 import HybridSearchEngineV2
        from src.query_understanding import QueryAnalyzer
        from src.embedding import EmbeddingEngine
        from src.response_generator import LibrarianResponseGenerator
        from src.conversation_logger import conversation_logger

        csv_path = os.path.join(BASE_DIR, "dataset", "books_enriched.csv")
        emb_path = os.path.join(BASE_DIR, "embeddings", "embeddings_enriched.npy")

        df = pd.read_csv(csv_path)
        embeddings = np.load(emb_path)
        embed_engine = EmbeddingEngine()
        query_analyzer = QueryAnalyzer(catalog_df=df)
        engine = HybridSearchEngineV2(df, embeddings, embed_engine, query_analyzer, k=60)
        generator = LibrarianResponseGenerator()
        mode = "in_memory_python"
        print("[+] Mô hình AI đã sẵn sàng phục vụ!\n")

    print("-" * 80)
    print("Bắt đầu xử lý từng câu hỏi và tự động ghi nhật ký vào CONVERSATION_HISTORY.md...")
    print("-" * 80 + "\n")

    shelf_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    latencies = []

    for i, item in enumerate(prompts, 1):
        q_text = item["text"]
        prefix = f"[{item['num']:3d}/100]"

        if mode == "online_http":
            try:
                data, lat = query_fastapi(q_text, top_k=4)
                latencies.append(lat)
                books = data.get("books", [])
                for b in books:
                    s = (b.get("shelf") or "A").upper()
                    if s in shelf_counts:
                        shelf_counts[s] += 1
                shelves = "/".join(sorted(list(set([b.get("shelf") or "A" for b in books]))))
                q_disp = q_text[:46] + ("…" if len(q_text) > 46 else "")
                print(f"{prefix} \"{q_disp}\" ➔ {len(books)} sách (Kệ {shelves}) [{lat:.1f}ms]")
            except Exception as e:
                print(f"{prefix} ❌ Lỗi gọi API: {e}")
        else:
            t0 = time.perf_counter()
            search_res = engine.search(q_text, top_k=4)
            resp = generator.format_response(search_res, max_books=4)
            lat = round((time.perf_counter() - t0) * 1000.0, 2)
            latencies.append(lat)

            books = resp.get("books", [])
            for b in books:
                s = (b.get("shelf") or "A").upper()
                if s in shelf_counts:
                    shelf_counts[s] += 1

            full_reply = resp.get("rendered_markdown") or resp.get("intro", "")
            conversation_logger.log_chat(
                user_msg=q_text,
                agent_reply=full_reply,
                books=books,
                analysis=search_res.get("analysis", {}),
                student_info={"name": f"Bạn đọc Tự động (Câu #{item['num']})", "department": "PTIT"},
                latency_ms=lat
            )

            shelves = "/".join(sorted(list(set([b.get("shelf") or "A" for b in books]))))
            q_disp = q_text[:46] + ("…" if len(q_text) > 46 else "")
            print(f"{prefix} \"{q_disp}\" ➔ {len(books)} sách (Kệ {shelves}) [{lat:.1f}ms]")

        time.sleep(0.01)

    avg_lat = round(sum(latencies) / max(len(latencies), 1), 1)

    print("\n" + "=" * 80)
    print("  🎉 HOÀN TẤT ĐỢT KIỂM THỬ TỰ ĐỘNG BẰNG PYTHON!")
    print("=" * 80)
    print(f"✅ Đã kiểm thử thành công: {len(latencies)}/{len(prompts)} câu hỏi")
    print(f"⚡ Độ trễ phản hồi trung bình: {avg_lat} ms")
    print("📊 Phân bổ gợi ý theo khu vực kệ sách:")
    print(f"   - Kệ A (Văn học - Thiếu nhi):        {shelf_counts['A']} lượt")
    print(f"   - Kệ B (Kinh tế - Kinh doanh):       {shelf_counts['B']} lượt")
    print(f"   - Kệ C (CNTT - Khoa học kỹ thuật):   {shelf_counts['C']} lượt")
    print(f"   - Kệ D (Giáo dục - Ngoại ngữ):       {shelf_counts['D']} lượt")
    print(f"   - Kệ E (Kỹ năng sống - Tâm lý học):  {shelf_counts['E']} lượt")
    print(f"   - Kệ F (Lịch sử - Văn hóa):          {shelf_counts['F']} lượt")
    print("\n📁 Toàn bộ kết quả đối thoại đã được lưu vào:")
    print(f"   👉 {os.path.join(WORKSPACE_ROOT, 'CONVERSATION_HISTORY.md')}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
