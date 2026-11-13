import os
import json
import matplotlib.pyplot as plt
import numpy as np

# Ensure static folder exists
os.makedirs("static", exist_ok=True)

# Load metrics
with open("tests/metrics.json", "r", encoding="utf-8") as f:
    metrics = json.load(f)

# Delete old OOD chart if exists
if os.path.exists("static/ood_distribution_roc.png"):
    os.remove("static/ood_distribution_roc.png")

# Data preparation
methods = ["BM25 Từ khóa", "Semantic (E5)", "Hybrid Search (RRF)"]
keys = ["bm25", "semantic", "hybrid"]
hit1 = [metrics[k]["Hit@1"] * 100 for k in keys]
hit3 = [metrics[k]["Hit@3"] * 100 for k in keys]
hit5 = [metrics[k]["Hit@5"] * 100 for k in keys]
mrr = [metrics[k]["MRR"] * 100 for k in keys]

x = np.arange(len(methods))
width = 0.2

# Dark theme styling matching Kiosk UI
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
fig.patch.set_facecolor('#0f172a')
ax.set_facecolor('#1e293b')

rects1 = ax.bar(x - 1.5*width, hit1, width, label='Hit@1 (%)', color='#38bdf8')
rects2 = ax.bar(x - 0.5*width, hit3, width, label='Hit@3 (%)', color='#818cf8')
rects3 = ax.bar(x + 0.5*width, hit5, width, label='Hit@5 (%)', color='#a855f7')
rects4 = ax.bar(x + 1.5*width, mrr, width, label='MRR (x100)', color='#10b981')

ax.set_ylabel('Điểm số (%)', fontsize=12, color='#f8fafc', fontweight='bold')
ax.set_title('Hiệu Năng Tìm Kiếm Trên Tập Dữ Liệu 3.000 Sách Thật (Smart Library Kiosk)', fontsize=13, color='#f8fafc', fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(methods, fontsize=11, color='#cbd5e1', fontweight='bold')
ax.legend(facecolor='#0f172a', edgecolor='#334155', fontsize=10, loc='upper left')
ax.set_ylim(0, 115)
ax.grid(axis='y', linestyle='--', alpha=0.3, color='#94a3b8')

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4),  # 4 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8.5, color='#f1f5f9', fontweight='bold')

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)
autolabel(rects4)

plt.tight_layout()
chart_path = "static/benchmark_comparison.png"
plt.savefig(chart_path, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close()
print(f"[+] Đã tạo biểu đồ benchmark mới chuẩn xác tại {chart_path}!")
