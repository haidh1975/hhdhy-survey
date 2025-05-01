# Ứng dụng khảo sát và phân tích dữ liệu

Ứng dụng web được xây dựng bằng Streamlit để tạo, phân phối và phân tích các khảo sát.

## Tính năng

- Tạo khảo sát với nhiều loại câu hỏi khác nhau
- Phân phối khảo sát thông qua liên kết hoặc mã QR
- Phân tích dữ liệu với các biểu đồ trực quan
- Phân tích nâng cao: Cronbach's Alpha, EFA, Hồi quy đa biến, CFA

## Yêu cầu hệ thống

- Python 3.9+
- Các thư viện được liệt kê trong `deployment_requirements.txt`

## Hướng dẫn triển khai trên hhd.one

### Bước 1: Clone dự án

```bash
git clone [URL_REPOSITORY]
cd [TÊN_THƯ_MỤC]
```

### Bước 2: Cài đặt dependencies

```bash
pip install -r deployment_requirements.txt
```

### Bước 3: Chạy ứng dụng

```bash
streamlit run app.py
```

## Cấu trúc dự án

- `app.py`: Trang chính của ứng dụng
- `pages/`: Thư mục chứa các trang của ứng dụng
  - `1_Create_Survey.py`: Tạo khảo sát
  - `2_Distribute_Survey.py`: Phân phối khảo sát
  - `3_View_Responses.py`: Xem kết quả khảo sát
  - `4_Data_Analysis.py`: Phân tích dữ liệu khảo sát
  - `5_Answer_Survey.py`: Trang trả lời khảo sát
- `utils/`: Thư mục chứa các module tiện ích
  - `data_analysis.py`: Hàm phân tích dữ liệu
  - `advanced_analysis.py`: Hàm phân tích nâng cao
  - `survey_utils.py`: Hàm tiện ích cho khảo sát
  - `visualization.py`: Hàm trực quan hóa dữ liệu
- `.streamlit/config.toml`: Cấu hình Streamlit

## Triển khai lên hhd.one

1. Đăng nhập vào tài khoản hhd.one của bạn
2. Tạo một ứng dụng mới
3. Cấu hình môi trường Python và cài đặt các dependencies từ file `deployment_requirements.txt`
4. Triển khai mã nguồn
5. Khởi chạy ứng dụng với lệnh `streamlit run app.py`

## Lưu ý khi triển khai

- Đảm bảo rằng các thư mục `data/` và `.streamlit/` được tạo đúng cách
- Có thể cần cấu hình CORS để cho phép các yêu cầu từ các nguồn khác nhau
- Đảm bảo quyền ghi cho các file JSON lưu trữ dữ liệu khảo sát và phản hồi