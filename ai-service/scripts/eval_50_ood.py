import sys
import os
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

df = load_and_verify_dataset("dataset/cleaned_books_dataset.csv")
work_mapping = get_work_catalog(df)
emb_engine = EmbeddingEngine()
embeddings, book_ids = emb_engine.get_or_build_embeddings(df)
bm25 = BM25SearchEngine(df, work_mapping)
semantic = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
hybrid = HybridSearchEngine(bm25, semantic, k=60)

# Bộ 50 câu OOD thuộc 5 nhóm chủ đề hoàn toàn nằm ngoài thư viện sách
ood_50_queries = [
    # Nhóm 1: Sửa chữa xe & cơ khí giao thông (10 câu)
    "hướng dẫn sửa xe máy honda wave tại nhà",
    "cách thay nhớt xe máy exciter 150",
    "địa chỉ tiệm vá xe đạp gần nhất",
    "bảng giá phụ tùng xe ô tô toyota vios",
    "cách xử lý khi xe máy bị ngập nước chết máy",
    "quy trình đăng kiểm xe ô tô con mới nhất",
    "hướng dẫn vá lốp không săm bằng keo tự vá",
    "cách căn chỉnh xích xe máy không bị chùng",
    "tiệm sửa xe máy mở cửa đêm khu vực hà nội",
    "cách sạc ắc quy xe máy tại nhà an toàn",

    # Nhóm 2: Y tế, thuốc & khám chữa bệnh (10 câu)
    "thuốc kháng sinh trị đau họng cho người lớn",
    "bệnh viện phụ sản trung ương ở đâu",
    "lịch tiêm vắc xin cho trẻ sơ sinh 2 tháng tuổi",
    "uống thuốc hạ sốt paracetamol cách nhau mấy tiếng",
    "triệu chứng của bệnh đau ruột thừa cấp tính",
    "thuốc thú y trị cảm cúm cho mèo con",
    "xét nghiệm máu tổng quát hết bao nhiêu tiền",
    "cách sơ cứu người bị đuối nước và ngưng tim",
    "phòng khám nha khoa nhổ răng khôn không đau",
    "đơn thuốc điều trị viêm loét dạ dày tá tràng",

    # Nhóm 3: Bất động sản & Thủ tục đất đai (10 câu)
    "thủ tục sang tên sổ đỏ nhà đất cần giấy tờ gì",
    "giá thuê phòng trọ sinh viên gần đại học bách khoa",
    "mẫu hợp đồng đặt cọc mua bán căn hộ chung cư",
    "lãi suất vay mua nhà ngân hàng vietcombank",
    "quy định tách thửa đất nông nghiệp mới nhất",
    "cần tìm thợ sửa ống nước rò rỉ tại nhà",
    "kinh nghiệm chọn hướng ban công chung cư mát",
    "dịch vụ chuyển nhà trọn gói giá rẻ tphcm",
    "thủ tục công chứng di chúc tại văn phòng công chứng",
    "tra cứu quy hoạch đất đai quận cầu giấy online",

    # Nhóm 4: Du lịch, vé máy bay & dịch vụ ăn uống (10 câu)
    "giá vé máy bay khứ hồi hà nội đà nẵng vietnam airlines",
    "khách sạn 3 sao gần biển mỹ khê có hồ bơi",
    "quán bún chả ngon nổi tiếng phố cổ hà nội",
    "tour du lịch thái lan 5 ngày 4 đêm giá bao nhiêu",
    "thủ tục xin visa du lịch hàn quốc tự túc",
    "đặt bàn tiệc sinh nhật 10 người nhà hàng buffet",
    "tàu hỏa hà nội sài gòn chạy mất bao nhiêu tiếng",
    "bảng giờ xe buýt số 08 hà nội chạy chuyến cuối",
    "dịch vụ đổi tiền đô la sang tiền việt ở đâu uy tín",
    "đặt vé xem phim rạp cgv tối thứ bảy",

    # Nhóm 5: Thời tiết, nông nghiệp thực tế & việc vặt đời sống (10 câu)
    "dự báo thời tiết ngày mai hà nội có mưa không",
    "cách diệt gián đức tận gốc trong tủ bếp",
    "thuốc trừ sâu sinh học cho cây hoa hồng",
    "kỹ thuật bón phân cho cây mai vàng ra hoa đúng tết",
    "cách thông tắc bồn cầu bị nghẹt nhanh nhất",
    "hướng dẫn giặt áo phao lông vũ bằng máy giặt",
    "cách đuổi chuột ra khỏi trần thạch cao",
    "giá vàng sjc 9999 hôm nay bao nhiêu một chỉ",
    "tỷ số bóng đá ngoại hạng anh manchester united đêm qua",
    "cách cài đặt wifi tenda bằng điện thoại"
]

# Tải 100 câu In-Domain từ verified ground truth
with open("tests/verified_ground_truth_110.json", "r", encoding="utf-8") as f:
    gt_all = json.load(f)
in_domain_100 = [tc['query'] for tc in gt_all if len(tc.get('rel_ids', [])) > 0]

print(f"Tổng số câu In-Domain: {len(in_domain_100)}")
print(f"Tổng số câu OOD: {len(ood_50_queries)}")

# Thu thập phân phối điểm số Top 1
id_scores = []
id_margins = []
id_bm25_max = []

print("\n[*] Đang chạy suy luận trên 100 câu In-Domain...")
for q in in_domain_100:
    s_res = semantic.search(q, top_k=2)
    b_res = bm25.search(q, top_k=1)
    top1_cos = s_res[0]['score'] if s_res else 0.0
    top2_cos = s_res[1]['score'] if len(s_res) > 1 else top1_cos
    margin = top1_cos - top2_cos
    bm_score = b_res[0]['score'] if b_res else 0.0
    id_scores.append(top1_cos)
    id_margins.append(margin)
    id_bm25_max.append(bm_score)

ood_scores = []
ood_margins = []
ood_bm25_max = []

print("[*] Đang chạy suy luận trên 50 câu OOD...")
for q in ood_50_queries:
    s_res = semantic.search(q, top_k=2)
    b_res = bm25.search(q, top_k=1)
    top1_cos = s_res[0]['score'] if s_res else 0.0
    top2_cos = s_res[1]['score'] if len(s_res) > 1 else top1_cos
    margin = top1_cos - top2_cos
    bm_score = b_res[0]['score'] if b_res else 0.0
    ood_scores.append(top1_cos)
    ood_margins.append(margin)
    ood_bm25_max.append(bm_score)

print("\n=== THỐNG KÊ PHÂN PHỐI ĐIỂM SỐ ===")
print(f"In-Domain Cosine : Min={min(id_scores):.4f}, Mean={np.mean(id_scores):.4f}, Max={max(id_scores):.4f}")
print(f"OOD Cosine       : Min={min(ood_scores):.4f}, Mean={np.mean(ood_scores):.4f}, Max={max(ood_scores):.4f}")
print(f"In-Domain BM25   : Min={min(id_bm25_max):.2f}, Mean={np.mean(id_bm25_max):.2f}, Max={max(id_bm25_max):.2f}")
print(f"OOD BM25         : Min={min(ood_bm25_max):.2f}, Mean={np.mean(ood_bm25_max):.2f}, Max={max(ood_bm25_max):.2f}")

# Đánh giá các ngưỡng Cosine trong bài toán phát hiện OOD:
# Ground truth: OOD = Positive (1), In-Domain = Negative (0)
# Quy tắc quyết định: Nếu cosine < threshold -> Phán đoán OOD (Positive)
# Ngược lại -> Phán đoán In-Domain (Negative)
thresholds = [0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86]
metrics_table = []

for th in thresholds:
    # OOD đúng là OOD (True Positive - TP)
    tp = sum(1 for s in ood_scores if s < th)
    # OOD bị nhận nhầm là In-Domain (False Negative - FN -> tức là False Accept)
    fn = sum(1 for s in ood_scores if s >= th)
    
    # In-Domain bị nhận nhầm là OOD (False Positive - FP -> tức là False Reject)
    fp = sum(1 for s in id_scores if s < th)
    # In-Domain nhận đúng là In-Domain (True Negative - TN)
    tn = sum(1 for s in id_scores if s >= th)
    
    far = (fn / len(ood_scores)) * 100.0 # False Accept Rate (% OOD lọt lưới)
    frr = (fp / len(id_scores)) * 100.0  # False Reject Rate (% Sách thật bị chặn oan)
    
    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    
    metrics_table.append({
        "threshold": th,
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "far_percent": round(far, 2),
        "frr_percent": round(frr, 2),
        "precision_percent": round(precision, 2),
        "recall_percent": round(recall, 2),
        "f1_score": round(f1, 2)
    })
    print(f"Threshold < {th:.2f}: FAR={far:.1f}% | FRR={frr:.1f}% | Precision={precision:.1f}% | Recall={recall:.1f}% | F1={f1:.1f}")

out_data = {
    "distribution": {
        "in_domain": {"min": min(id_scores), "mean": float(np.mean(id_scores)), "max": max(id_scores)},
        "ood": {"min": min(ood_scores), "mean": float(np.mean(ood_scores)), "max": max(ood_scores)}
    },
    "threshold_evaluation": metrics_table
}

with open("tests/ood_50_evaluation.json", "w", encoding="utf-8") as f:
    json.dump(out_data, f, ensure_ascii=False, indent=2)

print("\n[+] Đã lưu toàn bộ số liệu 50 OOD vào tests/ood_50_evaluation.json")
