# Hướng dẫn triển khai ứng dụng lên hhd.one

Tài liệu này cung cấp các bước chi tiết để triển khai ứng dụng khảo sát lên nền tảng hhd.one.

## Yêu cầu hệ thống

- Python 3.9+ 
- Pip (trình quản lý gói Python)
- Truy cập vào máy chủ hhd.one

## Các bước triển khai

### 1. Tải và giải nén ứng dụng

Giải nén tệp `survey_app_deployment.zip` vào thư mục mong muốn trên máy chủ.

```bash
unzip survey_app_deployment.zip -d /path/to/app
cd /path/to/app
```

### 2. Cài đặt các phụ thuộc

Sử dụng pip để cài đặt các thư viện cần thiết từ tệp `deployment_requirements.txt`:

```bash
pip install -r deployment_requirements.txt
```

### 3. Cấu hình máy chủ

Đảm bảo rằng thư mục `.streamlit` tồn tại và chứa tệp `config.toml` với cấu hình phù hợp. Tệp này đã được bao gồm trong gói triển khai.

### 4. Cấu hình quyền truy cập tệp

Đảm bảo rằng ứng dụng có quyền ghi vào thư mục dữ liệu:

```bash
chmod -R 755 .
chmod -R 777 data
```

### 5. Khởi động ứng dụng

Sử dụng một trong các phương pháp sau để khởi động ứng dụng:

**Cách 1: Sử dụng Streamlit trực tiếp**

```bash
streamlit run app.py --server.port=8501
```

**Cách 2: Sử dụng Procfile với Gunicorn/Uvicorn (cho môi trường production)**

Nếu bạn đang sử dụng Heroku hoặc nền tảng tương tự:

```bash
web: streamlit run app.py
```

**Cách 3: Sử dụng supervisor hoặc systemd (khuyến nghị cho triển khai lâu dài)**

Tạo tệp cấu hình supervisor:

```
[program:streamlit]
command=streamlit run /path/to/app/app.py --server.port=8501
directory=/path/to/app
autostart=true
autorestart=true
stderr_logfile=/var/log/streamlit.err.log
stdout_logfile=/var/log/streamlit.out.log
user=your_user
```

### 6. Cấu hình reverse proxy (nếu cần)

Nếu bạn đang sử dụng Nginx làm reverse proxy, đây là một cấu hình mẫu:

```nginx
server {
    listen 80;
    server_name your-domain.hhd.one;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Cấu trúc thư mục

- `app.py`: Điểm vào chính của ứng dụng
- `pages/`: Các trang của ứng dụng
- `utils/`: Các module tiện ích
- `data/`: Thư mục lưu trữ dữ liệu
- `attached_assets/`: Tệp Excel và tài nguyên khác
- `.streamlit/`: Cấu hình Streamlit

## Xử lý sự cố

### Vấn đề: Ứng dụng không khởi động

Kiểm tra:
- Python và Streamlit đã được cài đặt chính xác
- Tất cả các phụ thuộc đã được cài đặt
- Quyền truy cập tệp và thư mục phù hợp

### Vấn đề: Lỗi "Address already in use"

```bash
lsof -i :8501  # Kiểm tra tiến trình đang sử dụng cổng
kill -9 [PID]  # Kết thúc tiến trình
```

### Vấn đề: Dữ liệu không được lưu

Kiểm tra quyền ghi vào thư mục `data/` và các tệp JSON như `surveys.json` và `responses.json`.

## Liên hệ hỗ trợ

Nếu bạn gặp vấn đề trong quá trình triển khai, vui lòng liên hệ:
- Email: [your-email@example.com]
- Điện thoại: [your-phone]