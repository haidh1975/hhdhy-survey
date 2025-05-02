#!/bin/bash

# Cài đặt script cho ứng dụng khảo sát
# Được thiết kế để chạy trên Ubuntu/Debian
# Sử dụng: sudo bash install.sh

set -e

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then
  echo "Vui lòng chạy script với quyền root (sudo)"
  exit 1
fi

echo "===== Bắt đầu quá trình cài đặt ứng dụng khảo sát ====="

# Cập nhật hệ thống
echo "Đang cập nhật hệ thống..."
apt update
apt upgrade -y

# Cài đặt các công cụ cần thiết
echo "Đang cài đặt Python và các công cụ cần thiết..."
apt install -y python3 python3-pip python3-venv nginx supervisor certbot python3-certbot-nginx

# Tạo thư mục ứng dụng
echo "Đang chuẩn bị thư mục ứng dụng..."
mkdir -p /var/www/survey_app
mkdir -p /var/log/survey_app

# Sao chép tệp từ thư mục hiện tại đến thư mục ứng dụng
echo "Đang sao chép các tệp ứng dụng..."
cp -r ./* /var/www/survey_app/
cp -r ./.streamlit /var/www/survey_app/

# Đặt quyền thích hợp
echo "Đang đặt quyền thích hợp..."
chown -R www-data:www-data /var/www/survey_app
chown -R www-data:www-data /var/log/survey_app

# Tạo môi trường ảo và cài đặt yêu cầu
echo "Đang tạo môi trường ảo và cài đặt các gói..."
cd /var/www/survey_app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r deployment_requirements.txt

# Cấu hình Supervisor
echo "Đang cấu hình Supervisor..."
cp supervisor_config.conf /etc/supervisor/conf.d/survey_app.conf
supervisorctl reread
supervisorctl update

# Cấu hình Nginx
echo "Đang cấu hình Nginx..."
cp nginx_config.conf /etc/nginx/sites-available/survey_app.conf
ln -sf /etc/nginx/sites-available/survey_app.conf /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

echo "===== Cài đặt hoàn tất ====="
echo ""
echo "Ứng dụng khảo sát đã được cài đặt thành công!"
echo "Bạn có thể truy cập ứng dụng tại: http://IP_server:5000 hoặc http://hhd.one (nếu domain đã được cấu hình)"
echo ""
echo "Để cấu hình SSL (HTTPS), hãy chạy: sudo certbot --nginx -d hhd.one -d www.hhd.one"
echo ""
echo "Để quản lý ứng dụng, sử dụng các lệnh sau:"
echo "  - Khởi động: sudo supervisorctl start survey_app"
echo "  - Dừng: sudo supervisorctl stop survey_app"
echo "  - Khởi động lại: sudo supervisorctl restart survey_app"
echo "  - Kiểm tra trạng thái: sudo supervisorctl status survey_app"
echo ""
echo "Để xem logs:"
echo "  - Logs lỗi: sudo tail -f /var/log/survey_app/streamlit.err.log"
echo "  - Logs thông thường: sudo tail -f /var/log/survey_app/streamlit.out.log"