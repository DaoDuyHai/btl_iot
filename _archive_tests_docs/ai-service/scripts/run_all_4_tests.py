# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_ROOT = os.path.dirname(BASE_DIR)

test_runs = [
    {
        "name": "Phiên bản v1 (100 câu)",
        "file": os.path.join(WORKSPACE_ROOT, "TEST_PROMPTS_100.md"),
        "out": "CONVERSATION_HISTORY_v1.md",
        "limit": 100
    },
    {
        "name": "Phiên bản v2 (100 câu)",
        "file": os.path.join(WORKSPACE_ROOT, "TEST_PROMPTS_100_v2.md"),
        "out": "CONVERSATION_HISTORY_v2.md",
        "limit": 100
    },
    {
        "name": "Phiên bản v3 (100 câu)",
        "file": os.path.join(WORKSPACE_ROOT, "TEST_PROMPTS_v3.md"),
        "out": "CONVERSATION_HISTORY_v3.md",
        "limit": 100
    },
    {
        "name": "Phiên bản v4 (1.000 câu stress test)",
        "file": os.path.join(WORKSPACE_ROOT, "TEST_PROMPTS_v4.md"),
        "out": "CONVERSATION_HISTORY_v4.md",
        "limit": 1000
    }
]

print("=" * 80)
print("🚀 KHỞI CHẠY TỰ ĐỘNG CHẠY LẠI TOÀN BỘ 4 BỘ TEST_PROMPTS (v1, v2, v3, v4)")
print("   GHI ĐÈ TOÀN BỘ LỊCH SỬ MỚI VÀO CONVERSATION_HISTORY (v1 -> v4)")
print("=" * 80)

total_t0 = time.perf_counter()

for idx, tr in enumerate(test_runs, 1):
    print(f"\n[{idx}/4] 🏁 Đang chạy: {tr['name']} ...")
    print(f"       Nguồn: {os.path.basename(tr['file'])} ➔ Xuất: {tr['out']}")
    
    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "scripts", "auto_test_prompts.py"),
        f"--file={tr['file']}",
        f"--out={tr['out']}",
        f"--limit={tr['limit']}"
    ]
    
    t0 = time.perf_counter()
    res = subprocess.run(cmd, cwd=WORKSPACE_ROOT)
    elapsed = round(time.perf_counter() - t0, 2)
    
    if res.returncode == 0:
        print(f"       ✅ Hoàn tất {tr['name']} trong {elapsed}s!")
    else:
        print(f"       ❌ Lỗi thực thi {tr['name']} (mã lỗi {res.returncode})")

total_elapsed = round(time.perf_counter() - total_t0, 2)
print("\n" + "=" * 80)
print(f"🎉 HOÀN TẤT TOÀN BỘ 4 PHIÊN BẢN CONVERSATION HISTORY TRONG {total_elapsed}s!")
print("   1. CONVERSATION_HISTORY_v1.md (100 câu)")
print("   2. CONVERSATION_HISTORY_v2.md (100 câu)")
print("   3. CONVERSATION_HISTORY_v3.md (100 câu)")
print("   4. CONVERSATION_HISTORY_v4.md (1.000 câu)")
print("=" * 80)
