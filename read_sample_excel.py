import pandas as pd
import json
import uuid
import datetime

# Đọc file Excel mẫu
data_file = 'attached_assets/Data 30-4-2025.xlsx'
df = pd.read_excel(data_file)

# In ra thông tin về dữ liệu
print("Thông tin dữ liệu từ file Excel:")
print(f"Số dòng: {len(df)}")
print(f"Số cột: {len(df.columns)}")
print("\nTên các cột:")
for col in df.columns:
    print(f"- {col}")

print("\nHiển thị 5 dòng đầu tiên:")
print(df.head().to_string())

# Xử lý và tạo khảo sát dựa trên dữ liệu
# Giả sử dòng đầu tiên chứa câu hỏi, dòng thứ hai chứa mã thuộc tính
questions = []
attribute_codes = []

if len(df) >= 2:
    # Lấy tên câu hỏi từ dòng đầu tiên
    for col in df.columns:
        if col.strip():  # Bỏ qua các cột không có tên
            questions.append(col)
    
    # Lấy mã thuộc tính từ dòng thứ hai
    second_row = df.iloc[0]
    for col in df.columns:
        attribute_code = second_row[col]
        if pd.notna(attribute_code):
            attribute_codes.append(str(attribute_code))
        else:
            attribute_codes.append("")

    print("\nCác câu hỏi từ dữ liệu:")
    for i, (question, code) in enumerate(zip(questions, attribute_codes)):
        print(f"{i+1}. {question} (Mã: {code})")

# Hàm để xác định loại câu hỏi dựa trên dữ liệu
def determine_question_type(column_data):
    # Bỏ qua 2 dòng đầu là tiêu đề và mã thuộc tính
    data = column_data.iloc[1:].dropna()
    
    if len(data) == 0:
        return "text"  # Nếu không có dữ liệu, mặc định là text
    
    # Kiểm tra nếu tất cả giá trị là số
    if pd.to_numeric(data, errors='coerce').notna().all():
        # Nếu chỉ có các giá trị từ 1-5 hoặc 1-10, có thể là thang đo Likert
        unique_values = data.unique()
        if set(unique_values).issubset(set(range(1, 6))):
            return "likert_scale"
        elif set(unique_values).issubset(set(range(1, 11))):
            return "likert_scale"
        else:
            return "number"
    
    # Kiểm tra nếu có ít giá trị duy nhất, có thể là multiple_choice
    unique_values = data.unique()
    if len(unique_values) <= 10:
        return "multiple_choice"
    
    # Mặc định là text
    return "text"

# Tạo định dạng khảo sát từ dữ liệu
survey = {
    "title": "Khảo sát được tạo từ dữ liệu mẫu",
    "description": "Khảo sát này được tạo tự động từ file Excel 'Data 30-4-2025.xlsx'",
    "created_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "questions": []
}

# Duyệt qua từng cột để tạo câu hỏi
for i, (col, code) in enumerate(zip(questions, attribute_codes)):
    column_data = df[col]
    question_type = determine_question_type(column_data)
    
    question = {
        "id": f"q{i+1}",
        "question_text": col,
        "type": question_type,
        "required": True
    }
    
    # Nếu là multiple_choice, thêm các tùy chọn
    if question_type == "multiple_choice":
        unique_values = column_data.iloc[1:].dropna().unique()
        question["options"] = sorted([str(v) for v in unique_values])
    
    # Nếu là likert_scale, thêm các thuộc tính của thang đo
    elif question_type == "likert_scale":
        unique_values = column_data.iloc[1:].dropna().unique()
        min_val = int(min(unique_values))
        max_val = int(max(unique_values))
        
        question["scale_min"] = min_val
        question["scale_max"] = max_val
        
        # Tạo nhãn cho thang đo
        if max_val == 5:
            question["scale_labels"] = ["Rất không đồng ý", "Không đồng ý", "Trung lập", "Đồng ý", "Rất đồng ý"]
        elif max_val == 10:
            question["scale_labels"] = [f"{i}" for i in range(min_val, max_val + 1)]
    
    survey["questions"].append(question)

# Tạo dữ liệu phản hồi từ dữ liệu mẫu
responses = []

# Bắt đầu từ dòng thứ 3 (bỏ qua tiêu đề và mã thuộc tính)
for row_idx in range(1, len(df)):
    row = df.iloc[row_idx]
    response = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for i, col in enumerate(questions):
        q_id = f"q{i+1}"
        value = row[col]
        
        # Xử lý các giá trị NaN
        if pd.isna(value):
            continue
        
        # Chuyển đổi kiểu dữ liệu phù hợp
        if survey["questions"][i]["type"] == "number" or survey["questions"][i]["type"] == "likert_scale":
            try:
                value = float(value)
                # Nếu là số nguyên, chuyển về int
                if value.is_integer():
                    value = int(value)
            except:
                # Nếu không thể chuyển thành số, giữ nguyên
                pass
        else:
            # Chuyển thành string cho các loại khác
            value = str(value)
        
        response[q_id] = value
    
    responses.append(response)

# Lưu khảo sát và phản hồi
survey_id = str(uuid.uuid4())

# Lưu vào file JSON
surveys = {survey_id: survey}
all_responses = {survey_id: responses}

with open('sample_surveys.json', 'w', encoding='utf-8') as f:
    json.dump(surveys, f, ensure_ascii=False, indent=2)

with open('sample_responses.json', 'w', encoding='utf-8') as f:
    json.dump(all_responses, f, ensure_ascii=False, indent=2)

print(f"\nĐã tạo khảo sát và {len(responses)} phản hồi từ dữ liệu mẫu")
print(f"Survey ID: {survey_id}")
print("Các file đã được lưu vào sample_surveys.json và sample_responses.json")