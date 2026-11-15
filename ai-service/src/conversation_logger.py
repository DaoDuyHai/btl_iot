# -*- coding: utf-8 -*-
"""
conversation_logger.py - Tự động ghi nhận toàn bộ lịch sử trò chuyện & tìm kiếm giữa Bạn đọc và AI Agent.
Mục đích:
- Lưu vết 100% nội dung hội thoại, câu hỏi, câu trả lời, sách gợi ý và phân tích nội bộ.
- Không cần người dùng phải bấm nút chấm điểm thủ công hay làm phiền trải nghiệm.
- Xuất ra file CONVERSATION_HISTORY.md dễ đọc để người dùng và AI cùng bóc tách, đánh giá và cải thiện mỗi ngày.
"""

import os
import json
import time
import threading
from datetime import datetime

class ConversationLogger:
    def __init__(self, workspace_root=None, log_dir=None, target_md_name="CONVERSATION_HISTORY.md", source_name=None):
        if log_dir is None:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.log_dir = os.path.join(self.base_dir, "logs")
        else:
            self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

        if workspace_root is None:
            # Workspace root là thư mục cha của ai-service
            self.workspace_root = os.path.dirname(self.base_dir)
        else:
            self.workspace_root = workspace_root

        self.target_md_name = target_md_name
        self.source_name = source_name or "TEST_PROMPTS_v3.md"
        self.md_path_root = os.path.join(self.workspace_root, target_md_name)
        self.md_path_local = os.path.join(self.log_dir, target_md_name)
        self.jsonl_path = os.path.join(self.log_dir, "conversations.jsonl")

        self.lock = threading.Lock()
        self._ensure_header()

    def _ensure_header(self):
        """Khởi tạo tiêu đề file Markdown nếu chưa tồn tại."""
        for md_file in [self.md_path_root, self.md_path_local]:
            os.makedirs(os.path.dirname(os.path.abspath(md_file)), exist_ok=True)
            if not os.path.exists(md_file) or os.path.getsize(md_file) == 0:
                header = (
                    "# 📖 NHẬT KÝ LỊCH SỬ HỘI THOẠI & TƯƠNG TÁC GIỮA BẠN ĐỌC VÀ THỦ THƯ AI\n"
                    f"*Khởi tạo: {datetime.now().strftime('%Y-%m-%d')} | Tự động ghi nhận thực tế từ bộ kiểm thử {self.source_name}*\n\n"
                    f"> 💡 **Mục đích:** File này lưu lại toàn bộ các lượt trò chuyện thực tế giữa Bạn đọc và Thủ thư ảo AI Kiosk PTIT qua bộ 100 câu hỏi {self.source_name}.\n"
                    "> Dữ liệu được sinh tự động 100% từ AI Engine thật (FastAPI Port 8000 / Hybrid E5 + BM25).\n\n"
                    "---\n\n"
                )
                try:
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.write(header)
                except Exception as e:
                    print(f"[!] Không thể ghi header vào {md_file}: {e}")

    def log_chat(self, user_msg: str, agent_reply: str, books: list, analysis: dict = None, student_info: dict = None, latency_ms: float = 0.0):
        """Ghi nhận một lượt hội thoại trong Chat Box."""
        with self.lock:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            student_name = (student_info or {}).get("name") or "Bạn đọc Kiosk"
            department = (student_info or {}).get("department") or ""
            reader_label = f"{student_name} ({department})" if department else student_name

            # 1. Ghi JSON Lines
            json_entry = {
                "timestamp": now_str,
                "channel": "chat_box",
                "reader": reader_label,
                "user_message": user_msg,
                "agent_reply": agent_reply,
                "books": [
                    {
                        "book_id": b.get("book_id") or b.get("bookId"),
                        "title": b.get("title"),
                        "author": b.get("author"),
                        "category": b.get("category"),
                        "subcategory": b.get("subcategory"),
                        "position": b.get("position"),
                        "match_reason": b.get("match_reason")
                    }
                    for b in (books or [])
                ],
                "analysis": analysis or {},
                "latency_ms": latency_ms
            }
            try:
                with open(self.jsonl_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"[!] Lỗi ghi JSONL: {e}")

            # 2. Tạo nội dung Markdown trực quan
            intent = (analysis or {}).get("intent", "Chưa phân loại")
            detected_emo = (analysis or {}).get("detected_emotion")
            moods = (analysis or {}).get("detected_moods", []) or (analysis or {}).get("target_moods", [])
            
            if detected_emo and detected_emo != "Không có":
                if moods:
                    mood_str = f"{detected_emo} ({', '.join(moods)})"
                else:
                    mood_str = detected_emo
            elif moods:
                mood_str = ", ".join(moods)
            else:
                mood_str = "Không có"
            avoid_kw = (analysis or {}).get("avoid_keywords", [])
            avoid_str = ", ".join(avoid_kw) if avoid_kw else "Không có"
            effort = (analysis or {}).get("reading_effort", "vừa")

            md_block = []
            md_block.append(f"## 💬 [HỘI THOẠI CHAT BOX] 🕒 `{now_str}`")
            md_block.append(f"- 👤 **Bạn đọc:** `{reader_label}` | ⚡ **Độ trễ:** `{latency_ms} ms`")
            md_block.append(f"- 🧑 **Bạn đọc nói:** **\"{user_msg}\"**\n")
            md_block.append(f"- 🤖 **Thủ thư AI trả lời:**\n")
            # Trích dẫn câu trả lời của AI
            for line in agent_reply.strip().split("\n"):
                md_block.append(f"  > {line}")
            md_block.append("")

            if books:
                md_block.append(f"- 📚 **Sách AI gợi ý ({len(books)} cuốn):**")
                for idx, b in enumerate(books, 1):
                    title = b.get("title", "Không rõ tựa")
                    author = b.get("author", "Không rõ tác giả")
                    cat = b.get("category", "")
                    shelf = b.get("shelf") or "A"
                    floor = b.get("floor", 1)
                    reason = b.get("match_reason", "")
                    reason_text = f" — *Lý do:* {reason}" if reason else ""
                    md_block.append(f"  {idx}. **{title}** — {author} | *{cat}* (Khu vực: `Kệ {shelf}` - Tầng {floor}){reason_text}")
                md_block.append("")

            md_block.append(f"- ⚙️ **Phân tích kỹ thuật ngầm của AI:**")
            md_block.append(f"  - **Ý định (Intent):** `{intent}` | **Nỗ lực đọc:** `{effort}`")
            md_block.append(f"  - **Tâm trạng nhận diện:** `{mood_str}`")
            if avoid_kw:
                md_block.append(f"  - **Từ khóa phạt né tránh:** `{avoid_str}`")
            md_block.append("\n---\n\n")

            full_block = "\n".join(md_block)
            for md_file in [self.md_path_root, self.md_path_local]:
                try:
                    os.makedirs(os.path.dirname(os.path.abspath(md_file)), exist_ok=True)
                    with open(md_file, "a", encoding="utf-8") as f:
                        f.write(full_block)
                except Exception as e:
                    print(f"[!] Lỗi ghi Markdown vào {md_file}: {e}")

    def log_search(self, query: str, results: list, analysis: dict = None, latency_ms: float = 0.0):
        """Ghi nhận một lượt tìm kiếm nhanh theo từ khóa."""
        with self.lock:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Ghi JSON Lines
            json_entry = {
                "timestamp": now_str,
                "channel": "search_by_key",
                "query": query,
                "results": [
                    {
                        "book_id": b.get("book_id"),
                        "title": b.get("title"),
                        "author": b.get("author"),
                        "category": b.get("category"),
                        "position": b.get("position"),
                        "score": b.get("score")
                    }
                    for b in (results or [])[:5]
                ],
                "analysis": analysis or {},
                "latency_ms": latency_ms
            }
            try:
                with open(self.jsonl_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"[!] Lỗi ghi JSONL: {e}")

            # 2. Ghi Markdown
            intent = (analysis or {}).get("intent", "CATEGORY_TOPIC")
            md_block = []
            md_block.append(f"## 🔍 [TÌM KIẾM NHANH THEO KEY] 🕒 `{now_str}`")
            md_block.append(f"- 🔎 **Từ khóa tìm kiếm:** **\"{query}\"** | ⚡ **Độ trễ:** `{latency_ms} ms` | Ý định: `{intent}`\n")
            if results:
                md_block.append(f"- 📚 **Kết quả trả về hàng đầu (Top {min(len(results), 5)}):**")
                for idx, b in enumerate(results[:5], 1):
                    title = b.get("title", "")
                    author = b.get("author", "")
                    cat = b.get("category", "")
                    shelf = b.get("shelf") or "A"
                    floor = b.get("floor", 1)
                    score = b.get("score")
                    score_str = f" [Điểm: {round(score, 4)}]" if score is not None else ""
                    md_block.append(f"  {idx}. **{title}** — {author} | *{cat}* (Khu vực: `Kệ {shelf}` - Tầng {floor}){score_str}")
                md_block.append("")

            md_block.append("\n---\n\n")

            full_block = "\n".join(md_block)
            for md_file in [self.md_path_root, self.md_path_local]:
                try:
                    os.makedirs(os.path.dirname(os.path.abspath(md_file)), exist_ok=True)
                    with open(md_file, "a", encoding="utf-8") as f:
                        f.write(full_block)
                except Exception as e:
                    print(f"[!] Lỗi ghi Markdown vào {md_file}: {e}")

# Khởi tạo singleton instance
conversation_logger = ConversationLogger()
