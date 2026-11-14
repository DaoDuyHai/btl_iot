import re
from typing import Dict, List, Any, Optional

class LibrarianResponseGenerator:
    """
    Module sinh câu trả lời của Thủ Thư AI Kiosk (Bước 4):
    - Đóng vai: Thủ thư thân thiện, tâm lý, hiểu độc giả PTIT.
    - LUÔN trả ngay 3-5 gợi ý tốt nhất cho câu mơ hồ / cảm xúc, không trả "tôi không hiểu".
    - Mỗi gợi ý gồm: Tên sách, Tác giả, 1-2 câu giải thích vì sao hợp tâm trạng, vị trí kệ, tình trạng bản sao.
    - Kèm đúng 1 câu hỏi làm rõ tùy chọn đặt ở CUỐI danh sách.
    - Ngưỡng lọc tự tin: Chỉ thông báo chưa có sách phù hợp khi điểm số quá thấp (< 0.02) hoặc OUT_OF_DOMAIN.
    - Tuyệt đối không bịa sách ngoài dữ liệu.
    """
    def __init__(self):
        pass

    def _generate_empathy_intro(self, query: str, analysis: Dict[str, Any]) -> str:
        intent = analysis.get("intent", "EXACT_BOOK")
        target_moods = analysis.get("target_moods", [])
        q_lower = query.lower()

        if intent == "OUT_OF_DOMAIN":
            return "Chào bạn! Mình là Thủ thư ảo AI của Thư viện Kiosk PTIT. Hiện tại mình chuyên hỗ trợ bạn tìm kiếm sách, tra cứu vị trí kệ và gợi ý tác phẩm theo tâm trạng/chuyên ngành. Với câu hỏi này, bạn có thể hỏi về các đầu sách, tác giả hoặc nhờ mình gợi ý sách đọc nhé!"

        if intent == "EMOTIONAL_CONTEXT":
            if any(w in q_lower for w in ["tâm trạng không tốt", "buồn", "không vui", "chán", "thất tình", "tụt mood", "down mood"]):
                if "hài hước" in target_moods or "vui vẻ" in target_moods or any(w in q_lower for w in ["truyện hài", "hài", "cười"]):
                    return "Chào bạn! Mình rất thấu hiểu cảm giác khi tâm trạng không được tốt hay có những chuyện khiến bạn chùng xuống. Những lúc thế này, một cuốn truyện dí dỏm, ngập tràn tiếng cười và sự hồn nhiên sẽ là liều thuốc tinh thần tuyệt vời nhất để bạn giải sầu. Thủ thư đã chọn lọc ngay cho bạn những ấn phẩm hài hước, vui tươi nhất đang có sẵn trên kệ:"
                else:
                    return "Chào bạn! Mình rất thấu hiểu những ngày bạn cảm thấy nặng lòng hay có chuyện buồn phiền. Đôi khi chỉ cần một câu chuyện ấm áp hay vài trang tản văn dung dị cũng đủ để xoa dịu và giúp bạn thấy an yên hơn. Dưới đây là những cuốn sách mang năng lượng chữa lành và vỗ về tâm hồn mà thủ thư gợi ý cho bạn:"
            elif any(w in q_lower for w in ["mệt", "mỏi", "thư giãn", "chill", "nghỉ ngơi", "thảnh thơi"]):
                return "Chào bạn! Sau những giờ học tập và làm việc căng thẳng, cho phép bản thân nghỉ ngơi cùng một cuốn sách nhẹ nhàng là cách nạp lại năng lượng rất tốt. Thủ thư đã chọn ra những cuốn tản văn êm dịu, dễ đọc, không cần suy nghĩ nhiều để bạn thư thái tâm trí:"
            elif any(w in q_lower for w in ["stress", "áp lực", "deadline", "quá tải", "căng thẳng"]):
                return "Chào bạn! Áp lực thi cử và deadline đôi khi khiến chúng ta cảm thấy kiệt sức và quá tải. Đừng quá khắt khe với bản thân nhé! Thủ thư gợi ý cho bạn những cuốn sách đọc nhẹ đầu, giải tỏa căng thẳng và lấy lại sự cân bằng:"
            elif any(w in q_lower for w in ["mất ngủ", "khó ngủ", "đêm khuya"]):
                return "Chào bạn! Một cuốn sách dịu êm với câu chữ chậm rãi, bình yên sẽ giúp tâm trí bạn thả lỏng và dễ dàng chìm vào giấc ngủ hơn. Dưới đây là những ấn phẩm ru êm đêm muộn cho bạn:"
            elif any(w in q_lower for w in ["cho con", "cho bé", "trẻ em", "mầm non"]):
                return "Chào bạn! Đọc sách cùng con trước giờ đi ngủ là khoảnh khắc gắn kết vô cùng ý nghĩa. Thủ thư gợi ý cho bạn các tập truyện tranh và đồng thoại vui tươi, giàu tính giáo dục phù hợp cho các bé:"
            elif any(w in q_lower for w in ["mất động lực", "chán nản", "bế tắc", "động lực"]):
                return "Chào bạn! Ai trong chúng ta cũng có những giai đoạn chênh vênh và mất phương hướng. Dưới đây là những tác phẩm truyền cảm hứng mạnh mẽ, tiếp thêm lửa và niềm tin để bạn vững bước:"
            elif any(w in q_lower for w in ["trinh thám", "gay cấn", "hồi hộp", "phá án"]):
                return "Chào bạn! Nếu bạn đang muốn một câu chuyện nghẹt thở, ly kỳ để tỉnh táo đầu óc và kích thích trí tò mò, thủ thư gợi ý cho bạn các tác phẩm trinh thám xuất sắc nhất sau đây:"
            else:
                return f"Chào bạn! Dựa trên tâm trạng và mong muốn đọc của bạn lúc này, thủ thư đã rà soát kho sách và chọn ra những ấn phẩm phù hợp nhất:"

        elif intent == "CATEGORY_TOPIC":
            cat = analysis.get("filters", {}).get("category", "")
            if "ngoại ngữ" in cat.lower() or any(w in q_lower for w in ["tiếng anh", "tiếng nhật", "tiếng hoa", "tiếng hàn", "ielts", "toeic"]):
                return f"Chào bạn! Năng lực ngoại ngữ mở ra cánh cửa tri thức quốc tế và rất nhiều cơ hội nghề nghiệp. Dưới đây là các đầu sách luyện thi, ngữ pháp và đàm thoại chuẩn xác nhất trong kho sách thư viện:"
            elif "công nghệ" in cat.lower() or any(w in q_lower for w in ["lập trình", "python", "java", "cntt", "thuật toán"]):
                return f"Chào bạn! Dành cho lĩnh vực Công nghệ Thông tin, việc trang bị nền tảng chuẩn mực và cập nhật thực tiễn là rất cần thiết. Dưới đây là các giáo trình và tài liệu tiêu biểu nhất hiện có trên kệ:"
            elif "kinh tế" in cat.lower():
                return f"Chào bạn! Dưới đây là các tác phẩm chọn lọc về tư duy kinh doanh, quản trị và tài chính uy tín đang có sẵn tại thư viện:"
            else:
                return f"Chào bạn! Với chủ đề bạn đang quan tâm, thủ thư đã rà soát kho 3.000 đầu sách và chọn ra các ấn phẩm tiêu biểu nhất:"

        elif intent == "LOCATION_STATUS":
            book_target = analysis.get("filters", {}).get("title", "")
            if book_target:
                return f"Chào bạn! Dưới đây là thông tin tra cứu chi tiết về vị trí kệ và tình trạng còn sách của cuốn '{book_target}':"
            return "Chào bạn! Dưới đây là thông tin tra cứu vị trí kệ và số bản sách sẵn có để bạn tiện đến lấy mượn:"

        else:
            return "Chào bạn! Thủ thư gửi bạn thông tin chính xác của ấn phẩm bạn đang tìm kiếm:"

    def _generate_book_explanation(self, book: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Sinh 1-2 câu giải thích chi tiết, gắn kết nội dung sách với trạng thái cảm xúc của người đọc."""
        title = book.get("title", "")
        author = book.get("author", "Nhiều tác giả")
        moods = book.get("mood_tags", "")
        cat = book.get("category", "")
        subcat = book.get("subcategory", "")
        desc = book.get("description", "")
        intent = analysis.get("intent", "EXACT_BOOK")
        target_moods = analysis.get("target_moods", [])
        
        # Nếu đã có match_reason đặc thù từ Search Engine
        mr = book.get("match_reason")
        
        # Tùy biến sâu theo cảm xúc cụ thể
        if "hài hước" in target_moods or "vui vẻ" in target_moods:
            if "nguyễn nhật ánh" in author.lower():
                return f"Giọng văn hóm hỉnh, hồn nhiên của Nguyễn Nhật Ánh sẽ đưa bạn trở về những kỷ niệm tuổi thơ trong trẻo, mang lại tiếng cười nhẹ nhàng giúp bạn quên đi ưu phiền."
            elif "feynman" in title.lower():
                return f"Những mẩu chuyện đời thường cười ra nước mắt của nhà vật lý đoạt giải Nobel Richard Feynman sẽ giúp bạn có những tràng cười sảng khoái và một góc nhìn sống vô cùng lạc quan."
            elif "mèo mốc" in title.lower() or "truyện tranh" in subcat.lower():
                return f"Nét vẽ hài hước cùng những tình huống đời thường cực kỳ dí dỏm, đảm bảo đọc đến đâu bật cười đến đó, xua tan hoàn toàn cảm giác u ám."
            elif "kỹ năng" in cat.lower():
                return f"Cuốn sách truyền cảm hứng với giọng kể tưng tửng, hài hước và thực tế, giúp bạn lấy lại nụ cười và tinh thần phấn chấn."
            else:
                return f"Tác phẩm mang phong cách dí dỏm, nhẹ nhàng, rất thích hợp đọc để giải trí và xốc lại tinh thần tươi vui."
                
        elif "thư giãn" in target_moods or "nhẹ nhàng" in target_moods:
            if "tản văn" in subcat.lower():
                return f"Tập tản văn dung dị với câu từ êm đềm, đưa bạn vào không gian thảnh thơi, trút bỏ gánh nặng học tập để tâm hồn được nghỉ ngơi."
            elif "chữa lành" in moods:
                return f"Cuốn sách như một cái ôm ấm áp vỗ về cảm xúc, giúp bạn lắng đọng tâm tư và tìm lại sự bình yên trong tâm trí."
            else:
                return f"Nội dung nhẹ nhàng, dung lượng vừa phải, thích hợp nhâm nhi một tách trà và đọc thư giãn lúc rảnh rỗi."
                
        elif "hồi hộp" in target_moods:
            return f"Cốt truyện ly kỳ với những nút thắt mở bất ngờ, lôi cuốn bạn từ trang đầu đến trang cuối mà không thể dứt ra được."
            
        elif intent == "CATEGORY_TOPIC":
            return f"Đầu sách chuẩn mực trong mảng {subcat or cat}, hệ thống hóa kiến thức rõ ràng, dễ tiếp thu và mang tính ứng dụng cao."
            
        elif mr:
            return mr
        else:
            return f"Tác phẩm nổi bật thuộc mảng {cat}, được đông đảo bạn đọc thư viện đánh giá cao."

    def _generate_clarifying_question(self, search_results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Sinh đúng 1 câu hỏi làm rõ tùy chọn đặt ở CUỐI danh sách để hỗ trợ người đọc tiếp."""
        intent = analysis.get("intent", "EXACT_BOOK")
        target_moods = analysis.get("target_moods", [])
        
        if not search_results:
            return "Bạn có thể chia sẻ thêm về tác giả, chủ đề hoặc thể loại cụ thể bạn yêu thích để mình tìm kiếm chính xác hơn nhé?"

        top_book = search_results[0]
        shelf = top_book.get("shelf", "A")
        floor = top_book.get("floor", 1)

        if intent == "EMOTIONAL_CONTEXT":
            if "hài hước" in target_moods:
                return f"Bạn thích ghé Kệ {shelf} (Tầng {floor}) để mượn các cuốn truyện dí dỏm này, hay muốn thủ thư gợi ý thêm một số bộ truyện tranh hài hước khác?"
            elif "thư giãn" in target_moods:
                return f"Bạn có cần thủ thư chỉ đường chi tiết đến Kệ {shelf} ở Tầng {floor}, hay bạn muốn tìm thêm tản văn của tác giả Việt Nam?"
            else:
                return f"Bạn muốn đọc thử trích đoạn của cuốn nào trong danh sách trên, hay cần mình hướng dẫn lối đi đến Kệ {shelf} ở Tầng {floor}?"
        elif intent == "CATEGORY_TOPIC":
            return f"Bạn cần tài liệu ở mức độ cơ bản cho người mới bắt đầu hay tài liệu chuyên sâu nâng cao để mình lọc thêm cho bạn?"
        else:
            return f"Bạn có cần thủ thư hướng dẫn lối đi nhanh nhất tới Khu vực Kệ {shelf} - Tầng {floor} để nhận sách ngay không?"

    def format_response(self, search_result: Dict[str, Any], max_books: int = 5) -> Dict[str, Any]:
        """
        Chuẩn hóa câu trả lời toàn diện:
        - Intro thấu cảm
        - Danh sách 3-5 sách kèm lý do, vị trí, tình trạng
        - Đúng 1 câu hỏi làm rõ sau danh sách
        - Bản rendered markdown hiển thị trên giao diện Kiosk
        """
        query = search_result.get("query", "")
        analysis = search_result.get("analysis", {})
        raw_books = search_result.get("results", [])
        
        # 1. Kiểm tra trường hợp OUT_OF_DOMAIN
        if analysis.get("intent") == "OUT_OF_DOMAIN":
            intro = self._generate_empathy_intro(query, analysis)
            return {
                "query": query,
                "intent": "OUT_OF_DOMAIN",
                "intro": intro,
                "books": [],
                "clarifying_question": "Bạn đang cần tìm sách thuộc lĩnh vực nào trong 9 thể loại của thư viện?",
                "rendered_markdown": f"{intro}\n\n*Gợi ý: Bạn có thể thử các câu như: 'Sách học tiếng Anh giao tiếp', 'Truyện hài hước giải trí', hoặc 'Tìm sách Lập trình Python'.*"
            }

        # 2. Kiểm tra trường hợp điểm quá thấp hoặc không có kết quả
        valid_books = [b for b in raw_books if b.get("score", 0) >= 0.015][:max_books]
        
        if not valid_books:
            return {
                "query": query,
                "intent": analysis.get("intent", "EXACT_BOOK"),
                "intro": f"Chào bạn! Rất tiếc hiện tại thư viện chưa tìm thấy đầu sách nào thực sự phù hợp với yêu cầu: '{query}'.",
                "books": [],
                "clarifying_question": "Bạn có thể thử tìm theo tên tác giả, môn học hoặc từ khóa thể loại rộng hơn được không?",
                "rendered_markdown": f"Chào bạn! Rất tiếc hiện tại trong kho 3.000 sách của thư viện chưa có đầu sách nào khớp với yêu cầu: *'{query}'*.\n\nBạn có thể thử tìm theo tên tác giả, chủ đề môn học, hoặc nói cho mình biết bạn muốn đọc thể loại gì nhé!"
            }

        # 3. Xây dựng nội dung phản hồi đầy đủ
        intro = self._generate_empathy_intro(query, analysis)
        
        formatted_books = []
        md_lines = [intro, ""]
        
        for idx, b in enumerate(valid_books, 1):
            title = b.get("title", "Không có tiêu đề")
            author = b.get("author") or "Nhiều tác giả"
            cat = b.get("category", "")
            subcat = b.get("subcategory", "")
            cat_str = f"{cat} - {subcat}" if subcat else cat
            floor = b.get("floor", 1)
            shelf = b.get("shelf", "A")
            position = b.get("position", "A1-01")
            available = b.get("available_copies", b.get("available", 0))
            status_str = f"Sẵn có: {available} cuốn" if available > 0 else "Hiện tạm hết trên kệ (đã có bạn mượn)"
            
            explanation = self._generate_book_explanation(b, analysis)
            
            formatted_books.append({
                "rank": idx,
                "book_id": b.get("book_id"),
                "work_id": b.get("work_id"),
                "title": title,
                "author": author,
                "category": cat_str,
                "location": f"Khu vực Kệ {shelf} (Tầng {floor})",
                "floor": floor,
                "shelf": shelf,
                "position": f"Kệ {shelf}",
                "available_copies": available,
                "status_text": status_str,
                "explanation": explanation,
                "score": b.get("score", 0.0)
            })
            
            # Markdown block cho từng sách
            md_lines.append(f"**{idx}. {title}** — *Tác giả: {author}*")
            md_lines.append(f"- 🏷️ **Thể loại:** {cat_str}")
            md_lines.append(f"- 📍 **Khu vực:** Kệ {shelf} (Tầng {floor}) | **Tình trạng:** {status_str}")
            md_lines.append(f"- 💡 **Vì sao phù hợp:** {explanation}")
            md_lines.append("")

        clarifying_q = self._generate_clarifying_question(valid_books, analysis)
        md_lines.append(f"💬 *{clarifying_q}*")
        
        rendered_md = "\n".join(md_lines)
        
        return {
            "query": query,
            "intent": analysis.get("intent", "EXACT_BOOK"),
            "intro": intro,
            "books": formatted_books,
            "clarifying_question": clarifying_q,
            "rendered_markdown": rendered_md
        }
