# Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp

Ứng dụng web khảo sát toàn diện được xây dựng bằng Streamlit, cho phép tạo, phân phối, thu thập và phân tích dữ liệu khảo sát về ảnh hưởng của vốn xã hội và vốn nhân lực đến sự phát triển bền vững của doanh nghiệp tại tỉnh Hưng Yên.

## Tính năng chính

- **Tạo khảo sát** - Tạo khảo sát tùy chỉnh với nhiều loại câu hỏi (trắc nghiệm, thang đo Likert, văn bản, v.v.)
- **Phân phối khảo sát** - Chia sẻ khảo sát qua URL hoặc mã QR
- **Thu thập dữ liệu** - Thu thập phản hồi và lưu trữ kết quả dễ dàng
- **Phân tích dữ liệu** - Phân tích kết quả với biểu đồ trực quan và bảng thống kê
- **Phân tích nâng cao** - Cronbach's Alpha, EFA (Phân tích nhân tố khám phá), Hồi quy đa biến, CFA (Phân tích nhân tố khẳng định)
- **Song ngữ Việt-Anh** - Giao diện người dùng đa ngôn ngữ

## Yêu cầu hệ thống

- Python 3.10+
- Các thư viện Python (xem `deployment_requirements.txt`)
- Nginx (cho triển khai web)
- Supervisor (cho quản lý quy trình)

## Triển khai trên hhd.one

### Phương pháp 1: Sử dụng script cài đặt tự động

```bash
# Tải lên máy chủ và cấp quyền thực thi
chmod +x install.sh

# Chạy script cài đặt
sudo ./install.sh
```

### Phương pháp 2: Cài đặt thủ công

1. **Chuẩn bị máy chủ**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-pip python3-venv nginx supervisor
   ```

2. **Cài đặt mã nguồn**:
   ```bash
   sudo mkdir -p /var/www/survey_app
   sudo chown $USER:$USER /var/www/survey_app
   # Giải nén hoặc sao chép mã nguồn vào /var/www/survey_app
   ```

3. **Cài đặt môi trường Python**:
   ```bash
   cd /var/www/survey_app
   python3 -m venv venv
   source venv/bin/activate
   pip install -r deployment_requirements.txt
   ```

4. **Cấu hình Supervisor**:
   ```bash
   sudo cp supervisor_config.conf /etc/supervisor/conf.d/survey_app.conf
   sudo supervisorctl reread
   sudo supervisorctl update
   ```

5. **Cấu hình Nginx**:
   ```bash
   sudo cp nginx_config.conf /etc/nginx/sites-available/survey_app.conf
   sudo ln -s /etc/nginx/sites-available/survey_app.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

6. **Cấu hình SSL với Certbot**:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d hhd.one -d www.hhd.one
   ```

## Cấu trúc dự án

```
.
├── app.py                  # Trang chính của ứng dụng
├── pages/                  # Các trang ứng dụng
│   ├── 1_Create_Survey.py  # Tạo khảo sát
│   ├── 2_Distribute_Survey.py  # Phân phối khảo sát
│   ├── 3_View_Responses.py  # Xem phản hồi
│   ├── 4_Data_Analysis.py  # Phân tích dữ liệu
│   └── 5_Answer_Survey.py  # Trả lời khảo sát
├── utils/                  # Tiện ích và hàm
│   ├── data_analysis.py    # Phân tích dữ liệu
│   ├── advanced_analysis.py  # Phân tích thống kê nâng cao
│   ├── survey_utils.py     # Tiện ích khảo sát
│   └── visualization.py    # Trực quan hóa dữ liệu
├── .streamlit/             # Cấu hình Streamlit
│   └── config.toml
├── deployment_requirements.txt  # Dependencies
├── install.sh              # Script cài đặt
├── nginx_config.conf       # Cấu hình Nginx
├── supervisor_config.conf  # Cấu hình Supervisor
├── runtime.txt             # Phiên bản Python
└── DEPLOYMENT_GUIDE.md     # Hướng dẫn triển khai chi tiết
```

## Quản lý ứng dụng

### Khởi động/dừng/khởi động lại ứng dụng:

```bash
sudo supervisorctl start survey_app
sudo supervisorctl stop survey_app
sudo supervisorctl restart survey_app
```

### Xem logs:

```bash
sudo tail -f /var/log/survey_app/streamlit.out.log  # Logs thông thường
sudo tail -f /var/log/survey_app/streamlit.err.log  # Logs lỗi
```

### Cập nhật ứng dụng:

```bash
cd /var/www/survey_app
source venv/bin/activate
# Cập nhật mã nguồn
pip install -r deployment_requirements.txt  # Cập nhật dependencies nếu cần
sudo supervisorctl restart survey_app
```

## Thông tin liên hệ

Để được hỗ trợ triển khai, vui lòng liên hệ support@hhd.one

---

## Giấy phép

© 2025 Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp. Tất cả các quyền được bảo lưu.