# d:\Filecode\Iot\library-kiosk\ai-service\main.py
import os
import sys
import io
import time
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Fix console encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.data_processing import load_and_verify_dataset
from src.bm25_search import BM25SearchEngine
from src.work_mapping import get_work_catalog

# Safe / Resilient import of Deep Learning Semantic modules
HAS_TORCH_SEMANTIC = False
EmbeddingEngine = None
SemanticSearchEngine = None
HybridSearchEngine = None

try:
    from src.embedding import EmbeddingEngine
    from src.semantic_search import SemanticSearchEngine
    from src.hybrid_search import HybridSearchEngine
    HAS_TORCH_SEMANTIC = True
except Exception as e:
    HAS_TORCH_SEMANTIC = False
    print(f"[!] Chế độ Fallback: PyTorch/SentenceTransformers chưa thể tải do chính sách bảo mật ({e})")
    print("[*] Sẽ khởi chạy ở chế độ BM25Okapi Search Engine tối ưu hóa tiếng Việt.")

app = FastAPI(
    title="AI Smart Library Search",
    description="Hệ thống AI Tìm kiếm Sách Thông minh V1.0 (Hybrid & BM25 Search)",
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
    print("==================================================================")
    print("  🤖 KHỞI ĐỘNG HỆ THỐNG AI SMART LIBRARY SEARCH V1.0 (FASTAPI)")
    print("==================================================================")
    
    csv_path = os.path.join("dataset", "cleaned_books_dataset.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join("dataset", "books_dataset.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Không tìm thấy file dataset chuẩn tại {csv_path}")
        
    print(f"[*] Nạp dataset chuẩn: {csv_path}")
    df = load_and_verify_dataset(csv_path)
    
    work_mapping = get_work_catalog(df)
    print(f"[+] Catalog tác phẩm đã tải: {len(work_mapping)} tựa sách độc bản.")
    
    # Khởi tạo BM25 Search Engine (luôn sẵn sàng, độc lập với PyTorch, hiệu năng siêu cao)
    bm25_engine = BM25SearchEngine(df, work_mapping)
    search_engines['df'] = df
    search_engines['work_mapping'] = work_mapping
    search_engines['bm25'] = bm25_engine

    active_engine = bm25_engine
    active_mode = "BM25Okapi Search Engine (Vietnamese Normalized)"

    if HAS_TORCH_SEMANTIC:
        try:
            print("[*] Đang nạp mô hình Dense Semantic Embedding E5-Small...")
            emb_engine = EmbeddingEngine(cache_dir="embeddings")
            embeddings, book_ids = emb_engine.get_or_build_embeddings(df)
            semantic_engine = SemanticSearchEngine(df, emb_engine, embeddings, book_ids, work_mapping)
            hybrid_engine = HybridSearchEngine(bm25_engine, semantic_engine, k=60)
            
            search_engines['semantic'] = semantic_engine
            search_engines['hybrid'] = hybrid_engine
            active_engine = hybrid_engine
            active_mode = "Hybrid Search (BM25 + Semantic Multilingual-E5 + RRF)"
            print("[+] Đã nạp thành công mô hình Hybrid Search (BM25 + Dense E5)!")
        except Exception as err:
            print(f"[⚠️ CẢNH BÁO] Không thể nạp mô hình Semantic: {err}")
            print("[🚀 AUTO-FALLBACK] Kích hoạt chế độ BM25Okapi Search Engine (Zero-Downtime)!")
            active_engine = bm25_engine
            active_mode = "BM25Okapi Search Engine"
    else:
        print("[ℹ️ THÔNG BÁO] Hệ thống đang phục vụ bằng thuật toán BM25Okapi tiếng Việt.")
        print("    (Để kích hoạt thêm mô hình Dense E5, bạn có thể tắt Smart App Control trong Windows Security)")

    search_engines['active'] = active_engine
    search_engines['mode'] = active_mode
    print(f"[✅ SẴN SÀNG] AI Service đang hoạt động ở chế độ: {active_mode}")
    print("==================================================================")

@app.get("/", response_class=HTMLResponse)
def get_home():
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>AI Smart Library Search - Frontend đã sẵn sàng tại API</h1>"

@app.get("/api/stats")
def get_stats():
    df = search_engines.get('df')
    if df is None:
        return {"status": "loading"}
    cat_counts = df['Category'].value_counts().to_dict()
    return {
        "status": "ready",
        "system": "AI Smart Library Search V1.0",
        "method": search_engines.get('mode', 'BM25Okapi'),
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
        
    engine = search_engines.get('active')
    if engine is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Hệ thống AI đang khởi động, vui lòng thử lại sau giây lát."}
        )
        
    t0 = time.perf_counter()
    if hasattr(engine, 'search') and 'hybrid' in str(type(engine)).lower():
        results = engine.search(q_clean, top_k=top_k, fetch_k=200)
    else:
        results = engine.search(q_clean, top_k=top_k)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    
    return {
        "query": q_clean,
        "method": search_engines.get('mode', 'BM25Okapi'),
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
    engine = search_engines.get('active')
    if engine is None:
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
    if hasattr(engine, 'search') and 'hybrid' in str(type(engine)).lower():
        results = engine.search(query_str, top_k=top_k, fetch_k=200)
    else:
        results = engine.search(query_str, top_k=top_k)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        "department": department,
        "derived_query": query_str,
        "method": search_engines.get('mode', 'BM25Okapi'),
        "latency_ms": latency_ms,
        "total_results": len(results),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
