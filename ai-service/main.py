# d:\Filecode\Iot\library-kiosk\ai-service\main.py
import os
import sys
import io
import time
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Fix console encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ensure user site-packages (where Windows Application Control whitelists PyTorch) is prioritized
import site
user_site = site.getusersitepackages()
if user_site and os.path.exists(user_site):
    if user_site in sys.path:
        sys.path.remove(user_site)
    sys.path.insert(0, user_site)

# Ensure ai-service and venv site-packages are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
_venv_site = os.path.join(BASE_DIR, "venv", "Lib", "site-packages")
if os.path.exists(_venv_site) and _venv_site not in sys.path:
    sys.path.append(_venv_site)

# Mock sklearn to bypass Windows Application Control blocking DLLs on uvicorn reloader spawn
import types
if "sklearn" not in sys.modules:
    def _create_dummy(name):
        m = types.ModuleType(name)
        m.__spec__ = types.SimpleNamespace(name=name, loader=None, origin=None, submodule_search_locations=[])
        m.__path__ = []
        m.__file__ = f"<dummy_{name}>"
        return m
    sys.modules['sklearn'] = _create_dummy('sklearn')
    sys.modules['sklearn.__check_build'] = _create_dummy('sklearn.__check_build')
    sys.modules['sklearn.__check_build._check_build'] = _create_dummy('sklearn.__check_build._check_build')
    sys.modules['sklearn.metrics'] = _create_dummy('sklearn.metrics')
    sys.modules['sklearn.metrics.pairwise'] = _create_dummy('sklearn.metrics.pairwise')
    sys.modules['sklearn.metrics'].pairwise_distances = lambda *args, **kwargs: None

from src.hybrid_search_v2 import HybridSearchEngineV2
from src.query_understanding import QueryAnalyzer
from src.embedding import EmbeddingEngine
from src.response_generator import LibrarianResponseGenerator
from src.conversation_logger import conversation_logger

app = FastAPI(
    title="AI Smart Library Search Engine V2",
    description="Hệ thống AI Tìm kiếm Sách Thông minh V2 (Hybrid E5 + BM25 + Query Understanding + RRF)",
    version="2.0.0"
)

# Kích hoạt CORS hỗ trợ Kiosk UI & Backend Express
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder nếu tồn tại
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

search_engines = {}

@app.on_event("startup")
def startup_event():
    print("==================================================================")
    print("  🤖 KHỞI ĐỘNG HỆ THỐNG AI SMART LIBRARY SEARCH V2.0 (FASTAPI)")
    print("==================================================================")
    
    # 1. Tải dataset (ưu tiên books_enriched.csv đã làm giàu)
    csv_path = os.path.join(BASE_DIR, "dataset", "books_enriched.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join(BASE_DIR, "dataset", "cleaned_books_dataset.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Không tìm thấy dataset tại {csv_path}")
        
    print(f"[*] Nạp dataset chuẩn: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[+] Đã tải {len(df)} đầu sách vào bộ nhớ.")
    
    # 2. Tải embeddings (ưu tiên embeddings_enriched.npy)
    emb_path = os.path.join(BASE_DIR, "embeddings", "embeddings_enriched.npy")
    if not os.path.exists(emb_path):
        emb_path = os.path.join(BASE_DIR, "embeddings", "embeddings.npy")
    if not os.path.exists(emb_path):
        raise FileNotFoundError(f"Không tìm thấy file embeddings tại {emb_path}")
        
    print(f"[*] Nạp vector embeddings: {emb_path}")
    embeddings = np.load(emb_path)
    print(f"[+] Đã tải {len(embeddings)} vectors ({embeddings.shape[1]} chiều).")
    
    # 3. Khởi tạo QueryAnalyzer & EmbeddingEngine
    print("[*] Khởi tạo QueryAnalyzer và EmbeddingEngine (Multilingual-E5)...")
    query_analyzer = QueryAnalyzer(catalog_df=df)
    embed_engine = EmbeddingEngine()
    
    # 4. Khởi tạo HybridSearchEngineV2
    print("[*] Đang khởi tạo HybridSearchEngineV2 (BM25 + Dense E5 + RRF + Soft Reranking)...")
    engine = HybridSearchEngineV2(
        df=df,
        embeddings=embeddings,
        embedding_engine=embed_engine,
        query_analyzer=query_analyzer,
        k=60
    )
    
    search_engines['df'] = df
    search_engines['engine'] = engine
    search_engines['generator'] = LibrarianResponseGenerator()
    search_engines['mode'] = "HybridSearchV2 (BM25 + Multilingual-E5 + RRF + Query Understanding)"
    print("[✅ SẴN SÀNG] AI Search Engine V2.0 đã nạp thành công và sẵn sàng phục vụ!")
    print("==================================================================")

@app.get("/", response_class=HTMLResponse)
def get_home():
    return """
    <!DOCTYPE html>
    <html lang="vi">
        <head>
            <meta charset="utf-8">
            <title>AI Smart Library Search V2.0</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; text-align: center; padding-top: 60px; background-color: #f8fafc; color: #1e293b; }
                .card { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
                h1 { color: #dc2626; font-size: 24px; margin-bottom: 8px; }
                .badge { display: inline-block; padding: 6px 14px; background: #dcfce7; color: #15803d; border-radius: 9999px; font-weight: 600; font-size: 14px; margin: 12px 0 24px 0; }
                .links a { display: inline-block; margin: 0 10px; padding: 10px 18px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: 500; }
                .links a:hover { background: #1d4ed8; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>📚 PTIT Smart Library Kiosk</h1>
                <p>Hệ thống AI Tìm kiếm Sách Thông minh V2 (Multilingual-E5 + BM25 + Intent/Emotion Routing)</p>
                <div class="badge">● Dịch vụ AI đang chạy (Active)</div>
                <div class="links">
                    <a href="/docs" target="_blank">📖 Swagger API Docs</a>
                    <a href="/api/stats" target="_blank">📊 Thống kê Hệ thống</a>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/api/stats")
def get_stats():
    df = search_engines.get('df')
    engine = search_engines.get('engine')
    if df is None or engine is None:
        return {"status": "loading"}
    cat_counts = df['Category'].value_counts().to_dict()
    return {
        "status": "ready",
        "system": "AI Smart Library Search V2.0",
        "method": search_engines.get('mode', 'HybridSearchV2'),
        "total_records": int(len(df)),
        "unique_works": int(len(engine.work_catalog)),
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
        
    engine = search_engines.get('engine')
    if engine is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Hệ thống AI đang khởi động, vui lòng thử lại sau giây lát."}
        )
        
    t0 = time.perf_counter()
    search_res = engine.search(q_clean, top_k=top_k)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    
    results = search_res.get("results", [])
    analysis = search_res.get("analysis", {})
    msg = search_res.get("message")
    
    # Chuẩn hóa các trường trả về để khớp hoàn hảo với Express backend
    formatted_results = []
    for r in results:
        formatted_results.append({
            "book_id": r.get("book_id"),
            "work_id": r.get("work_id"),
            "title": r.get("title"),
            "author": r.get("author"),
            "category": r.get("category"),
            "subcategory": r.get("subcategory"),
            "description": r.get("description"),
            "mood_tags": r.get("mood_tags"),
            "reading_effort": r.get("reading_effort"),
            "score": r.get("score"),
            "floor": r.get("floor", 1),
            "shelf": r.get("shelf", "A"),
            "position": r.get("position", "A1-01"),
            "available": r.get("available_copies", 0),
            "available_copies": r.get("available_copies", 0),
            "total": r.get("total_copies", 0),
            "total_copies": r.get("total_copies", 0),
            "match_reason": r.get("match_reason")
        })
        
    generator = search_engines.get('generator')
    librarian_resp = generator.format_response(search_res, max_books=top_k) if generator else {}

    # Tự động ghi nhật ký tìm kiếm vào CONVERSATION_HISTORY.md
    conversation_logger.log_search(
        query=q_clean,
        results=formatted_results,
        analysis=analysis,
        latency_ms=latency_ms
    )

    return {
        "query": q_clean,
        "method": search_engines.get('mode', 'HybridSearchV2'),
        "latency_ms": latency_ms,
        "analysis": analysis,
        "message": msg,
        "librarian_response": librarian_resp,
        "total_results": len(formatted_results),
        "results": formatted_results
    }

@app.post("/api/chat")
def chat_api(payload: dict):
    msg = (payload.get("message") or "").strip()
    top_k = int(payload.get("top_k", 4))
    student_info = payload.get("studentInfo") or payload.get("student_info") or {}

    if not msg:
        return JSONResponse(
            status_code=400,
            content={"error": "Nội dung tin nhắn không được để trống."}
        )

    engine = search_engines.get('engine')
    generator = search_engines.get('generator')
    if engine is None or generator is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Hệ thống AI đang khởi động, vui lòng thử lại sau giây lát."}
        )

    t0 = time.perf_counter()
    search_res = engine.search(msg, top_k=top_k)
    resp = generator.format_response(search_res, max_books=top_k)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    resp["latency_ms"] = latency_ms

    intro = resp.get("intro", "")
    clarify = resp.get("clarifying_question", "")
    full_reply = f"{intro}\n\n💬 *{clarify}*" if clarify else intro

    # Tự động ghi nhận hội thoại vào CONVERSATION_HISTORY.md
    conversation_logger.log_chat(
        user_msg=msg,
        agent_reply=full_reply,
        books=resp.get("books", []),
        analysis=search_res.get("analysis", {}),
        student_info=student_info,
        latency_ms=latency_ms
    )

    resp["reply"] = full_reply
    resp["analysis"] = search_res.get("analysis", {})
    resp["success"] = True
    return resp

@app.get("/api/recommend")
def recommend_api(
    department: str = Query("", description="Khoa hoặc chuyên ngành của bạn đọc"),
    category: str = Query("", description="Chủ đề/thể loại quan tâm"),
    top_k: int = Query(5, ge=1, le=20)
):
    engine = search_engines.get('engine')
    if engine is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Hệ thống AI đang khởi động, vui lòng thử lại sau."}
        )

    dept_lower = (department or "").lower()
    if "công nghệ thông tin" in dept_lower or "cntt" in dept_lower or "phần mềm" in dept_lower:
        query_str = "Lập trình máy tính, cấu trúc dữ liệu và giải thuật, trí tuệ nhân tạo, công nghệ phần mềm"
    elif "viễn thông" in dept_lower or "dcvt" in dept_lower or "điện tử" in dept_lower:
        query_str = "Mạng máy tính, viễn thông, vi điều khiển IoT, điện tử viễn thông"
    elif "an toàn thông tin" in dept_lower or "attt" in dept_lower or "bảo mật" in dept_lower:
        query_str = "Bảo mật an ninh mạng, mật mã học, an toàn thông tin máy tính"
    elif "kinh tế" in dept_lower or "quản trị" in dept_lower or "marketing" in dept_lower or "qtkd" in dept_lower:
        query_str = "Quản trị kinh doanh, marketing, tài chính kế toán, tư duy kinh tế"
    elif "đa phương tiện" in dept_lower or "truyền thông" in dept_lower:
        query_str = "Thiết kế đồ họa, truyền thông đa phương tiện, nội dung sáng tạo"
    elif category:
        query_str = category
    else:
        query_str = "Sách hay kỹ năng sống, phát triển bản thân, tư duy tích cực và tác phẩm kinh điển"

    t0 = time.perf_counter()
    search_res = engine.search(query_str, top_k=top_k)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    
    results = search_res.get("results", [])
    formatted_results = []
    for r in results:
        formatted_results.append({
            "book_id": r.get("book_id"),
            "work_id": r.get("work_id"),
            "title": r.get("title"),
            "author": r.get("author"),
            "category": r.get("category"),
            "subcategory": r.get("subcategory"),
            "description": r.get("description"),
            "score": r.get("score"),
            "floor": r.get("floor", 1),
            "shelf": r.get("shelf", "A"),
            "position": r.get("position", "A1-01"),
            "available": r.get("available_copies", 0),
            "total": r.get("total_copies", 0),
            "match_reason": r.get("match_reason")
        })

    return {
        "department": department,
        "derived_query": query_str,
        "method": search_engines.get('mode', 'HybridSearchV2'),
        "latency_ms": latency_ms,
        "total_results": len(formatted_results),
        "results": formatted_results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
