import json
import re
import pandas as pd
import numpy as np

df = pd.read_csv('dataset/cleaned_books_dataset.csv')

# Build query test cases with precise ground truth lists
gt_cases = []

def b_ids(title_sub):
    m = df[df['Title'].str.contains(title_sub, case=False, na=False)]
    return list(m['Book_ID'])

def a_ids(author_name):
    m = df[df['Author'].str.contains(author_name, case=False, na=False)]
    return list(m['Book_ID'])

def kw_ids(kws, cat=None):
    mask = pd.Series(False, index=df.index)
    for kw in kws:
        m = (df['Title'].str.contains(kw, case=False, na=False) |
             df['Keywords'].str.contains(kw, case=False, na=False) |
             df['Description'].str.contains(kw, case=False, na=False))
        mask = mask | m
    if cat:
        mask = mask & (df['Category'] == cat)
    return list(df[mask]['Book_ID'])

# 1. Exact Title (12 queries)
gt_cases.append({"id": "TC001", "group": "1. Tên sách chính xác", "query": "Người Đàn Ông Mang Tên Ove", "rel_ids": b_ids("Người Đàn Ông Mang Tên Ove")})
gt_cases.append({"id": "TC002", "group": "1. Tên sách chính xác", "query": "Trăm năm cô đơn", "rel_ids": b_ids("Trăm năm cô đơn")})
gt_cases.append({"id": "TC003", "group": "1. Tên sách chính xác", "query": "Nhà Giả Kim", "rel_ids": b_ids("Nhà Giả Kim")})
gt_cases.append({"id": "TC004", "group": "1. Tên sách chính xác", "query": "Cây Cam Ngọt Của Tôi", "rel_ids": b_ids("Cây Cam Ngọt Của Tôi")})
gt_cases.append({"id": "TC005", "group": "1. Tên sách chính xác", "query": "Mắt Biếc", "rel_ids": b_ids("Mắt Biếc")})
gt_cases.append({"id": "TC006", "group": "1. Tên sách chính xác", "query": "Nỗi buồn chiến tranh", "rel_ids": b_ids("Nỗi buồn chiến tranh")})
gt_cases.append({"id": "TC007", "group": "1. Tên sách chính xác", "query": "Án Mạng Trên Chuyến Tàu Tốc Hành Phương Đông", "rel_ids": b_ids("Chuyến Tàu Tốc Hành Phương Đông")})
gt_cases.append({"id": "TC008", "group": "1. Tên sách chính xác", "query": "Không Gia Đình", "rel_ids": b_ids("Không Gia Đình")})
gt_cases.append({"id": "TC009", "group": "1. Tên sách chính xác", "query": "Totto - Chan Bên Cửa Sổ", "rel_ids": b_ids("Totto - Chan Bên Cửa Sổ")})
gt_cases.append({"id": "TC010", "group": "1. Tên sách chính xác", "query": "Thiên Tài Bên Trái, Kẻ Điên Bên Phải", "rel_ids": b_ids("Thiên Tài Bên Trái")})
gt_cases.append({"id": "TC011", "group": "1. Tên sách chính xác", "query": "Điều Kỳ Diệu Của Tiệm Tạp Hóa NAMIYA", "rel_ids": b_ids("Tiệm Tạp Hóa NAMIYA")})
gt_cases.append({"id": "TC012", "group": "1. Tên sách chính xác", "query": "Dạy Con Làm Giàu - Để Không Có Tiền Vẫn Tạo Ra Tiền - Cha Giàu Cha Nghèo", "rel_ids": b_ids("Dạy Con Làm Giàu")})

# 2. Author (10 queries)
gt_cases.append({"id": "TC013", "group": "2. Tên tác giả", "query": "Nguyễn Nhật Ánh", "rel_ids": a_ids("Nguyễn Nhật Ánh")})
gt_cases.append({"id": "TC014", "group": "2. Tên tác giả", "query": "Fredrik Backman", "rel_ids": a_ids("Fredrik Backman")})
gt_cases.append({"id": "TC015", "group": "2. Tên tác giả", "query": "Agatha Christie", "rel_ids": a_ids("Agatha Christie")})
gt_cases.append({"id": "TC016", "group": "2. Tên tác giả", "query": "Paulo Coelho", "rel_ids": a_ids("Paulo Coelho")})
gt_cases.append({"id": "TC017", "group": "2. Tên tác giả", "query": "Bảo Ninh", "rel_ids": a_ids("Bảo Ninh")})
gt_cases.append({"id": "TC018", "group": "2. Tên tác giả", "query": "Hector Malot", "rel_ids": a_ids("Hector Malot")})
gt_cases.append({"id": "TC019", "group": "2. Tên tác giả", "query": "Higashino Keigo", "rel_ids": a_ids("Higashino Keigo")})
gt_cases.append({"id": "TC020", "group": "2. Tên tác giả", "query": "Daniel Kahneman", "rel_ids": a_ids("Daniel Kahneman")})
gt_cases.append({"id": "TC021", "group": "2. Tên tác giả", "query": "Nguyễn Hiến Lê", "rel_ids": a_ids("Nguyễn Hiến Lê")})
gt_cases.append({"id": "TC022", "group": "2. Tên tác giả", "query": "Stephen Hawking", "rel_ids": a_ids("Stephen Hawking")})

# 3. Topic (12 queries)
gt_cases.append({"id": "TC023", "group": "3. Chủ đề chuyên môn", "query": "sách về trí tuệ nhân tạo và học máy", "rel_ids": kw_ids(["Trí Tuệ Nhân Tạo", "Học Máy", "Machine Learning", "AI"], cat="Công nghệ thông tin")})
gt_cases.append({"id": "TC024", "group": "3. Chủ đề chuyên môn", "query": "tài chính cá nhân và đầu tư chứng khoán", "rel_ids": kw_ids(["Tài Chính Cá Nhân", "Chứng Khoán", "Đầu Tư"], cat="Kinh tế – Kinh doanh")})
gt_cases.append({"id": "TC025", "group": "3. Chủ đề chuyên môn", "query": "tâm lý học hành vi và tiềm thức con người", "rel_ids": kw_ids(["Tâm lý", "Tiềm Thức", "Hành Vi", "Tư Duy"], cat="Tâm lý học")})
gt_cases.append({"id": "TC026", "group": "3. Chủ đề chuyên môn", "query": "tiểu thuyết trinh thám án mạng phá án", "rel_ids": kw_ids(["Trinh thám", "Án mạng", "Vụ án"], cat="Văn học – Tiểu thuyết")})
gt_cases.append({"id": "TC027", "group": "3. Chủ đề chuyên môn", "query": "giáo trình học tiếng trung hsk", "rel_ids": kw_ids(["HSK", "Tiếng Trung", "Tiếng Hoa"], cat="Giáo dục – Ngoại ngữ")})
gt_cases.append({"id": "TC028", "group": "3. Chủ đề chuyên môn", "query": "khoa học thiên văn vũ trụ và vật lý lượng tử", "rel_ids": kw_ids(["Vũ Trụ", "Thiên Văn", "Vật Lý", "Lỗ Đen"], cat="Khoa học – Công nghệ")})
gt_cases.append({"id": "TC029", "group": "3. Chủ đề chuyên môn", "query": "truyện tranh thiếu nhi cho bé mẫu giáo", "rel_ids": kw_ids(["Thiếu nhi", "Tranh", "Bé", "Mẫu giáo"], cat="Thiếu nhi")})
gt_cases.append({"id": "TC030", "group": "3. Chủ đề chuyên môn", "query": "lịch sử văn hóa việt nam qua các triều đại", "rel_ids": kw_ids(["Lịch Sử", "Việt Nam", "Triều đại", "Văn Hóa"], cat="Lịch sử – Văn hóa")})
gt_cases.append({"id": "TC031", "group": "3. Chủ đề chuyên môn", "query": "kỹ năng giao tiếp và thuyết phục người khác", "rel_ids": kw_ids(["Giao Tiếp", "Thuyết Phục", "Ứng Xử"], cat="Kỹ năng sống – Phát triển bản thân")})
gt_cases.append({"id": "TC032", "group": "3. Chủ đề chuyên môn", "query": "quản trị kinh doanh và nghệ thuật lãnh đạo", "rel_ids": kw_ids(["Quản Trị", "Lãnh Đạo", "Quản Lý"], cat="Kinh tế – Kinh doanh")})
gt_cases.append({"id": "TC033", "group": "3. Chủ đề chuyên môn", "query": "tiểu thuyết văn học kinh điển thế giới", "rel_ids": kw_ids(["Kinh điển"], cat="Văn học – Tiểu thuyết")})
gt_cases.append({"id": "TC034", "group": "3. Chủ đề chuyên môn", "query": "lập trình phát triển ứng dụng web internet", "rel_ids": kw_ids(["Web", "HTML", "CSS", "Javascript", "Internet"], cat="Công nghệ thông tin")})

# 4. Learning Purpose (12 queries)
gt_cases.append({"id": "TC035", "group": "4. Mục đích học tập", "query": "Tôi muốn học lập trình Python từ con số 0", "rel_ids": kw_ids(["Python"], cat="Công nghệ thông tin")})
gt_cases.append({"id": "TC036", "group": "4. Mục đích học tập", "query": "Tôi muốn học cách xây dựng và thiết kế website", "rel_ids": kw_ids(["Web", "Website", "Thiết Kế Web"], cat="Công nghệ thông tin")})
gt_cases.append({"id": "TC037", "group": "4. Mục đích học tập", "query": "Tôi muốn tìm tài liệu giúp cải thiện kỹ năng giao tiếp", "rel_ids": kw_ids(["Giao Tiếp", "Nói", "Ứng Xử"], cat="Kỹ năng sống – Phát triển bản thân")})
gt_cases.append({"id": "TC038", "group": "4. Mục đích học tập", "query": "Tôi muốn tìm sách giúp trẻ lớp 3 cải thiện tư duy logic", "rel_ids": kw_ids(["Tư Duy", "Logic", "Toán"])})
gt_cases.append({"id": "TC039", "group": "4. Mục đích học tập", "query": "Tôi muốn tìm cuốn sách dạy học toán tiểu học", "rel_ids": kw_ids(["Toán"])})
gt_cases.append({"id": "TC040", "group": "4. Mục đích học tập", "query": "học cách kể chuyện và trực quan hóa dữ liệu biểu đồ", "rel_ids": b_ids("Storytelling With Data")})
gt_cases.append({"id": "TC041", "group": "4. Mục đích học tập", "query": "tìm sách hướng dẫn quản lý thời gian và tăng năng suất", "rel_ids": kw_ids(["Thời Gian", "Năng Suất"])})
gt_cases.append({"id": "TC042", "group": "4. Mục đích học tập", "query": "học tiếng anh giao tiếp căn bản cho người mới bắt đầu", "rel_ids": kw_ids(["Tiếng Anh", "English", "Giao Tiếp Tiếng Anh"], cat="Giáo dục – Ngoại ngữ")})
gt_cases.append({"id": "TC043", "group": "4. Mục đích học tập", "query": "cách khởi nghiệp kinh doanh nhỏ và quản lý vốn", "rel_ids": kw_ids(["Khởi Nghiệp", "Kinh Doanh"], cat="Kinh tế – Kinh doanh")})
gt_cases.append({"id": "TC044", "group": "4. Mục đích học tập", "query": "phương pháp rèn luyện tư duy phản biện cho sinh viên", "rel_ids": kw_ids(["Tư Duy", "Phản Biện", "Logic"])})
gt_cases.append({"id": "TC045", "group": "4. Mục đích học tập", "query": "hướng dẫn tự học tin học văn phòng excel word", "rel_ids": kw_ids(["Tin Học", "Văn Phòng", "Excel", "Word"], cat="Công nghệ thông tin")})
gt_cases.append({"id": "TC046", "group": "4. Mục đích học tập", "query": "cách vượt qua trầm cảm lo âu và chữa lành nội tâm", "rel_ids": kw_ids(["Trầm Cảm", "Lo Âu", "Chữa Lành", "Nội Tâm"])})

# 5. Narrative / Semantic Description (16 queries) - Mapped to specific iconic books
gt_cases.append({"id": "TC047", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "sách kể về nỗi đau chiến tranh qua ký ức người lính cựu binh", "rel_ids": b_ids("Nỗi buồn chiến tranh")})
gt_cases.append({"id": "TC048", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "chàng trai chăn cừu vượt sa mạc đi tìm kho báu dưới chân kim tự tháp ai cập", "rel_ids": b_ids("Nhà Giả Kim")})
gt_cases.append({"id": "TC049", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "vụ án giết người trên toa xe lửa tốc hành bị tuyết chặn lại", "rel_ids": b_ids("Chuyến Tàu Tốc Hành Phương Đông")})
gt_cases.append({"id": "TC050", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "cậu bé mồ côi đi lang thang khắp nước pháp biểu diễn xiếc rong cùng ông già tốt bụng", "rel_ids": b_ids("Không Gia Đình")})
gt_cases.append({"id": "TC051", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "ngôi trường độc đáo có lớp học nằm trong toa xe điện cũ kỹ", "rel_ids": b_ids("Totto - Chan Bên Cửa Sổ")})
gt_cases.append({"id": "TC052", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "cuộc đối thoại có thật với các bệnh nhân tâm thần khám phá góc nhìn thế giới khác lạ", "rel_ids": b_ids("Thiên Tài Bên Trái, Kẻ Điên Bên Phải")})
gt_cases.append({"id": "TC053", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "ông già khó tính cộc cằn nhưng có trái tim ấm áp luôn muốn tự tử", "rel_ids": b_ids("Người Đàn Ông Mang Tên Ove")})
gt_cases.append({"id": "TC054", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "tình yêu tuổi thơ trong sáng của ngạn dành cho hà lan ở làng đo đo", "rel_ids": b_ids("Mắt Biếc")})
gt_cases.append({"id": "TC055", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "cậu bé nghèo coi cây ăn quả trong vườn là người bạn thân tâm sự nỗi buồn", "rel_ids": b_ids("Cây Cam Ngọt Của Tôi")})
gt_cases.append({"id": "TC056", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "tiệm tạp hóa bí ẩn nhận những lá thư nhờ tư vấn gửi về từ quá khứ", "rel_ids": b_ids("Tiệm Tạp Hóa NAMIYA")})
gt_cases.append({"id": "TC057", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "thị trấn nhỏ bị tuyết bao phủ và giấc mơ khúc côn cầu trên băng", "rel_ids": b_ids("Beartown")})
gt_cases.append({"id": "TC058", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "bảy dòng dõi gia tộc sống cô độc qua một thế kỷ tại ngôi làng hoang sơ", "rel_ids": b_ids("Trăm năm cô đơn")})
gt_cases.append({"id": "TC059", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "cách người giàu bắt tiền bạc làm việc cật lực phục vụ cho mình", "rel_ids": b_ids("Dạy Con Làm Giàu")})
gt_cases.append({"id": "TC060", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "lược sử quá trình tiến hóa và phát triển văn minh của loài người qua các thời kỳ", "rel_ids": b_ids("Sapiens")})
gt_cases.append({"id": "TC061", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "sách dạy cách nuôi dạy con ngoan và gắn kết tình cảm gia đình", "rel_ids": kw_ids(["Nuôi Dạy Con", "Gia Đình", "Cha Mẹ"])})
gt_cases.append({"id": "TC062", "group": "5. Ngôn ngữ tự nhiên (Ngữ nghĩa)", "query": "phương pháp rèn luyện tập thể dục thể thao tăng cường sức khỏe cơ bắp", "rel_ids": b_ids("Khoa học về tập kháng lực")})

# 6. Short queries (10 queries)
gt_cases.append({"id": "TC063", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Ove", "rel_ids": b_ids("Ove")})
gt_cases.append({"id": "TC064", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Mắt Biếc", "rel_ids": b_ids("Mắt Biếc")})
gt_cases.append({"id": "TC065", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Python", "rel_ids": kw_ids(["Python"])})
gt_cases.append({"id": "TC066", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Nhà giả kim", "rel_ids": b_ids("Nhà Giả Kim")})
gt_cases.append({"id": "TC067", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Sapiens", "rel_ids": b_ids("Sapiens")})
gt_cases.append({"id": "TC068", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Agatha Christie", "rel_ids": a_ids("Agatha Christie")})
gt_cases.append({"id": "TC069", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "HSK 1", "rel_ids": b_ids("HSK 1")})
gt_cases.append({"id": "TC070", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Cây cam ngọt", "rel_ids": b_ids("Cây Cam Ngọt Của Tôi")})
gt_cases.append({"id": "TC071", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Trí tuệ nhân tạo", "rel_ids": kw_ids(["Trí Tuệ Nhân Tạo"])})
gt_cases.append({"id": "TC072", "group": "6. Câu hỏi ngắn (1-3 từ)", "query": "Nỗi buồn chiến tranh", "rel_ids": b_ids("Nỗi buồn chiến tranh")})

# 7. Long queries (10 queries)
gt_cases.append({"id": "TC073", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Em đang là sinh viên năm nhất muốn tìm một cuốn sách văn học kinh điển cảm động nói về tình bạn thời thơ ấu nông thôn Việt Nam", "rel_ids": a_ids("Nguyễn Nhật Ánh")})
gt_cases.append({"id": "TC074", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Tôi muốn tìm một cuốn tiểu thuyết trinh thám hồi hộp có thám tử tài ba phá án trên một phương tiện giao thông bị cô lập hoàn toàn giữa trời tuyết", "rel_ids": b_ids("Chuyến Tàu Tốc Hành Phương Đông")})
gt_cases.append({"id": "TC075", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Thư viện có sách nào hướng dẫn cách thức máy tính và thuật toán tự động học hỏi từ dữ liệu để đưa ra dự đoán trong tương lai không", "rel_ids": kw_ids(["Trí Tuệ Nhân Tạo", "Học Máy"])})
gt_cases.append({"id": "TC076", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Cho tôi hỏi có tài liệu nào phân tích chi tiết về tâm lý con người khi đưa ra các quyết định chi tiêu tiền bạc và đầu tư tài chính cá nhân", "rel_ids": b_ids("Tâm Lý Học Về Tiền")})
gt_cases.append({"id": "TC077", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Cuốn sách nào kể về cuộc đời phiêu bạt nhiều thăng trầm của một cậu bé mồ côi người Pháp theo đoàn xiếc rong của một cụ già", "rel_ids": b_ids("Không Gia Đình")})
gt_cases.append({"id": "TC078", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Tôi muốn đọc một tác phẩm tâm lý học sâu sắc về giấc mơ và tiềm thức của tác giả Carl Jung hoặc các trường phái phân tâm học", "rel_ids": b_ids("Hồi ức, giấc mơ, suy ngẫm")})
gt_cases.append({"id": "TC079", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Tìm giúp tôi cuốn sách dạy các em nhỏ mầm non học cách quản lý cảm xúc khi tức giận hay buồn bã", "rel_ids": kw_ids(["Cảm Xúc", "Buồn", "Tức Giận"])})
gt_cases.append({"id": "TC080", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Có cuốn sách nào giúp một người bình thường không có nhiều vốn học được tư duy làm giàu và độc lập tài chính như tác giả Kiyosaki", "rel_ids": b_ids("Dạy Con Làm Giàu")})
gt_cases.append({"id": "TC081", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Tôi muốn tìm hiểu về nguồn gốc của vũ trụ và các lỗ đen không gian do nhà vật lý học thiên tài viết ra", "rel_ids": a_ids("Stephen Hawking")})
gt_cases.append({"id": "TC082", "group": "7. Câu hỏi dài (15-25 từ)", "query": "Sách nào kể về những câu chuyện tuổi thơ trong sáng của một cô bé đi học tại một trường tiểu học rất đặc biệt bên cửa sổ", "rel_ids": b_ids("Totto - Chan Bên Cửa Sổ")})

# 8. Unaccented (10 queries)
gt_cases.append({"id": "TC083", "group": "8. Tiếng Việt không dấu", "query": "nguoi dan ong mang ten ove", "rel_ids": b_ids("Người Đàn Ông Mang Tên Ove")})
gt_cases.append({"id": "TC084", "group": "8. Tiếng Việt không dấu", "query": "mat biec nguyen nhat anh", "rel_ids": b_ids("Mắt Biếc")})
gt_cases.append({"id": "TC085", "group": "8. Tiếng Việt không dấu", "query": "cay cam ngot cua toi", "rel_ids": b_ids("Cây Cam Ngọt Của Tôi")})
gt_cases.append({"id": "TC086", "group": "8. Tiếng Việt không dấu", "query": "nha gia kim paulo coelho", "rel_ids": b_ids("Nhà Giả Kim")})
gt_cases.append({"id": "TC087", "group": "8. Tiếng Việt không dấu", "query": "noi buon chien tranh bao ninh", "rel_ids": b_ids("Nỗi buồn chiến tranh")})
gt_cases.append({"id": "TC088", "group": "8. Tiếng Việt không dấu", "query": "an mang tren chuyen tau toc hanh phuong dong", "rel_ids": b_ids("Chuyến Tàu Tốc Hành Phương Đông")})
gt_cases.append({"id": "TC089", "group": "8. Tiếng Việt không dấu", "query": "khong gia dinh hector malot", "rel_ids": b_ids("Không Gia Đình")})
gt_cases.append({"id": "TC090", "group": "8. Tiếng Việt không dấu", "query": "toi muon hoc lap trinh cho nguoi moi bat dau", "rel_ids": kw_ids(["Lập Trình"])})
gt_cases.append({"id": "TC091", "group": "8. Tiếng Việt không dấu", "query": "sach day con lam giau robert kiyosaki", "rel_ids": b_ids("Dạy Con Làm Giàu")})
gt_cases.append({"id": "TC092", "group": "8. Tiếng Việt không dấu", "query": "giao trinh chuan hsk 1", "rel_ids": b_ids("Giáo Trình Chuẩn HSK 1")})

# 9. Typos / Misspellings (8 queries)
gt_cases.append({"id": "TC093", "group": "9. Lỗi chính tả / Gõ sai", "query": "Người đàn ông mang tên Ô-vê", "rel_ids": b_ids("Người Đàn Ông Mang Tên Ove")})
gt_cases.append({"id": "TC094", "group": "9. Lỗi chính tả / Gõ sai", "query": "Mat Biec - Nguyen Nhat Anh", "rel_ids": b_ids("Mắt Biếc")})
gt_cases.append({"id": "TC095", "group": "9. Lỗi chính tả / Gõ sai", "query": "Nhà giã kim", "rel_ids": b_ids("Nhà Giả Kim")})
gt_cases.append({"id": "TC096", "group": "9. Lỗi chính tả / Gõ sai", "query": "Cây cam ngột của tôi", "rel_ids": b_ids("Cây Cam Ngọt Của Tôi")})
gt_cases.append({"id": "TC097", "group": "9. Lỗi chính tả / Gõ sai", "query": "An mang tau toc hanh phuong dong", "rel_ids": b_ids("Chuyến Tàu Tốc Hành Phương Đông")})
gt_cases.append({"id": "TC098", "group": "9. Lỗi chính tả / Gõ sai", "query": "Sách tri tue nhan tao và machile learning", "rel_ids": kw_ids(["Trí Tuệ Nhân Tạo"])})
gt_cases.append({"id": "TC099", "group": "9. Lỗi chính tả / Gõ sai", "query": "To to chan ben cua so", "rel_ids": b_ids("Totto - Chan Bên Cửa Sổ")})
gt_cases.append({"id": "TC100", "group": "9. Lỗi chính tả / Gõ sai", "query": "Day kon lam giau", "rel_ids": b_ids("Dạy Con Làm Giàu")})

# 10. OOD (10 queries)
ood_queries = [
    "hướng dẫn sửa chữa xe máy Honda Wave Alpha tại nhà",
    "thuốc kháng sinh trị bệnh cảm cúm cho mèo con",
    "đặt vé máy bay giá rẻ đi Đà Nẵng tháng 11",
    "cách làm bánh pizza hải sản bằng nồi chiên không dầu",
    "bảng giá sửa chữa điện nước gia dụng tại quận 1",
    "dịch vụ cho thuê xe ô tô tự lái tại hà nội",
    "hướng dẫn cài đặt phần mềm chỉnh vang cơ chống hú micro",
    "mua hạt giống hoa hồng leo pháp ở đâu giá rẻ",
    "thực đơn ăn kiêng giảm cân cấp tốc trong 3 ngày",
    "dự báo thời tiết cuối tuần tại sa pa có tuyết không"
]
for i, q in enumerate(ood_queries, 101):
    gt_cases.append({"id": f"TC{i}", "group": "10. Ngoài kho dữ liệu (OOD)", "query": q, "rel_ids": []})

# Verification
print(f"Total curated test cases: {len(gt_cases)}")
empty_in_domain = [tc['id'] for tc in gt_cases[:100] if len(tc['rel_ids']) == 0]
print(f"In-Domain cases with empty target: {empty_in_domain}")

rel_counts = [len(tc['rel_ids']) for tc in gt_cases[:100]]
print(f"Target pool sizes for In-Domain: min={min(rel_counts)}, max={max(rel_counts)}, mean={np.mean(rel_counts):.2f}, median={np.median(rel_counts)}")

with open('tests/verified_ground_truth_110.json', 'w', encoding='utf-8') as f:
    json.dump(gt_cases, f, ensure_ascii=False, indent=2)

print("[+] Đã lưu Ground Truth chuẩn xác vào tests/verified_ground_truth_110.json!")
