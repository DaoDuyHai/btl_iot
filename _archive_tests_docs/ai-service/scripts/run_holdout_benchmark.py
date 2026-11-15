import json
import time
import urllib.request
import urllib.error
import numpy as np

def run_benchmark(api_url="http://127.0.0.1:8000/api/chat"):
    with open("ai-service/tests/holdout_eval_set.json", "r", encoding="utf-8") as f:
        test_set = json.load(f)

    total_queries = len(test_set)
    latencies = []
    
    intent_correct = 0
    
    # Title queries present
    title_present_count = 0
    title_present_hits_at_4 = 0
    reciprocal_ranks = []
    
    # Title queries missing (honest rejection)
    missing_count = 0
    missing_correct_rejection = 0
    
    # Emotional context queries
    emotional_count = 0
    emotional_detected = 0
    
    # Negation constraint queries
    negation_count = 0
    negation_satisfied = 0
    
    # Location status queries
    location_count = 0
    location_direct_answered = 0
    
    # Out of domain queries
    ood_count = 0
    ood_correct = 0
    
    print("=" * 80)
    print(f"📊 BẮT ĐẦU CHẠY HOLDOUT BENCHMARK ({total_queries} CÂU HỎI ĐỘC LẬP)")
    print("=" * 80)
    
    details = []

    for item in test_set:
        qid = item["id"]
        query = item["query"]
        qtype = item["type"]
        expected_intent = item.get("expected_intent")
        
        payload = json.dumps({"message": query, "top_k": 4}).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"Error querying #{qid}: {e}")
            continue
        latency_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(latency_ms)
        
        analysis = res_data.get("analysis", {})
        actual_intent = analysis.get("intent", "UNKNOWN")
        reply = res_data.get("reply", "") or res_data.get("intro", "")
        books = res_data.get("books", [])
        detected_moods = analysis.get("detected_moods") or analysis.get("target_moods", [])
        
        # 1. Intent check
        is_intent_match = (actual_intent == expected_intent)
        if is_intent_match:
            intent_correct += 1
            
        # 2. EXACT_BOOK_PRESENT check
        if qtype in ["EXACT_BOOK_PRESENT", "ROBUSTNESS_EDGE"] and item.get("expected_status") == "FOUND":
            title_present_count += 1
            target_kw = item.get("target_title_kw", "").lower()
            hit_rank = 0
            for r, b in enumerate(books, 1):
                b_title = b.get("title", "").lower()
                if target_kw in b_title:
                    hit_rank = r
                    break
            if hit_rank > 0 and hit_rank <= 4:
                title_present_hits_at_4 += 1
                reciprocal_ranks.append(1.0 / hit_rank)
            else:
                reciprocal_ranks.append(0.0)
                
        # 3. EXACT_BOOK_MISSING check (Phải nhận diện không có / thư viện chưa có)
        if qtype == "EXACT_BOOK_MISSING":
            missing_count += 1
            reply_lower = reply.lower()
            # Kiểm tra xem câu trả lời có từ chối đúng không:
            # "chưa có", "chưa tìm thấy", "rất tiếc", "hiện không có"
            rejected_explicitly = any(w in reply_lower for w in ["chưa có", "chưa tìm thấy", "rất tiếc", "hiện không có", "chưa có đầu sách"])
            if rejected_explicitly:
                missing_correct_rejection += 1

        # 4. EMOTIONAL_CONTEXT check (Tâm trạng phải được nhận diện thực sự)
        if qtype == "EMOTIONAL_CONTEXT" or item.get("expected_emotion"):
            emotional_count += 1
            # Kiểm tra xem detected_moods có giá trị không rỗng và không phải "Không có"
            if detected_moods and len(detected_moods) > 0 and detected_moods != ["Không có"]:
                emotional_detected += 1
                
        # 5. NEGATION_CONSTRAINT check (Tránh các từ khóa bị cấm trong kết quả)
        if qtype == "NEGATION_CONSTRAINT":
            negation_count += 1
            avoid_list = item.get("negation_avoid", [])
            violated = False
            top_titles = " ".join([b.get("title", "") for b in books[:2]]).lower()
            for av in avoid_list:
                if av.lower() in top_titles:
                    violated = True
                    break
            if not violated:
                negation_satisfied += 1
                
        # 6. LOCATION_STATUS check (Trả lời trực tiếp vị trí)
        if qtype == "LOCATION_STATUS":
            location_count += 1
            target_kw = item.get("target_title_kw")
            if target_kw:
                # Kiểm tra xem có nói trực tiếp Kệ X, Tầng Y của cuốn đó không
                if "kệ" in reply.lower() and ("tầng" in reply.lower() or "vị trí" in reply.lower()):
                    location_direct_answered += 1
            else:
                if "kệ" in reply.lower() and "tầng" in reply.lower():
                    location_direct_answered += 1
                    
        # 7. OUT_OF_DOMAIN check
        if qtype == "OUT_OF_DOMAIN":
            ood_count += 1
            if actual_intent == "OUT_OF_DOMAIN" and len(books) == 0:
                ood_correct += 1
                
        details.append({
            "id": qid,
            "query": query,
            "type": qtype,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "books_count": len(books),
            "top_book": books[0].get("title") if books else "NONE",
            "reply_preview": reply[:100].replace("\n", " ")
        })

    # Summary calculations
    intent_acc = (intent_correct / total_queries) * 100.0
    recall_at_4 = (title_present_hits_at_4 / title_present_count * 100.0) if title_present_count else 0.0
    mrr = np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    rejection_rate = (missing_correct_rejection / missing_count * 100.0) if missing_count else 0.0
    negation_acc = (negation_satisfied / negation_count * 100.0) if negation_count else 0.0
    emotion_acc = (emotional_detected / emotional_count * 100.0) if emotional_count else 0.0
    loc_acc = (location_direct_answered / location_count * 100.0) if location_count else 0.0
    ood_acc = (ood_correct / ood_count * 100.0) if ood_count else 0.0
    
    p50_lat = np.percentile(latencies, 50)
    p95_lat = np.percentile(latencies, 95)
    p99_lat = np.percentile(latencies, 99)
    avg_lat = np.mean(latencies)

    print("\n" + "=" * 80)
    print("📈 KẾT QUẢ ĐO LƯỜNG HOLDOUT BENCHMARK (BASELINE)")
    print("=" * 80)
    print(f"1. Độ chính xác phân loại Intent (Intent Accuracy):       {intent_acc:6.2f}% ({intent_correct}/{total_queries})")
    print(f"2. Recall@4 tựa sách có trong kho (Book Recall@4):         {recall_at_4:6.2f}% ({title_present_hits_at_4}/{title_present_count})")
    print(f"3. Mean Reciprocal Rank (MRR tựa sách):                   {mrr:6.4f}")
    print(f"4. Tỉ lệ từ chối đúng khi sách KHÔNG có trong kho:         {rejection_rate:6.2f}% ({missing_correct_rejection}/{missing_count})")
    print(f"5. Tỉ lệ xử lý đúng ràng buộc phủ định (Negation):        {negation_acc:6.2f}% ({negation_satisfied}/{negation_count})")
    print(f"6. Tỉ lệ nhận diện cảm xúc thực tế (Emotion Detection):   {emotion_acc:6.2f}% ({emotional_detected}/{emotional_count})")
    print(f"7. Trả lời trực tiếp vị trí (LOCATION_STATUS Direct):     {loc_acc:6.2f}% ({location_direct_answered}/{location_count})")
    print(f"8. Nhận diện ngoài phạm vi (OUT_OF_DOMAIN Accuracy):      {ood_acc:6.2f}% ({ood_correct}/{ood_count})")
    print("-" * 80)
    print(f"⚡ Độ trễ trung bình (Avg Latency):                         {avg_lat:6.2f} ms")
    print(f"⚡ Độ trễ p50:                                              {p50_lat:6.2f} ms")
    print(f"⚡ Độ trễ p95:                                              {p95_lat:6.2f} ms")
    print(f"⚡ Độ trễ p99:                                              {p99_lat:6.2f} ms")
    print("=" * 80)

    # Save baseline metrics to json
    results_summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_queries": total_queries,
        "intent_accuracy": round(intent_acc, 2),
        "recall_at_4": round(recall_at_4, 2),
        "mrr": round(mrr, 4),
        "missing_book_rejection_rate": round(rejection_rate, 2),
        "negation_accuracy": round(negation_acc, 2),
        "emotion_detection_rate": round(emotion_acc, 2),
        "location_direct_rate": round(loc_acc, 2),
        "ood_accuracy": round(ood_acc, 2),
        "latency_avg_ms": round(avg_lat, 2),
        "latency_p50_ms": round(p50_lat, 2),
        "latency_p95_ms": round(p95_lat, 2),
        "details": details
    }
    with open("ai-service/tests/holdout_baseline_results.json", "w", encoding="utf-8") as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_benchmark()
