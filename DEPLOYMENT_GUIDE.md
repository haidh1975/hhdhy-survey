# Hướng dẫn triển khai chi tiết

Tài liệu này cung cấp hướng dẫn chi tiết để triển khai ứng dụng khảo sát trên máy chủ web hhd.one.

## 1. Chuẩn bị máy chủ

Đảm bảo máy chủ của bạn đáp ứng các yêu cầu sau:
- Hệ điều hành: Ubuntu 20.04 LTS hoặc mới hơn
- RAM: Tối thiểu 2GB
- CPU: Tối thiểu 1 vCPU
- Dung lượng đĩa: Tối thiểu 10GB
- Tên miền đã cấu hình: hhd.one (nếu bạn dùng tên miền khác, cần điều chỉnh cấu hình tương ứng)

## 2. Cài đặt tự động

Cách đơn giản nhất để triển khai ứng dụng là sử dụng script cài đặt tự động đã cung cấp:

1. Tải tệp nén có chứa mã nguồn lên máy chủ:
   ```bash
   scp survey_app_deployment.zip user@your_server_ip:/home/user/
   ```

2. Kết nối SSH vào máy chủ:
   ```bash
   ssh user@your_server_ip
   ```

3. Giải nén tệp:
   ```bash
   unzip survey_app_deployment.zip
   cd survey_app_deployment
   ```

4. Cấp quyền thực thi cho script cài đặt:
   ```bash
   chmod +x install.sh
   ```

5. Chạy script cài đặt:
   ```bash
   sudo ./install.sh
   ```

Script sẽ tự động:
- Cài đặt tất cả các gói phụ thuộc cần thiết
- Tạo môi trường ảo Python
- Cài đặt mã nguồn và cấu hình
- Cấu hình Nginx và Supervisor
- Khởi động ứng dụng

## 3. Cài đặt thủ công

Nếu bạn muốn kiểm soát chi tiết quá trình cài đặt, bạn có thể cài đặt thủ công:

### 3.1 Cài đặt các gói phụ thuộc

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx supervisor
```

### 3.2 Tạo thư mục ứng dụng

```bash
sudo mkdir -p /var/www/survey_app
sudo chown $USER:$USER /var/www/survey_app
sudo mkdir -p /var/log/survey_app
sudo chown $USER:$USER /var/log/survey_app
```

### 3.3 Sao chép mã nguồn

Giả sử bạn đã tải và giải nén mã nguồn:

```bash
cp -r /path/to/extracted/files/* /var/www/survey_app/
cp -r /path/to/extracted/files/.streamlit /var/www/survey_app/
```

### 3.4 Tạo môi trường ảo và cài đặt các gói

```bash
cd /var/www/survey_app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r deployment_requirements.txt
```

### 3.5 Cấu hình Supervisor

Tạo tệp cấu hình Supervisor:

```bash
sudo cp /var/www/survey_app/supervisor_config.conf /etc/supervisor/conf.d/survey_app.conf
sudo supervisorctl reread
sudo supervisorctl update
```

### 3.6 Cấu hình Nginx

```bash
sudo cp /var/www/survey_app/nginx_config.conf /etc/nginx/sites-available/survey_app.conf
sudo ln -sf /etc/nginx/sites-available/survey_app.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3.7 Cấu hình HTTPS với Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d hhd.one -d www.hhd.one
```

## 4. Xác minh cài đặt

Sau khi cài đặt, bạn có thể xác minh rằng ứng dụng đang chạy:

1. Kiểm tra trạng thái Supervisor:
   ```bash
   sudo supervisorctl status survey_app
   ```

2. Kiểm tra logs:
   ```bash
   sudo tail -f /var/log/survey_app/streamlit.out.log
   ```

3. Truy cập ứng dụng web:
   - Nếu bạn đã cấu hình tên miền: https://hhd.one
   - Nếu chưa: http://your_server_ip:5000

## 5. Khắc phục sự cố

### 5.1 Ứng dụng không khởi động

Kiểm tra logs lỗi:
```bash
sudo tail -f /var/log/survey_app/streamlit.err.log
```

### 5.2 Vấn đề quyền truy cập

Đảm bảo quyền phù hợp cho thư mục ứng dụng:
```bash
sudo chown -R www-data:www-data /var/www/survey_app
sudo chown -R www-data:www-data /var/log/survey_app
```

### 5.3 Nginx không hoạt động

Kiểm tra cấu hình Nginx:
```bash
sudo nginx -t
```

Kiểm tra logs Nginx:
```bash
sudo tail -f /var/log/nginx/error.log
```

### 5.4 Khởi động lại các dịch vụ

```bash
sudo systemctl restart nginx
sudo supervisorctl restart survey_app
```

## 6. Bảo trì

### 6.1 Sao lưu dữ liệu

Dữ liệu khảo sát được lưu trữ trong các tệp JSON. Hãy sao lưu chúng thường xuyên:
```bash
sudo cp /var/www/survey_app/surveys.json /backup/surveys_$(date +%Y%m%d).json
sudo cp /var/www/survey_app/responses.json /backup/responses_$(date +%Y%m%d).json
```

### 6.2 Cập nhật mã nguồn

Khi có phiên bản mới:
```bash
# Sao lưu dữ liệu hiện tại
sudo cp /var/www/survey_app/surveys.json /backup/surveys_$(date +%Y%m%d).json
sudo cp /var/www/survey_app/responses.json /backup/responses_$(date +%Y%m%d).json

# Cập nhật mã nguồn (ví dụ, từ tệp nén mới)
cd /tmp
unzip new_survey_app.zip
sudo cp -r new_survey_app/* /var/www/survey_app/

# Cập nhật dependencies nếu cần
cd /var/www/survey_app
source venv/bin/activate
pip install -r deployment_requirements.txt

# Khôi phục dữ liệu nếu cần
sudo cp /backup/surveys_$(date +%Y%m%d).json /var/www/survey_app/surveys.json
sudo cp /backup/responses_$(date +%Y%m%d).json /var/www/survey_app/responses.json

# Khởi động lại ứng dụng
sudo supervisorctl restart survey_app
```

## 7. Tùy chỉnh

### 7.1 Thay đổi cổng

Nếu bạn muốn chạy ứng dụng trên cổng khác, cập nhật các tệp sau:
- `/var/www/survey_app/.streamlit/config.toml`
- `/etc/supervisor/conf.d/survey_app.conf`
- `/etc/nginx/sites-available/survey_app.conf`

### 7.2 Thay đổi domain

Nếu bạn muốn sử dụng tên miền khác, cập nhật:
- `/etc/nginx/sites-available/survey_app.conf`
- Sau đó chạy lại Certbot với tên miền mới

## 8. Bảo mật

- Đảm bảo cập nhật hệ thống thường xuyên: `sudo apt update && sudo apt upgrade -y`
- Cân nhắc thêm tường lửa UFW: `sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw allow 22/tcp`
- Kiểm tra và đảm bảo HTTPS được cấu hình đúng
- Xem xét thêm xác thực cơ bản HTTP nếu cần hạn chế truy cập

## Thông tin liên hệ

Nếu bạn gặp vấn đề trong quá trình triển khai, vui lòng liên hệ support@hhd.one