# -*- coding: utf-8 -*-
"""
test_conversation_logging.py - Kiểm thử cơ chế tự động lưu vết toàn bộ lịch sử trò chuyện.
"""
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.conversation_logger import conversation_logger

def run_test():
    print("[*] Đang thử nghiệm ghi log hội thoại tự động...")

    # Giả lập lượt 1: Bạn đọc hỏi khi tâm trạng buồn
    user_msg_1 = "nay tôi tâm trạng không tốt, tôi cần 1 cuốn truyện hài"
    agent_reply_1 = (
        "Chào bạn, mình rất hiểu cảm giác này... Khi tâm trạng trĩu nặng, một chút tiếng cười nhẹ nhàng sẽ là liều thuốc xoa dịu tốt nhất.\n"
        "Dưới đây là một số cuốn truyện dí dỏm, ấm áp từ thư viện mà bạn có thể ghé lấy đọc ngay nhé!\n\n"
        "💬 *Bạn thích đọc truyện hài hước kiểu đời thường ấm áp như Nguyễn Nhật Ánh hay truyện cười hóm hỉnh ngắn gọn?*"
    )
    books_1 = [
        {
            "book_id": "B0892",
            "title": "Cảm Ơn Người Lớn",
            "author": "Nguyễn Nhật Ánh",
            "category": "Văn học – Tiểu thuyết",
            "position": "Ô A3-26",
            "shelf": "A",
            "floor": 3,
            "match_reason": "Cuốn sách mang phong cách vui vẻ, hài hước, nhẹ nhàng, giúp bạn thư thái và xoa dịu cảm xúc."
        },
        {
            "book_id": "B1420",
            "title": "Sống Bình Thường Mà Không Tầm Thường",
            "author": "Không rõ tác giả",
            "category": "Kỹ năng sống – Phát triển bản thân",
            "position": "Ô E1-26",
            "shelf": "E",
            "floor": 1,
            "match_reason": "Cuốn sách mang phong cách vui vẻ, hài hước, giúp bạn thư thái."
        }
    ]
    analysis_1 = {
        "intent": "EMOTIONAL_CONTEXT",
        "detected_moods": ["vui vẻ", "hài hước", "nhẹ nhàng", "chữa lành"],
        "reading_effort": "nhẹ",
        "avoid_keywords": ["án mạng", "cái chết", "đám tang", "tự tử", "bạo lực", "chiến tranh", "tang thương", "u uất", "kinh dị", "kỹ thuật"]
    }
    conversation_logger.log_chat(
        user_msg=user_msg_1,
        agent_reply=agent_reply_1,
        books=books_1,
        analysis=analysis_1,
        student_info={"name": "Nguyễn Văn Tuấn", "department": "Công nghệ thông tin"},
        latency_ms=95.4
    )

    # Giả lập lượt 2: Bạn đọc hỏi tiếp câu thứ hai trong cùng phiên
    user_msg_2 = "thư viện có cuốn nào của tác giả Nguyễn Nhật Ánh nữa không bạn?"
    agent_reply_2 = (
        "Thư viện PTIT hiện có rất nhiều đầu sách của bác Nguyễn Nhật Ánh đấy bạn nhé!\n"
        "Dưới đây là những cuốn tiêu biểu nhất đang có sẵn trên kệ tầng 3:"
    )
    books_2 = [
        {
            "book_id": "B0890",
            "title": "Mắt Biếc",
            "author": "Nguyễn Nhật Ánh",
            "category": "Văn học – Tiểu thuyết",
            "position": "Ô A3-24",
            "shelf": "A",
            "floor": 3,
            "match_reason": "Tác phẩm tiêu biểu của tác giả Nguyễn Nhật Ánh thuộc danh mục Văn học – Tiểu thuyết."
        },
        {
            "book_id": "B0895",
            "title": "Tôi Thấy Hoa Vàng Trên Cỏ Xanh",
            "author": "Nguyễn Nhật Ánh",
            "category": "Văn học – Tiểu thuyết",
            "position": "Ô A3-29",
            "shelf": "A",
            "floor": 3,
            "match_reason": "Tác phẩm tiêu biểu của tác giả Nguyễn Nhật Ánh thuộc danh mục Văn học – Tiểu thuyết."
        }
    ]
    analysis_2 = {
        "intent": "AUTHOR_LOOKUP",
        "detected_author": "Nguyễn Nhật Ánh",
        "reading_effort": "nhẹ"
    }
    conversation_logger.log_chat(
        user_msg=user_msg_2,
        agent_reply=agent_reply_2,
        books=books_2,
        analysis=analysis_2,
        student_info={"name": "Nguyễn Văn Tuấn", "department": "Công nghệ thông tin"},
        latency_ms=82.1
    )

    # Giả lập lượt 3: Bạn đọc chuyển sang ô Tìm kiếm nhanh
    conversation_logger.log_search(
        query="sách học tiếng anh giao tiếp cấp tốc",
        results=[
            {
                "book_id": "B0412",
                "title": "Quick English – Nói Tiếng Anh Cấp Tốc",
                "author": "Pitsamorn Apichattapong",
                "category": "Giáo dục – Ngoại ngữ",
                "position": "Ô D2-06",
                "shelf": "D",
                "floor": 2,
                "score": 0.0578
            },
            {
                "book_id": "B0401",
                "title": "Speak Up - Giao Tiếp Tiếng Anh Tự Tin Trong Mọi Tình Huống",
                "author": "Hầu Nghị Lăng",
                "category": "Giáo dục – Ngoại ngữ",
                "position": "Ô D1-20",
                "shelf": "D",
                "floor": 1,
                "score": 0.0571
            }
        ],
        analysis={"intent": "CATEGORY_TOPIC"},
        latency_ms=78.3
    )

    print("[+] Đã chạy xong mô phỏng ghi nhận.")

if __name__ == "__main__":
    run_test()
