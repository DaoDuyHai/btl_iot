# d:\TrainAI\main.py
import os
import sys
import io
import time
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.data_processing import load_and_verify_dataset
from src.embedding import EmbeddingEngine
from src.bm25_search import BM25SearchEngine
from src.semantic_search import SemanticSearchEngine
from src.hybrid_search import HybridSearchEngine
from src.work_mapping import get_work_catalog

# Fix console encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = FastAPI(
    title="AI Smart Library Search",
    description="Hệ thống AI Tìm kiếm Sách Thông minh V1.0 (Hybrid Search)",
    version="1.0.0"
)

# Kích hoạt CORS hỗ trợ Kiosk UI & Backend Express
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

search_engines = {}

@app.on_event("startup")
def startup_event():
    print("[*] Đang khởi động hệ thống AI Smart Library Search V1.0...")
    
    csv_path = os.path.join("dataset", "cleaned_books_dataset.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join("dataset", "books_dataset.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Không tìm thấy file dataset chuẩn tại {csv_path}")
        
    print(f"[*] Nạp dataset: {csv_path}")
    df = load_and_verify_dataset(csv_path)
    
    work_mapping = get_work_catalog(df)
    print(f"[+] Catalog tác phẩm đã tải: {len(work_mapping)} tựa sách.")
    
    emb_engine = EmbeddingEngine(cache_dir="embeddings")
    embeddings, book_ids = emb_engine.get_or_build_embeddings(df)
    
    # Cấu hình đóng băng AI Search V1.0: BM25 + Semantic E5 + RRF (k=60, fetch_k=200)
    bm25_engine = BM25SearchEngine(df, work_mapping)
    semantic_engine = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
    hybrid_engine = HybridSearchEngine(bm25_engine, semantic_engine, k=60)
    
    search_engines['df'] = df
    search_engines['work_mapping'] = work_mapping
    search_engines['hybrid'] = hybrid_engine
    print("[+] AI Search Engine V1.0 (Hybrid Search) đã sẵn sàng phục vụ người dùng!")

@app.get("/", response_class=HTMLResponse)
def get_home():
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>AI Smart Library Search - Frontend chưa sẵn sàng</h1>"

@app.get("/api/stats")
def get_stats():
    df = search_engines.get('df')
    if df is None:
        return {"status": "loading"}
    cat_counts = df['Category'].value_counts().to_dict()
    return {
        "status": "ready",
        "system": "AI Smart Library Search V1.0",
        "method": "Hybrid Search (BM25 + Multilingual E5 + RRF k=60, fetch_k=200)",
        "total_records": int(len(df)),
        "unique_works": int(len(search_engines.get('work_mapping', {}))),
        "categories": {str(k): int(v) for k, v in cat_counts.items()}
    }

@app.get("/api/search")
def search_api(
    q: str = Query(..., description="Nội dung tìm kiếm"),
    top_k: int = Query(5, ge=1, le=50, description="Số lượng sách trả về")
):
    q_clean = q.strip()
    if not q_clean:
        return JSONResponse(
            status_code=400,
            content={"error": "Nội dung tìm kiếm không được để trống."}
        )
        
    if 'hybrid' not in search_engines:
        return JSONResponse(
            status_code=503,
            content={"error": "Hệ thống đang khởi động mô hình AI, vui lòng thử lại sau giây lát."}
        )
        
    t0 = time.perf_counter()
    # Phương pháp tìm kiếm chính thức duy nhất là Hybrid Search
    results = search_engines['hybrid'].search(q_clean, top_k=top_k, fetch_k=200)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    
    return {
        "query": q_clean,
        "method": "Hybrid Search (BM25 + Semantic E5 + RRF)",
        "latency_ms": latency_ms,
        "total_results": len(results),
        "results": results
    }

@app.get("/api/recommend")
def recommend_api(
    department: str = Query("", description="Khoa hoặc chuyên ngành của bạn đọc"),
    category: str = Query("", description="Chủ đề/thể loại quan tâm"),
    top_k: int = Query(5, ge=1, le=20)
):
    if 'hybrid' not in search_engines:
        return JSONResponse(
            status_code=503,
            content={"error": "Hệ thống AI đang khởi động, vui lòng thử lại sau."}
        )

    dept_lower = (department or "").lower()
    if "công nghệ thông tin" in dept_lower or "cntt" in dept_lower or "phần mềm" in dept_lower:
        query_str = "Lập trình máy tính, khoa học máy tính, trí tuệ nhân tạo, giải thuật phần mềm"
    elif "viễn thông" in dept_lower or "dcvt" in dept_lower or "điện tử" in dept_lower:
        query_str = "Mạng máy tính, viễn thông, vi điều khiển IoT, điện tử viễn thông và hệ thống số"
    elif "an toàn thông tin" in dept_lower or "attt" in dept_lower or "bảo mật" in dept_lower:
        query_str = "Bảo mật an ninh mạng, mã hóa dữ liệu, an toàn thông tin máy tính"
    elif "kinh tế" in dept_lower or "quản trị" in dept_lower or "marketing" in dept_lower or "qtkd" in dept_lower:
        query_str = "Quản trị kinh doanh, khởi nghiệp, tài chính kế toán, tư duy kinh tế"
    elif "đa phương tiện" in dept_lower or "truyền thông" in dept_lower:
        query_str = "Thiết kế đồ họa, truyền thông đa phương tiện, nghệ thuật thị giác và nội dung sáng tạo"
    elif category:
        query_str = category
    else:
        query_str = "Sách kỹ năng sống, phát triển bản thân, tư duy thành công và tác phẩm kinh điển"

    t0 = time.perf_counter()
    results = search_engines['hybrid'].search(query_str, top_k=top_k, fetch_k=200)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        "department": department,
        "derived_query": query_str,
        "method": "Personalized Hybrid Recommendation",
        "latency_ms": latency_ms,
        "total_results": len(results),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
