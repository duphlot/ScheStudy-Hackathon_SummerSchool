import csv
import random
from datetime import datetime, timedelta

# Tạo student_id chuyên nghiệp hơn: VD 20250001, 20250002 ...
students = [{"student_id": f"202500{str(i).zfill(2)}"} for i in range(1, 300)]

# Các môn học
subjects = ["Toán", "Lý", "Hóa", "Sinh", "Sử", "Địa", "GDCD", "Văn", "Anh"]

# Chủ đề/mảng kiến thức giả
topics_per_subject = {
    "Toán": ["Tích phân", "Nguyên hàm", "Hàm số", "Logarit", "Lượng giác", "Hình học", "Thống kê", "Xác suất", "Dãy số", "Giới hạn"],
    "Lý": ["Dao động cơ học", "Sóng cơ học", "Điện xoay chiều", "Hạt nhân", "Điện từ", "Quang học", "Nhiệt học", "Cơ học", "Điện học", "Vật lý hiện đại"],
    "Hóa": ["Điện li", "Hydrocarbon", "Polymer", "Kim loại", "Phi kim", "Hóa hữu cơ", "Hóa vô cơ", "Phản ứng", "Cân bằng", "Nhiệt hóa học"],
    "Sinh": ["Di truyền", "Tiến hóa", "Sinh thái", "Hệ sinh thái", "Tế bào", "Sinh lý", "Thực vật", "Động vật", "Vi sinh", "Sinh học phân tử"],
    "Sử": ["Kháng chiến", "Cách mạng", "Thời kỳ phong kiến", "Hiện đại", "Thế giới cận đại", "Việt Nam cận đại", "Chiến tranh lạnh", "Toàn cầu hóa", "Dân chủ", "Xã hội chủ nghĩa"],
    "Địa": ["Địa hình", "Khí hậu", "Dân số", "Tài nguyên", "Kinh tế", "Môi trường", "Đô thị hóa", "Nông nghiệp", "Công nghiệp", "Thủy văn"],
    "GDCD": ["Pháp luật", "Đạo đức", "Quyền công dân", "Kỹ năng sống", "Hiến pháp", "Nhà nước", "Xã hội", "Gia đình", "Trường học", "Cộng đồng"],
    "Văn": ["Đọc hiểu", "Nghị luận XH", "Nghị luận VH", "Tiếng Việt", "Thơ", "Truyện", "Kịch", "Phong cách", "Tu từ", "Ngữ pháp"],
    "Anh": ["Ngữ pháp", "Giao tiếp", "Đọc hiểu", "Viết", "Nghe", "Từ vựng", "Phát âm", "Văn hóa", "Dịch thuật", "Văn học"]
}

# Mức độ vận dụng
levels = ["Nhận biết", "Thông hiểu", "Vận dụng thấp", "Vận dụng cao"]

# Tạo danh sách ngày kiểm tra (trong vòng 6 tháng gần đây)
def generate_test_dates():
    start_date = datetime(2024, 9, 1)  # Bắt đầu năm học
    end_date = datetime(2025, 7, 13)   # Hiện tại
    
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        # Tạo ngày kiểm tra mỗi tuần (thứ 2, 4, 6)
        if current_date.weekday() in [0, 2, 4]:  # Monday, Wednesday, Friday
            dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    return dates

test_dates = generate_test_dates()

# Tạo thông tin lớp học
classes = [f"12A{i}" for i in range(1, 11)] + [f"12B{i}" for i in range(1, 6)]

# Tạo điểm số thực tế hơn
def generate_score():
    # Tạo phân bố điểm gần giống thực tế
    score_weights = {
        range(0, 3): 0.05,   # Kém
        range(3, 5): 0.15,   # Yếu
        range(5, 7): 0.35,   # Trung bình
        range(7, 8): 0.25,   # Khá
        range(8, 9): 0.15,   # Giỏi
        range(9, 11): 0.05   # Xuất sắc
    }
    
    rand = random.random()
    cumulative = 0
    
    for score_range, weight in score_weights.items():
        cumulative += weight
        if rand <= cumulative:
            return round(random.uniform(score_range.start, score_range.stop-0.1), 1)
    
    return 7.0  # Default

# Tạo danh sách kết quả
results = []

result_id = 1

for student in students:
    # Gán lớp ngẫu nhiên cho học sinh
    student_class = random.choice(classes)
    
    # Tạo profile năng lực học sinh (một số giỏi, một số yếu)
    student_ability = random.choices(
        ["xuất sắc", "giỏi", "khá", "trung bình", "yếu"], 
        weights=[0.05, 0.15, 0.25, 0.35, 0.20]
    )[0]
    
    for subject in subjects:
        # Mỗi học sinh làm 3-7 bài kiểm tra mỗi môn trong năm
        num_tests = random.randint(3, 7)
        
        for test_num in range(num_tests):
            test_date = random.choice(test_dates)
            
            # Số lượng câu hỏi trong bài kiểm tra
            total_questions = random.randint(15, 30)
            
            # Tạo kết quả cho từng câu hỏi
            for question_num in range(1, total_questions + 1):
                topic = random.choice(topics_per_subject[subject])
                level = random.choice(levels)
                
                # Tính xác suất đúng dựa trên năng lực học sinh và độ khó
                base_correct_prob = {
                    "xuất sắc": 0.9,
                    "giỏi": 0.8,
                    "khá": 0.7,
                    "trung bình": 0.6,
                    "yếu": 0.4
                }[student_ability]
                
                # Điều chỉnh xác suất theo độ khó
                level_modifier = {
                    "Nhận biết": 0.15,
                    "Thông hiểu": 0.05,
                    "Vận dụng thấp": -0.05,
                    "Vận dụng cao": -0.15
                }[level]
                
                correct_prob = max(0.1, min(0.95, base_correct_prob + level_modifier))
                is_correct = 1 if random.random() < correct_prob else 0
                
                # Tạo thời gian làm bài (giây)
                time_taken = random.randint(30, 300)
                
                results.append({
                    "result_id": result_id,
                    "student_id": student["student_id"],
                    "student_class": student_class,
                    "subject": subject,
                    "test_date": test_date,
                    "test_number": test_num + 1,
                    "question_number": question_num,
                    "topic": topic,
                    "level": level,
                    "is_correct": is_correct,
                    "time_taken_seconds": time_taken,
                    "student_ability": student_ability
                })
                result_id += 1

# Xuất CSV
header = ["result_id", "student_id", "student_class", "subject", "test_date", "test_number", 
          "question_number", "topic", "level", "is_correct", "time_taken_seconds", "student_ability"]

with open("fake_student_results_professional.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=header)
    writer.writeheader()
    writer.writerows(results)

print(f"Đã tạo {len(results)} bản ghi dữ liệu cho {len(students)} học sinh")
print(f"Dữ liệu đã được lưu vào file: fake_student_results_professional.csv")