# Hướng Dẫn Triển Khai Ứng Dụng Khảo Sát

## Tổng Quan

Tài liệu này hướng dẫn cách triển khai ứng dụng khảo sát Streamlit lên máy chủ web, cụ thể là domain hhd.one. Ứng dụng này là một công cụ khảo sát toàn diện cho phép tạo, phân phối, thu thập và phân tích dữ liệu khảo sát.

## Yêu Cầu Hệ Thống

- Python 3.10+ đã cài đặt
- Pip (quản lý gói Python)
- Quyền truy cập SSH vào máy chủ (nếu triển khai trên máy chủ riêng)
- Domain đã cài đặt và trỏ về máy chủ (hhd.one)

## Các Bước Triển Khai

### 1. Chuẩn Bị Môi Trường

#### Trên Server Ubuntu/Debian:

```bash
# Cập nhật hệ thống
sudo apt update
sudo apt upgrade -y

# Cài đặt Python và các công cụ cần thiết
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# Tạo thư mục cho ứng dụng
sudo mkdir -p /var/www/survey_app
sudo chown $USER:$USER /var/www/survey_app
```

### 2. Triển Khai Mã Nguồn

#### Tải lên và giải nén mã nguồn:

```bash
# Giả sử bạn đã tải lên file survey_app_deployment.zip
cd /var/www/survey_app
unzip /path/to/survey_app_deployment.zip -d .
```

#### Tạo môi trường ảo và cài đặt dependencies:

```bash
cd /var/www/survey_app
python3 -m venv venv
source venv/bin/activate
pip install -r deployment_requirements.txt
```

### 3. Cấu Hình Streamlit

Tạo file cấu hình Streamlit:

```bash
mkdir -p /var/www/survey_app/.streamlit
```

Tạo file `/var/www/survey_app/.streamlit/config.toml` với nội dung:

```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = false
port = 8501
address = "0.0.0.0"
```

### 4. Cấu Hình Supervisor

Tạo file cấu hình Supervisor để quản lý quy trình Streamlit:

```bash
sudo nano /etc/supervisor/conf.d/survey_app.conf
```

Thêm nội dung sau:

```ini
[program:survey_app]
command=/var/www/survey_app/venv/bin/streamlit run /var/www/survey_app/app.py --server.port=8501
directory=/var/www/survey_app
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/survey_app/streamlit.err.log
stdout_logfile=/var/log/survey_app/streamlit.out.log
```

Tạo thư mục log:

```bash
sudo mkdir -p /var/log/survey_app
sudo chown www-data:www-data /var/log/survey_app
```

Cập nhật và khởi động lại Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start survey_app
```

### 5. Cấu Hình Nginx

Tạo cấu hình Nginx cho ứng dụng:

```bash
sudo nano /etc/nginx/sites-available/survey_app.conf
```

Thêm nội dung sau (điều chỉnh domain phù hợp):

```nginx
server {
    listen 80;
    server_name hhd.one www.hhd.one;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

Kích hoạt cấu hình:

```bash
sudo ln -s /etc/nginx/sites-available/survey_app.conf /etc/nginx/sites-enabled/
sudo nginx -t  # Kiểm tra cấu hình
sudo systemctl restart nginx
```

### 6. Cấu Hình HTTPS (SSL)

Cài đặt Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

Lấy chứng chỉ SSL:

```bash
sudo certbot --nginx -d hhd.one -d www.hhd.one
```

Làm theo hướng dẫn trên màn hình để hoàn tất cài đặt SSL.

### 7. Kiểm Tra Triển Khai

Truy cập vào domain của bạn (https://hhd.one) để xác nhận rằng ứng dụng đang hoạt động.

## Quản Lý Ứng Dụng

### Khởi động/dừng ứng dụng:

```bash
sudo supervisorctl start survey_app
sudo supervisorctl stop survey_app
sudo supervisorctl restart survey_app
```

### Xem logs:

```bash
sudo tail -f /var/log/survey_app/streamlit.out.log
sudo tail -f /var/log/survey_app/streamlit.err.log
```

### Cập nhật ứng dụng:

```bash
cd /var/www/survey_app
source venv/bin/activate
# Tải và giải nén phiên bản mới
# cập nhật các dependencies nếu cần
pip install -r deployment_requirements.txt
sudo supervisorctl restart survey_app
```

## Khắc Phục Sự Cố

### Ứng dụng không khởi động:
- Kiểm tra logs: `sudo tail -f /var/log/survey_app/streamlit.err.log`
- Xác minh môi trường ảo: `cd /var/www/survey_app && source venv/bin/activate`
- Kiểm tra cài đặt: `pip list | grep streamlit`

### Không thể truy cập trang web:
- Kiểm tra trạng thái Nginx: `sudo systemctl status nginx`
- Kiểm tra cấu hình Nginx: `sudo nginx -t`
- Xác minh rằng Streamlit đang chạy: `sudo supervisorctl status survey_app`

### Các vấn đề về quyền:
- Đảm bảo thư mục ứng dụng có quyền thích hợp: `sudo chown -R www-data:www-data /var/www/survey_app`
- Kiểm tra quyền của thư mục log: `sudo chown -R www-data:www-data /var/log/survey_app`

## Liên Hệ Hỗ Trợ

Nếu bạn gặp vấn đề trong quá trình triển khai, vui lòng liên hệ đội hỗ trợ kỹ thuật tại: support@hhd.one

---

Tài liệu này được cập nhật lần cuối vào: 02/05/2025