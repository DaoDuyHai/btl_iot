import re
from typing import Dict, List, Any, Optional

class LibrarianResponseGenerator:
    """
    Module sinh câu trả lời của Thủ Thư AI Kiosk:
    - Đóng vai: Thủ thư thân thiện, tâm lý, hiểu độc giả PTIT.
    - Trung thực: Nói rõ 'thư viện chưa có' khi sách không có trong kho, sau đó mới gợi ý sách thay thế (kèm nhãn rõ ràng).
    - LOCATION_STATUS: Trả lời trực tiếp vị trí Kệ, Tầng, số bản sẵn có.
    - Tách biệt rõ ràng tác giả và tác phẩm (không nhầm tác giả thành 'tác phẩm').
    - Câu hỏi làm rõ tùy biến theo đúng cảm xúc và intent của người dùng.
    """
    def __init__(self):
        pass

    def _generate_empathy_intro(self, query: str, analysis: Dict[str, Any], search_result: Dict[str, Any] = None) -> str:
        intent = analysis.get("intent", "EXACT_BOOK")
        detected_emotion = analysis.get("detected_emotion", "Không có")
        target_moods = analysis.get("target_moods", [])
        filters = analysis.get("filters", {})
        q_lower = query.lower()

        # 1. OUT OF DOMAIN
        if intent == "OUT_OF_DOMAIN":
            return "Chào bạn! Mình là Thủ thư ảo AI của Thư viện Kiosk PTIT. Hiện tại mình chuyên hỗ trợ tra cứu sách, tìm vị trí kệ và gợi ý tác phẩm theo chuyên ngành/tâm trạng. Với câu hỏi này, bạn có thể hỏi về các đầu sách, tác giả hoặc nhờ mình gợi ý sách đọc nhé!"

        # 2. KIỂM TRA TRƯỜNG HỢP SÁCH KHÔNG CÓ TRONG KHO (HONEST REJECTION)
        book_found = (search_result or {}).get("book_found", True)
        if not book_found and intent in ["EXACT_BOOK", "LOCATION_STATUS"]:
            req_title = (search_result or {}).get("requested_title") or filters.get("target_title") or filters.get("quoted_title") or filters.get("title") or ""
            req_author = (search_result or {}).get("requested_author") or filters.get("target_author") or filters.get("author") or ""
            
            auth_str = f" của tác giả '{req_author}'" if req_author else ""
            
            if intent == "LOCATION_STATUS":
                return f"Chào bạn! Rất tiếc, cuốn sách '{req_title}'{auth_str} hiện không có trong hệ thống thư viện, do đó thủ thư không tìm thấy vị trí lưu trữ trên kệ."
            else:
                has_rel = bool((search_result or {}).get("results", []))
                if has_rel:
                    return f"Chào bạn! Rất tiếc, hiện tại trong kho sách thư viện chưa có cuốn '{req_title}'{auth_str}.\n\nTuy nhiên, thủ thư đã chọn lọc các đầu sách gần nhất cùng chuyên ngành / chủ đề có sẵn trên kệ để bạn tham khảo thay thế:"
                else:
                    return f"Chào bạn! Rất tiếc, hiện tại trong kho 3.000 đầu sách của thư viện chưa có cuốn '{req_title}'{auth_str} và cũng chưa có ấn phẩm liên quan gần."

        # 3. LOCATION_STATUS KHI CÓ SÁCH HOẶC HỎI KỆ
        if intent == "LOCATION_STATUS":
            if analysis.get("target_location"):
                loc = analysis["target_location"]
                avail_txt = f"hiện có sẵn **{loc['available']} cuốn**" if loc['available'] > 0 else "hiện tạm hết trên kệ (đã được mượn)"
                return f"Chào bạn! Cuốn sách **'{loc['title']}'** của tác giả **{loc['author']}** hiện đang được xếp tại **Khu vực Kệ {loc['shelf']} - Tầng {loc['floor']}** (Vị trí: **{loc['position']}**).\n\nThư viện {avail_txt} để bạn có thể đến mượn ngay."
            elif analysis.get("shelf_location"):
                sloc = analysis["shelf_location"]
                return f"Chào bạn! Khu vực **Kệ {sloc['shelf']}** được bố trí tại **Tầng {sloc['floor']}** của thư viện, chuyên lưu trữ các ấn phẩm thuộc lĩnh vực **{sloc['category']}**."
            elif filters.get("title"):
                return f"Chào bạn! Dưới đây là thông tin tra cứu chi tiết về vị trí kệ và tình trạng còn sách của cuốn '{filters['title']}':"
            return "Chào bạn! Dưới đây là thông tin tra cứu vị trí kệ và số bản sách sẵn có để bạn tiện đến lấy mượn:"

        # 4. EMOTIONAL CONTEXT: CÁC TÌNH HUỐNG CẢM XÚC
        if any(w in q_lower for w in ["chia tay", "người yêu", "thất tình", "tan vỡ", "đổ vỡ", "tổn thương", "đau lòng"]) or detected_emotion == "Thất tình / Tan vỡ tình cảm":
            return "Chào bạn! Chuyện tình cảm tan vỡ hay vừa chia tay luôn để lại những khoảng trống và nỗi buồn không dễ gì vượt qua. Đừng ép mình phải mạnh mẽ ngay lúc này nhé. Thủ thư xin gửi đến bạn những cuốn sách dịu dàng vỗ về, chữa lành và giúp bạn tìm lại sự bình yên trong tâm hồn:"

        if any(w in q_lower for w in ["chữa lành", "vỗ về", "an ủi", "liều thuốc tinh thần"]) or detected_emotion == "Chữa lành / Vỗ về tâm hồn":
            return "Chào bạn! Những lúc lòng chùng xuống, những trang sách ấm áp và chân thành sẽ là liều thuốc tinh thần tốt nhất. Dưới đây là những cuốn sách mang năng lượng chữa lành, giúp tâm hồn bạn được thả lỏng và tìm lại sự cân bằng:"

        if any(w in q_lower for w in ["cô đơn", "lẻ loi", "lạc lõng", "một mình"]) or detected_emotion == "Cô đơn / Lạc lõng":
            return "Chào bạn! Cảm giác cô đơn giữa dòng người đông đúc đôi khi khiến chúng ta thấy mình thật nhỏ bé và trống trải. Một cuốn sách hay có thể trở thành người bạn tri kỷ lặng lẽ bầu bạn cùng bạn. Thủ thư đã chọn lọc những tác phẩm ấm áp nhất gửi đến bạn:"

        if any(w in q_lower for w in ["muốn khóc", "khóc", "cảm động", "rơi nước mắt"]):
            return "Chào bạn! Đôi khi được khóc một trận thật đã, để những kìm nén trong lòng được giải tỏa theo trang sách lại là cách tốt nhất để trái tim nhẹ nhõm hơn. Thủ thư xin gửi đến bạn những câu chuyện sâu lắng, cảm động và chạm tới nơi sâu nhất của tâm hồn:"

        if any(w in q_lower for w in ["ấm áp", "yêu đời", "nụ cười", "hy vọng"]) or detected_emotion == "Tìm kiếm hy vọng / Lạc quan":
            return "Chào bạn! Những trang sách ngập tràn sự tử tế, tình người và niềm lạc quan sẽ thắp sáng lại hy vọng trong bạn. Dưới đây là những tác phẩm ấm áp, tiếp thêm năng lượng tích cực để bạn thấy yêu đời hơn:"

        if any(w in q_lower for w in ["stress", "áp lực", "deadline", "quá tải", "căng thẳng", "đồ án tốt nghiệp"]) or detected_emotion == "Căng thẳng / Áp lực (Stress)":
            return "Chào bạn! Áp lực học tập, thi cử và đồ án đôi khi khiến chúng ta cảm thấy kiệt sức và quá tải. Đừng quá khắt khe với bản thân nhé! Thủ thư gợi ý cho bạn những cuốn sách đọc nhẹ đầu, giải tỏa căng thẳng và lấy lại sự cân bằng:"

        if any(w in q_lower for w in ["mệt", "mỏi", "thư giãn", "chill", "nghỉ ngơi", "thảnh thơi"]) or detected_emotion == "Mệt mỏi / Cần thư giãn":
            return "Chào bạn! Sau những giờ học tập và làm việc căng thẳng, cho phép bản thân nghỉ ngơi cùng một cuốn sách nhẹ nhàng là cách nạp lại năng lượng rất tốt. Thủ thư đã chọn ra những cuốn tản văn êm dịu, dễ đọc, không cần suy nghĩ nhiều để bạn thư thái tâm trí:"

        if any(w in q_lower for w in ["mất ngủ", "khó ngủ", "đêm khuya"]) or detected_emotion == "Mất ngủ / Khó ngủ":
            return "Chào bạn! Một cuốn sách dịu êm với câu chữ chậm rãi, bình yên sẽ giúp tâm trí bạn thả lỏng và dễ dàng chìm vào giấc ngủ hơn. Dưới đây là những ấn phẩm ru êm đêm muộn cho bạn:"

        if any(w in q_lower for w in ["mất động lực", "chán nản", "bế tắc", "mất phương hướng"]) or detected_emotion == "Mất động lực / Bế tắc":
            return "Chào bạn! Ai trong chúng ta cũng có những giai đoạn chênh vênh và mất phương hướng. Dưới đây là những tác phẩm truyền cảm hứng mạnh mẽ, tiếp thêm lửa và niềm tin để bạn vững bước:"

        if any(w in q_lower for w in ["kỳ ảo", "fantasy", "phép thuật"]) or detected_emotion == "Thoát ly thực tại / Kỳ ảo":
            return "Chào bạn! Đôi khi thả mình vào những thế giới kỳ ảo và các cuộc phiêu lưu phép thuật là cách tuyệt vời nhất để tạm gác lại thực tại âu lo. Dưới đây là những tiểu thuyết kỳ ảo hấp dẫn đang có sẵn trên kệ:"

        if any(w in q_lower for w in ["hài hước", "hài", "dí dỏm", "cười"]) or detected_emotion == "Cần tiếng cười / Hài hước":
            return "Chào bạn! Một cuốn sách dí dỏm cùng những tiếng cười sảng khoái luôn là liều thuốc tinh thần tuyệt vời để giải tỏa ưu phiền. Thủ thư xin gửi đến bạn những tác phẩm hài hước, vui tươi nhất đang có sẵn trên kệ:"

        if intent == "EMOTIONAL_CONTEXT":
            return f"Chào bạn! Thấu hiểu tâm trạng của bạn lúc này ({detected_emotion}), thủ thư đã rà soát kho sách và chọn ra những ấn phẩm phù hợp nhất:"

        # 5. CATEGORY_TOPIC
        elif intent == "CATEGORY_TOPIC":
            cat = analysis.get("filters", {}).get("category", "")
            if "ngoại ngữ" in cat.lower() or any(w in q_lower for w in ["tiếng anh", "tiếng nhật", "tiếng hoa", "tiếng hàn", "ielts", "toeic", "hsk"]):
                return f"Chào bạn! Năng lực ngoại ngữ mở ra cánh cửa tri thức quốc tế và rất nhiều cơ hội nghề nghiệp. Dưới đây là các đầu sách luyện thi, ngữ pháp và đàm thoại chuẩn xác nhất trong kho sách thư viện:"
            elif "công nghệ" in cat.lower() or any(w in q_lower for w in ["lập trình", "python", "java", "cntt", "thuật toán", "microservices"]):
                return f"Chào bạn! Dành cho lĩnh vực Công nghệ Thông tin, việc trang bị nền tảng chuẩn mực và cập nhật thực tiễn là rất cần thiết. Dưới đây là các giáo trình và tài liệu tiêu biểu nhất hiện có trên kệ:"
            elif "kinh tế" in cat.lower():
                return f"Chào bạn! Dưới đây là các tác phẩm chọn lọc về tư duy kinh doanh, quản trị và tài chính uy tín đang có sẵn tại thư viện:"
            elif "lịch sử" in cat.lower() or any(w in q_lower for w in ["lịch sử", "văn hóa", "chiến tranh"]):
                return f"Chào bạn! Khám phá dòng chảy lịch sử và văn hóa là cách tuyệt vời nhất để mở rộng thế giới quan. Thủ thư gợi ý cho bạn những ấn phẩm lịch sử sâu sắc và dễ tiếp cận nhất:"
            else:
                return f"Chào bạn! Với chủ đề bạn đang quan tâm, thủ thư đã rà soát kho 3.000 đầu sách và chọn ra các ấn phẩm tiêu biểu nhất:"

        # 6. EXACT_BOOK (SỬA LỖI NHẦM TÁC GIẢ THÀNH TÁC PHẨM)
        else:
            if filters.get("title"):
                return f"Chào bạn! Dưới đây là thông tin chi tiết về tác phẩm '{filters['title']}' cùng các ấn phẩm nổi bật liên quan đang có sẵn tại thư viện:"
            elif filters.get("author"):
                return f"Chào bạn! Dưới đây là các tác phẩm tiêu biểu của tác giả '{filters['author']}' đang có sẵn tại thư viện:"
            elif filters.get("quoted_title"):
                return f"Chào bạn! Dưới đây là thông tin chi tiết về tác phẩm '{filters['quoted_title']}' đang có sẵn tại thư viện:"
            return "Chào bạn! Dựa trên nhu cầu tìm kiếm của bạn, thủ thư đã chọn lọc các ấn phẩm tiêu biểu và phù hợp nhất hiện có trên kệ sách:"

    def _generate_book_explanation(self, book: Dict[str, Any], analysis: Dict[str, Any], is_alternative: bool = False) -> str:
        title = book.get("title", "")
        author = book.get("author", "Nhiều tác giả")
        moods = book.get("mood_tags", "")
        cat = book.get("category", "")
        subcat = book.get("subcategory", "")
        intent = analysis.get("intent", "EXACT_BOOK")
        target_moods = analysis.get("target_moods", [])
        
        if is_alternative:
            return f"Ấn phẩm liên quan cùng chủ đề {subcat or cat} đang có sẵn tại thư viện để bạn tham khảo thay thế."

        mr = book.get("match_reason")
        
        if "hài hước" in target_moods or "vui vẻ" in target_moods:
            if "nguyễn nhật ánh" in author.lower():
                return f"Giọng văn hóm hỉnh, hồn nhiên của Nguyễn Nhật Ánh sẽ đưa bạn trở về những kỷ niệm tuổi thơ trong trẻo, mang lại tiếng cười nhẹ nhàng giúp bạn quên đi ưu phiền."
            elif "feynman" in title.lower():
                return f"Những mẩu chuyện đời thường cười ra nước mắt của nhà vật lý Richard Feynman mang lại tràng cười sảng khoái và một góc nhìn sống vô cùng lạc quan."
            elif "mèo mốc" in title.lower() or "truyện tranh" in subcat.lower():
                return f"Nét vẽ hài hước cùng những tình huống đời thường cực kỳ dí dỏm, đảm bảo đọc đến đâu bật cười đến đó, xua tan hoàn toàn cảm giác u ám."
            else:
                return f"Tác phẩm mang phong cách dí dỏm, nhẹ nhàng, rất thích hợp đọc để giải trí và xốc lại tinh thần tươi vui."
                
        elif "thư giãn" in target_moods or "nhẹ nhàng" in target_moods:
            if "tản văn" in subcat.lower():
                return f"Tập tản văn dung dị với câu từ êm đềm, đưa bạn vào không gian thảnh thơi, trút bỏ gánh nặng để tâm hồn được nghỉ ngơi."
            elif "chữa lành" in moods:
                return f"Cuốn sách như một cái ôm ấm áp vỗ về cảm xúc, giúp bạn lắng đọng tâm tư và tìm lại sự bình yên trong tâm trí."
            else:
                return f"Nội dung nhẹ nhàng, dung lượng vừa phải, thích hợp đọc thư giãn lúc rảnh rỗi."
                
        elif "hồi hộp" in target_moods:
            return f"Cốt truyện ly kỳ với những nút thắt mở bất ngờ, lôi cuốn bạn từ trang đầu đến trang cuối mà không thể dứt ra được."
            
        elif intent == "CATEGORY_TOPIC":
            return f"Đầu sách chuẩn mực trong mảng {subcat or cat}, hệ thống hóa kiến thức rõ ràng, dễ tiếp thu và mang tính ứng dụng cao."
            
        elif mr:
            return mr
        else:
            return f"Tác phẩm nổi bật thuộc mảng {cat}, được đông đảo bạn đọc thư viện đánh giá cao."

    def _generate_clarifying_question(self, search_results: List[Dict[str, Any]], analysis: Dict[str, Any], book_found: bool = True) -> str:
        intent = analysis.get("intent", "EXACT_BOOK")
        detected_emotion = analysis.get("detected_emotion", "Không có")
        
        if not search_results:
            if not book_found:
                return "Bạn có muốn gửi phiếu đề xuất mua thêm cuốn sách này tại quầy thủ thư, hoặc tìm kiếm một tựa sách khác không?"
            return "Bạn có thể chia sẻ thêm về tác giả, chủ đề hoặc thể loại cụ thể bạn yêu thích để mình tìm kiếm chính xác hơn nhé?"

        top_book = search_results[0]
        shelf = top_book.get("shelf", "A")
        floor = top_book.get("floor", 1)

        if not book_found:
            return f"Bạn có muốn thủ thư hướng dẫn đường đến Kệ {shelf} - Tầng {floor} để xem các cuốn sách thay thế trên không?"

        if intent == "LOCATION_STATUS":
            return f"Bạn có cần thủ thư hướng dẫn lối đi nhanh nhất tới Khu vực Kệ {shelf} - Tầng {floor} để nhận sách ngay không?"

        if intent == "EMOTIONAL_CONTEXT":
            if "Hài hước" in detected_emotion:
                return f"Bạn thích ghé Kệ {shelf} (Tầng {floor}) để mượn các cuốn truyện dí dỏm này, hay muốn thủ thư gợi ý thêm một số bộ truyện tranh khác?"
            elif "Stress" in detected_emotion:
                return f"Bạn có muốn thủ thư chỉ đường tới khu vực đọc sách yên tĩnh tại Tầng {floor} để ngồi thư giãn không?"
            elif "Thất tình" in detected_emotion or "Chữa lành" in detected_emotion:
                return f"Bạn có muốn xem thêm các tập tản văn vỗ về tâm hồn, hay cần thủ thư hướng dẫn đến Kệ {shelf} để lấy sách?"
            elif "Cô đơn" in detected_emotion:
                return f"Bạn muốn đọc thử trích đoạn ấm áp của cuốn nào trong danh sách trên, hay cần mình hướng dẫn đường tới Kệ {shelf}?"
            elif "Mất ngủ" in detected_emotion:
                return f"Bạn cần thủ thư chỉ đường đến Kệ sách tản văn ru êm giấc ngủ ở Tầng {floor} không?"
            else:
                return f"Bạn muốn đọc thử trích đoạn của cuốn nào trong danh sách trên, hay cần mình hướng dẫn lối đi đến Kệ {shelf} ở Tầng {floor}?"

        elif intent == "CATEGORY_TOPIC":
            return f"Bạn cần tài liệu ở mức độ cơ bản cho người mới bắt đầu hay tài liệu chuyên sâu nâng cao để mình lọc thêm cho bạn?"
        else:
            return f"Bạn có cần thủ thư hướng dẫn lối đi nhanh nhất tới Khu vực Kệ {shelf} - Tầng {floor} để nhận sách ngay không?"

    def format_response(self, search_result: Dict[str, Any], max_books: int = 5) -> Dict[str, Any]:
        query = search_result.get("query", "")
        analysis = search_result.get("analysis", {})
        raw_books = search_result.get("results", [])
        book_found = search_result.get("book_found", True)
        intent = analysis.get("intent", "EXACT_BOOK")
        
        # 1. OUT_OF_DOMAIN
        if intent == "OUT_OF_DOMAIN":
            intro = self._generate_empathy_intro(query, analysis, search_result)
            return {
                "query": query,
                "intent": "OUT_OF_DOMAIN",
                "intro": intro,
                "books": [],
                "clarifying_question": "Bạn đang cần tìm sách thuộc lĩnh vực nào trong các thể loại của thư viện?",
                "rendered_markdown": f"{intro}\n\n*Gợi ý: Bạn có thể thử các câu như: 'Sách học tiếng Anh giao tiếp', 'Truyện hài hước giải trí', hoặc 'Tìm sách Lập trình Python'.*"
            }

        # 2. LOCATION_STATUS ĐÃ CÓ VỊ TRÍ TRỰC TIẾP
        if intent == "LOCATION_STATUS":
            intro = self._generate_empathy_intro(query, analysis, search_result)
            clarifying_q = self._generate_clarifying_question(raw_books, analysis, book_found)
            
            if not book_found:
                return {
                    "query": query,
                    "intent": "LOCATION_STATUS",
                    "intro": intro,
                    "books": [],
                    "clarifying_question": clarifying_q,
                    "rendered_markdown": f"{intro}\n\n💬 *{clarifying_q}*"
                }
            elif raw_books:
                # Trả lời trực tiếp vị trí cuốn sách
                b = raw_books[0]
                return {
                    "query": query,
                    "intent": "LOCATION_STATUS",
                    "intro": intro,
                    "books": [{
                        "rank": 1,
                        "book_id": b.get("book_id"),
                        "work_id": b.get("work_id"),
                        "title": b.get("title"),
                        "author": b.get("author"),
                        "category": b.get("category"),
                        "location": f"Khu vực Kệ {b.get('shelf')} (Tầng {b.get('floor')})",
                        "floor": b.get("floor", 1),
                        "shelf": b.get("shelf", "A"),
                        "position": b.get("position", "A1-01"),
                        "available_copies": b.get("available_copies", 0),
                        "status_text": f"Sẵn có: {b.get('available_copies', 0)} cuốn",
                        "explanation": f"Vị trí lưu trữ: Kệ {b.get('shelf')} - Tầng {b.get('floor')}",
                        "score": 1.0
                    }],
                    "clarifying_question": clarifying_q,
                    "rendered_markdown": f"{intro}\n\n💬 *{clarifying_q}*"
                }
            else:
                return {
                    "query": query,
                    "intent": "LOCATION_STATUS",
                    "intro": intro,
                    "books": [],
                    "clarifying_question": clarifying_q,
                    "rendered_markdown": f"{intro}\n\n💬 *{clarifying_q}*"
                }

        # 3. EXACT_BOOK KHÔNG CÓ TRONG KHO (HONEST REJECTION)
        if not book_found and intent == "EXACT_BOOK":
            intro = self._generate_empathy_intro(query, analysis, search_result)
            valid_books = [b for b in raw_books if b.get("score", 0) >= 0.015][:max_books]
            clarifying_q = self._generate_clarifying_question(valid_books, analysis, book_found=False)
            
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
                available = b.get("available_copies", b.get("available", 0))
                status_str = f"Sẵn có: {available} cuốn" if available > 0 else "Hiện tạm hết trên kệ"
                explanation = self._generate_book_explanation(b, analysis, is_alternative=True)
                
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
                md_lines.append(f"**{idx}. {title}** — *Tác giả: {author}*")
                md_lines.append(f"- 🏷️ **Thể loại:** {cat_str}")
                md_lines.append(f"- 📍 **Khu vực:** Kệ {shelf} (Tầng {floor}) | **Tình trạng:** {status_str}")
                md_lines.append(f"- 💡 **Gợi ý thay thế:** {explanation}")
                md_lines.append("")
                
            md_lines.append(f"💬 *{clarifying_q}*")
            return {
                "query": query,
                "intent": intent,
                "intro": intro,
                "books": formatted_books,
                "clarifying_question": clarifying_q,
                "rendered_markdown": "\n".join(md_lines)
            }

        # 4. TRƯỜNG HỢP BÌNH THƯỜNG (CÓ SÁCH HOẶC GỢI Ý CHỦ ĐỀ/CẢM XÚC)
        valid_books = [b for b in raw_books if b.get("score", 0) >= 0.015][:max_books]
        intro = self._generate_empathy_intro(query, analysis, search_result)
        
        if not valid_books:
            return {
                "query": query,
                "intent": intent,
                "intro": f"Chào bạn! Rất tiếc hiện tại thư viện chưa tìm thấy đầu sách nào thực sự phù hợp với yêu cầu: '{query}'.",
                "books": [],
                "clarifying_question": "Bạn có thể thử tìm theo tên tác giả, môn học hoặc từ khóa thể loại rộng hơn được không?",
                "rendered_markdown": f"Chào bạn! Rất tiếc hiện tại trong kho 3.000 sách của thư viện chưa có đầu sách nào khớp với yêu cầu: *'{query}'*.\n\nBạn có thể thử tìm theo tên tác giả, chủ đề môn học, hoặc nói cho mình biết bạn muốn đọc thể loại gì nhé!"
            }

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
            
            explanation = self._generate_book_explanation(b, analysis, is_alternative=False)
            
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
            
            md_lines.append(f"**{idx}. {title}** — *Tác giả: {author}*")
            md_lines.append(f"- 🏷️ **Thể loại:** {cat_str}")
            md_lines.append(f"- 📍 **Khu vực:** Kệ {shelf} (Tầng {floor}) | **Tình trạng:** {status_str}")
            md_lines.append(f"- 💡 **Vì sao phù hợp:** {explanation}")
            md_lines.append("")

        clarifying_q = self._generate_clarifying_question(valid_books, analysis, book_found=True)
        md_lines.append(f"💬 *{clarifying_q}*")
        
        rendered_md = "\n".join(md_lines)
        
        return {
            "query": query,
            "intent": intent,
            "intro": intro,
            "books": formatted_books,
            "clarifying_question": clarifying_q,
            "rendered_markdown": rendered_md
        }
