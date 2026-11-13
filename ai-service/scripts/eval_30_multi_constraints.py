import sys
import os
import json
import pandas as pd
import numpy as np

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

# Định nghĩa 30 truy vấn Multi-Constraint có kiểm tra tiêu chí thủ công
# Mỗi ca có hàm check_full_pass(row) và check_partial_pass(row)
mc_30_specs = [
    {
        "id": "MC01",
        "query": "Sách Python dành cho người mới bắt đầu",
        "c1": "Chủ đề Python", "c2": "Trình độ cơ bản/nhập môn",
        "full": lambda r: "python" in (str(r['Title'])+str(r['Description'])+str(r['Keywords'])).lower() and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["cơ bản", "bắt đầu", "nhập môn", "căn bản", "tự học"]),
        "partial": lambda r: "python" in (str(r['Title'])+str(r['Description'])+str(r['Keywords'])).lower()
    },
    {
        "id": "MC02",
        "query": "Sách của Nguyễn Nhật Ánh viết về tuổi học trò",
        "c1": "Tác giả Nguyễn Nhật Ánh", "c2": "Chủ đề học trò / tuổi thơ",
        "full": lambda r: "nguyễn nhật ánh" in str(r['Author']).lower() and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["tuổi thơ", "học trò", "trường", "mùa hè", "bàn có năm chỗ ngồi", "cô bé", "vé đi tuổi thơ", "ngôi trường"]),
        "partial": lambda r: "nguyễn nhật ánh" in str(r['Author']).lower()
    },
    {
        "id": "MC03",
        "query": "Sách tiếng Anh về trí tuệ nhân tạo",
        "c1": "Chủ đề AI", "c2": "Sách viết bằng tiếng Anh",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Keywords'])).lower() for w in ["ai", "trí tuệ nhân tạo"]) and any(w in str(r['Title']).lower() for w in ["foundation", "handbook", "guide", "introduction", "artificial intelligence"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Keywords'])+str(r['Description'])).lower() for w in ["ai", "trí tuệ nhân tạo", "tiếng anh"])
    },
    {
        "id": "MC04",
        "query": "Sách lập trình Java có ví dụ thực hành",
        "c1": "Ngôn ngữ Java", "c2": "Nội dung thực hành/bài tập",
        "full": lambda r: "java" in (str(r['Title'])+str(r['Keywords'])+str(r['Description'])).lower() and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["thực hành", "bài tập", "dự án", "thuật toán"]),
        "partial": lambda r: "java" in (str(r['Title'])+str(r['Keywords'])+str(r['Description'])).lower()
    },
    {
        "id": "MC05",
        "query": "Sách về tâm lý trẻ em dành cho phụ huynh",
        "c1": "Tâm lý trẻ em", "c2": "Đối tượng phụ huynh/cha mẹ",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["trẻ em", "con cái", "trẻ con"]) and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["cha mẹ", "phụ huynh", "gia đình", "nuôi dạy"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["trẻ em", "tâm lý", "cha mẹ"])
    },
    {
        "id": "MC06",
        "query": "Sách kinh doanh dành cho người chưa có kinh nghiệm",
        "c1": "Kinh doanh/khởi nghiệp", "c2": "Người mới bắt đầu/chưa kinh nghiệm",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["kinh doanh", "khởi nghiệp"]) and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["mới bắt đầu", "bắt đầu", "nhập môn", "cơ bản", "đầu tiên"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["kinh doanh", "khởi nghiệp"])
    },
    {
        "id": "MC07",
        "query": "Tiểu thuyết trinh thám của Agatha Christie",
        "c1": "Tác giả Agatha Christie", "c2": "Thể loại trinh thám án mạng",
        "full": lambda r: "agatha christie" in str(r['Author']).lower(),
        "partial": lambda r: "trinh thám" in (str(r['Category'])+str(r['Description'])+str(r['Title'])).lower()
    },
    {
        "id": "MC08",
        "query": "Giáo trình thiết kế Web HTML CSS",
        "c1": "Thiết kế Web", "c2": "Công nghệ HTML/CSS",
        "full": lambda r: any(w in str(r['Title']).lower() for w in ["web", "html", "css"]) and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["thiết kế", "lập trình"]),
        "partial": lambda r: "web" in (str(r['Title'])+str(r['Description'])).lower()
    },
    {
        "id": "MC09",
        "query": "Sách tài chính cá nhân quản lý tiền bạc",
        "c1": "Tài chính cá nhân", "c2": "Quản lý chi tiêu/tiền bạc",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["tài chính cá nhân", "quản lý tiền", "tiền bạc", "tiết kiệm", "chi tiêu"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["tài chính", "tiền", "làm giàu"])
    },
    {
        "id": "MC10",
        "query": "Lịch sử Việt Nam giai đoạn cận hiện đại",
        "c1": "Lịch sử Việt Nam", "c2": "Giai đoạn cận hiện đại / kháng chiến",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["lịch sử việt nam", "chiến tranh việt nam", "việt nam", "cận đại", "kháng chiến", "sử việt"]),
        "partial": lambda r: "lịch sử" in str(r['Category']).lower()
    },
    {
        "id": "MC11",
        "query": "Sách triết học phương Tây nhập môn",
        "c1": "Triết học", "c2": "Phương Tây / Nhập môn",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["triết học", "nhập môn triết học", "tư tưởng phương tây"]),
        "partial": lambda r: "triết" in (str(r['Title'])+str(r['Description'])).lower()
    },
    {
        "id": "MC12",
        "query": "Sách tâm lý học hành vi và đọc vị con người",
        "c1": "Tâm lý học hành vi", "c2": "Đọc vị / Nhận diện tính cách",
        "full": lambda r: any(w in str(r['Title']).lower() for w in ["tâm lý", "đọc vị", "hành vi", "thấu hiểu"]),
        "partial": lambda r: "tâm lý" in (str(r['Category'])+str(r['Title'])).lower()
    },
    {
        "id": "MC13",
        "query": "Sách thiếu nhi song ngữ Anh Việt",
        "c1": "Thiếu nhi", "c2": "Song ngữ Anh Việt",
        "full": lambda r: "thiếu nhi" in str(r['Category']).lower() and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["song ngữ", "anh - việt", "anh việt"]),
        "partial": lambda r: "thiếu nhi" in str(r['Category']).lower()
    },
    {
        "id": "MC14",
        "query": "Sách rèn luyện kỹ năng giao tiếp và thuyết phục",
        "c1": "Kỹ năng giao tiếp", "c2": "Thuyết phục / Đàm phán",
        "full": lambda r: any(w in str(r['Title']).lower() for w in ["giao tiếp", "thuyết phục", "nói chuyện", "đàm phán", "khéo ăn nói"]),
        "partial": lambda r: "kỹ năng" in str(r['Category']).lower()
    },
    {
        "id": "MC15",
        "query": "Sách quản trị nhân sự và nghệ thuật lãnh đạo",
        "c1": "Quản trị nhân sự", "c2": "Nghệ thuật lãnh đạo",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["lãnh đạo", "nhân sự", "quản trị con người", "nhân sự"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["quản trị", "kinh doanh"])
    },
    {
        "id": "MC16",
        "query": "Tiểu thuyết kiếm hiệp của Kim Dung",
        "c1": "Tác giả Kim Dung", "c2": "Kiếm hiệp",
        "full": lambda r: "kim dung" in str(r['Author']).lower(),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["kiếm hiệp", "võ hiệp"])
    },
    {
        "id": "MC17",
        "query": "Sách thiên văn học của Stephen Hawking",
        "c1": "Tác giả Stephen Hawking", "c2": "Vũ trụ / Thiên văn học",
        "full": lambda r: "stephen hawking" in str(r['Author']).lower() and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["vũ trụ", "hố đen", "thời gian", "vật lý"]),
        "partial": lambda r: "stephen hawking" in str(r['Author']).lower()
    },
    {
        "id": "MC18",
        "query": "Sách y học dinh dưỡng và ăn uống lành mạnh",
        "c1": "Dinh dưỡng sức khỏe", "c2": "Ăn uống lành mạnh",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["dinh dưỡng", "ăn uống", "sức khỏe", "thực phẩm"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["sức khỏe", "y học"])
    },
    {
        "id": "MC19",
        "query": "Sách đầu tư chứng khoán cho người mới",
        "c1": "Đầu tư chứng khoán", "c2": "Người mới bắt đầu",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["chứng khoán", "cổ phiếu"]) and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["mới bắt đầu", "bắt đầu", "nhập môn", "cơ bản"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["chứng khoán", "đầu tư"])
    },
    {
        "id": "MC20",
        "query": "Sách trí tuệ nhân tạo Deep Learning học sâu",
        "c1": "Trí tuệ nhân tạo", "c2": "Deep Learning / Mạng nơ-ron",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["deep learning", "học sâu", "mô hình nền tảng", "neural"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["ai", "trí tuệ nhân tạo"])
    },
    {
        "id": "MC21",
        "query": "Sách tự học tiếng Nhật cơ bản N5",
        "c1": "Tiếng Nhật", "c2": "Cơ bản / N5",
        "full": lambda r: any(w in str(r['Title']).lower() for w in ["tiếng nhật", "nihongo", "n5"]),
        "partial": lambda r: "tiếng nhật" in (str(r['Title'])+str(r['Description'])).lower()
    },
    {
        "id": "MC22",
        "query": "Sách tự học tiếng Trung giao tiếp cơ bản",
        "c1": "Tiếng Trung / Hán ngữ", "c2": "Giao tiếp cơ bản",
        "full": lambda r: any(w in str(r['Title']).lower() for w in ["tiếng trung", "tiếng hoa", "hán ngữ"]),
        "partial": lambda r: "tiếng trung" in (str(r['Title'])+str(r['Description'])).lower()
    },
    {
        "id": "MC23",
        "query": "Tiểu thuyết thanh xuân vườn trường tình cảm lãng mạn",
        "c1": "Thanh xuân vườn trường", "c2": "Tình cảm lãng mạn",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["thanh xuân", "học đường", "tuổi trẻ"]) and "văn học" in str(r['Category']).lower(),
        "partial": lambda r: "văn học" in str(r['Category']).lower()
    },
    {
        "id": "MC24",
        "query": "Sách rèn luyện thói quen tốt để thành công",
        "c1": "Rèn luyện thói quen", "c2": "Phát triển bản thân / Thành công",
        "full": lambda r: any(w in str(r['Title']).lower() for w in ["thói quen", "kỷ luật", "nguyên tắc thành công"]),
        "partial": lambda r: "kỹ năng sống" in str(r['Category']).lower()
    },
    {
        "id": "MC25",
        "query": "Sách phân tích dữ liệu Data Science với Python",
        "c1": "Data Science / Phân tích dữ liệu", "c2": "Python",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["dữ liệu", "data"]) and "python" in (str(r['Title'])+str(r['Description'])).lower(),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["dữ liệu", "python"])
    },
    {
        "id": "MC26",
        "query": "Sách marketing online tiếp thị số mạng xã hội",
        "c1": "Marketing / Tiếp thị số", "c2": "Mạng xã hội / Online",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["marketing", "tiếp thị", "bán hàng online", "số hóa"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["marketing", "kinh doanh"])
    },
    {
        "id": "MC27",
        "query": "Tác phẩm của tác giả Yuval Noah Harari",
        "c1": "Tác giả Yuval Noah Harari", "c2": "Sapiens / Lược sử loài người",
        "full": lambda r: "yuval noah harari" in str(r['Author']).lower(),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["lược sử loài người", "sapiens", "homo deus"])
    },
    {
        "id": "MC28",
        "query": "Tiểu thuyết của Paulo Coelho",
        "c1": "Tác giả Paulo Coelho", "c2": "Tiểu thuyết (Nhà giả kim...)",
        "full": lambda r: "paulo coelho" in str(r['Author']).lower(),
        "partial": lambda r: "nhà giả kim" in str(r['Title']).lower()
    },
    {
        "id": "MC29",
        "query": "Sách cấu trúc dữ liệu và giải thuật lập trình C++",
        "c1": "Cấu trúc dữ liệu & giải thuật", "c2": "Ngôn ngữ C++",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["c++", "thuật toán", "cấu trúc dữ liệu"]),
        "partial": lambda r: "thuật toán" in (str(r['Title'])+str(r['Description'])).lower()
    },
    {
        "id": "MC30",
        "query": "Phương pháp nuôi dạy con kiểu Nhật",
        "c1": "Nuôi dạy con", "c2": "Kiểu Nhật / Nhật Bản",
        "full": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["nuôi dạy con", "dạy con"]) and any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["nhật bản", "kiểu nhật", "người nhật"]),
        "partial": lambda r: any(w in (str(r['Title'])+str(r['Description'])).lower() for w in ["nuôi dạy con", "dạy con", "mẹ nhật"])
    }
]

print("=== EVALUATING 30 MULTI-CONSTRAINT TEST CASES ===")
mc_30_results = []
summary_counts = {"bm25": {"PASS": 0, "PARTIAL": 0, "FAIL": 0},
                  "semantic": {"PASS": 0, "PARTIAL": 0, "FAIL": 0},
                  "hybrid": {"PASS": 0, "PARTIAL": 0, "FAIL": 0}}

for spec in mc_30_specs:
    qid = spec['id']
    q = spec['query']
    
    # Ground truth candidates in df
    full_cands = [r['Book_ID'] for _, r in df.iterrows() if spec['full'](r)]
    part_cands = [r['Book_ID'] for _, r in df.iterrows() if spec['partial'](r) and r['Book_ID'] not in full_cands]
    
    b_res = bm25.search(q, top_k=5)
    s_res = semantic.search(q, top_k=5)
    h_res = hybrid.search(q, top_k=5, fetch_k=200)
    
    def grade(res_list):
        if not res_list:
            return "FAIL"
        top1_bid = res_list[0]['book_id']
        row = df[df['Book_ID'] == top1_bid].iloc[0] if len(df[df['Book_ID'] == top1_bid]) > 0 else {}
        if not row.empty and spec['full'](row):
            return "PASS"
        elif not row.empty and spec['partial'](row):
            return "PARTIAL"
        return "FAIL"
        
    b_grade = grade(b_res)
    s_grade = grade(s_res)
    h_grade = grade(h_res)
    
    summary_counts["bm25"][b_grade] += 1
    summary_counts["semantic"][s_grade] += 1
    summary_counts["hybrid"][h_grade] += 1
    
    b_top1 = f"[{b_res[0]['book_id']}] {b_res[0]['title']}" if b_res else "None"
    s_top1 = f"[{s_res[0]['book_id']}] {s_res[0]['title']}" if s_res else "None"
    h_top1 = f"[{h_res[0]['book_id']}] {h_res[0]['title']}" if h_res else "None"
    
    mc_30_results.append({
        "id": qid,
        "query": q,
        "condition_1": spec['c1'],
        "condition_2": spec['c2'],
        "total_full_cands": len(full_cands),
        "total_partial_cands": len(part_cands),
        "bm25_top1": b_top1, "bm25_grade": b_grade,
        "semantic_top1": s_top1, "semantic_grade": s_grade,
        "hybrid_top1": h_top1, "hybrid_grade": h_grade
    })
    print(f"[{qid}] '{q}': BM25={b_grade} | Semantic={s_grade} | Hybrid={h_grade} | Top1 Hyb: {h_top1[:40]}")

output = {
    "summary": summary_counts,
    "detailed_cases": mc_30_results
}

os.makedirs("tests", exist_ok=True)
with open("tests/multi_constraint_30_eval.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n=== SUMMARY COUNTS (TOP 1) ===")
print("BM25    :", summary_counts['bm25'])
print("Semantic:", summary_counts['semantic'])
print("Hybrid  :", summary_counts['hybrid'])
