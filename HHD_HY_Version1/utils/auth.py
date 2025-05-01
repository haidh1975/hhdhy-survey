import streamlit as st
import json
import os
import hashlib
import re
from datetime import datetime, timedelta
import uuid

# Đường dẫn đến file lưu trữ thông tin người dùng
USER_DB_PATH = "data/users.json"
SESSIONS_DB_PATH = "data/sessions.json"

# Cấu trúc quyền hạn
ROLES = {
    "admin": {
        "description": "Toàn quyền quản trị hệ thống",
        "permissions": ["create_survey", "edit_survey", "delete_survey", "view_responses", 
                       "analyze_data", "manage_users", "export_data", "import_data", "manage_forms"]
    },
    "manager": {
        "description": "Quản lý khảo sát và phân tích",
        "permissions": ["create_survey", "edit_survey", "view_responses", "analyze_data", "export_data", "manage_forms"]
    },
    "editor": {
        "description": "Tạo và chỉnh sửa khảo sát",
        "permissions": ["create_survey", "edit_survey", "view_responses", "manage_forms"]
    },
    "viewer": {
        "description": "Chỉ xem kết quả",
        "permissions": ["view_responses"]
    },
    "respondent": {
        "description": "Chỉ trả lời khảo sát",
        "permissions": ["answer_survey"]
    }
}

def init_auth():
    """Khởi tạo hệ thống xác thực"""
    # Tạo thư mục data nếu chưa tồn tại
    os.makedirs("data", exist_ok=True)
    
    # Tạo file người dùng nếu chưa tồn tại
    if not os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, "w") as f:
            # Tạo tài khoản admin mặc định
            default_admin = {
                "admin@hhd.one": {
                    "password": hash_password("admin123"),
                    "name": "Admin",
                    "role": "admin",
                    "email": "admin@hhd.one",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None
                }
            }
            json.dump(default_admin, f)
    
    # Tạo file sessions nếu chưa tồn tại
    if not os.path.exists(SESSIONS_DB_PATH):
        with open(SESSIONS_DB_PATH, "w") as f:
            json.dump({}, f)
    
    # Khởi tạo session state cho auth
    if "user" not in st.session_state:
        st.session_state.user = None
    
    if "language" not in st.session_state:
        st.session_state.language = "vi"  # Mặc định là tiếng Việt

def load_users():
    """Tải danh sách người dùng từ file"""
    if os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    """Lưu danh sách người dùng vào file"""
    with open(USER_DB_PATH, "w") as f:
        json.dump(users, f)

def load_sessions():
    """Tải danh sách phiên đăng nhập từ file"""
    if os.path.exists(SESSIONS_DB_PATH):
        with open(SESSIONS_DB_PATH, "r") as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    """Lưu danh sách phiên đăng nhập vào file"""
    with open(SESSIONS_DB_PATH, "w") as f:
        json.dump(sessions, f)

def hash_password(password):
    """Mã hóa mật khẩu bằng SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, password, name, role="respondent"):
    """Tạo người dùng mới"""
    # Kiểm tra email hợp lệ
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Email không hợp lệ"
    
    # Kiểm tra mật khẩu đủ mạnh
    if len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự"
    
    users = load_users()
    
    # Kiểm tra email đã tồn tại chưa
    if email in users:
        return False, "Email đã được sử dụng"
    
    # Tạo người dùng mới
    users[email] = {
        "password": hash_password(password),
        "name": name,
        "role": role,
        "email": email,
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }
    
    save_users(users)
    return True, "Tạo tài khoản thành công"

def login(email, password):
    """Đăng nhập người dùng"""
    users = load_users()
    
    if email not in users:
        return False, "Email hoặc mật khẩu không đúng"
    
    user = users[email]
    
    if user["password"] != hash_password(password):
        return False, "Email hoặc mật khẩu không đúng"
    
    # Cập nhật thời gian đăng nhập cuối cùng
    user["last_login"] = datetime.now().isoformat()
    save_users(users)
    
    # Tạo phiên đăng nhập mới
    session_id = str(uuid.uuid4())
    sessions = load_sessions()
    sessions[session_id] = {
        "email": email,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=1)).isoformat()
    }
    save_sessions(sessions)
    
    # Lưu thông tin người dùng vào session
    st.session_state.user = user
    st.session_state.session_id = session_id
    
    return True, "Đăng nhập thành công"

def logout():
    """Đăng xuất người dùng"""
    if "session_id" in st.session_state:
        sessions = load_sessions()
        if st.session_state.session_id in sessions:
            del sessions[st.session_state.session_id]
        save_sessions(sessions)
        
    st.session_state.user = None
    if "session_id" in st.session_state:
        del st.session_state.session_id

def check_permission(permission):
    """Kiểm tra quyền hạn của người dùng hiện tại"""
    if not st.session_state.user:
        return False
    
    role = st.session_state.user["role"]
    if role not in ROLES:
        return False
    
    return permission in ROLES[role]["permissions"]

def require_login():
    """Yêu cầu đăng nhập để tiếp tục"""
    if not st.session_state.user:
        st.warning("Bạn cần đăng nhập để truy cập trang này")
        show_login_form()
        st.stop()

def require_permission(permission):
    """Yêu cầu quyền hạn cụ thể để tiếp tục"""
    require_login()
    
    if not check_permission(permission):
        st.error("Bạn không có quyền truy cập chức năng này")
        st.stop()

def show_login_form():
    """Hiển thị biểu mẫu đăng nhập"""
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")
        
        if submitted:
            success, message = login(email, password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("---")
    
    if st.button("Đăng ký tài khoản mới"):
        st.session_state.show_register = True
    
    if st.session_state.get("show_register", False):
        with st.form("register_form"):
            st.subheader("Đăng ký tài khoản mới")
            new_email = st.text_input("Email")
            new_name = st.text_input("Họ tên")
            new_password = st.text_input("Mật khẩu", type="password")
            confirm_password = st.text_input("Xác nhận mật khẩu", type="password")
            
            submitted = st.form_submit_button("Đăng ký")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Mật khẩu xác nhận không khớp")
                else:
                    success, message = create_user(new_email, new_password, new_name)
                    if success:
                        st.success(message)
                        st.session_state.show_register = False
                    else:
                        st.error(message)

def has_responded(survey_id, email):
    """Kiểm tra xem người dùng đã trả lời khảo sát chưa"""
    if not os.path.exists("responses.json"):
        return False
        
    with open("responses.json", "r") as f:
        responses = json.load(f)
    
    if survey_id not in responses:
        return False
    
    for response in responses[survey_id]:
        if response.get("email") == email:
            return True
    
    return False

def switch_language():
    """Chuyển đổi ngôn ngữ hiển thị"""
    if st.session_state.language == "vi":
        st.session_state.language = "en"
    else:
        st.session_state.language = "vi"
        
def get_translation(key, lang=None):
    """Lấy bản dịch theo ngôn ngữ hiện tại"""
    if lang is None:
        lang = st.session_state.language
        
    translations = {
        "app_title": {
            "vi": "Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên",
            "en": "Survey on the Impact of Social Capital and Human Capital on Sustainable Development of Enterprises in Hung Yen Province"
        },
        "login": {
            "vi": "Đăng nhập",
            "en": "Login"
        },
        "logout": {
            "vi": "Đăng xuất",
            "en": "Logout"
        },
        "welcome": {
            "vi": "Chào mừng",
            "en": "Welcome"
        },
        "dashboard": {
            "vi": "Bảng điều khiển",
            "en": "Dashboard"
        },
        "total_surveys": {
            "vi": "Tổng số khảo sát",
            "en": "Total surveys"
        },
        "total_responses": {
            "vi": "Tổng số phản hồi",
            "en": "Total responses"
        },
        "average_responses": {
            "vi": "Phản hồi trung bình",
            "en": "Average responses"
        },
        "total_questions": {
            "vi": "Tổng số câu hỏi",
            "en": "Total questions"
        },
        "existing_surveys": {
            "vi": "Khảo sát hiện có",
            "en": "Existing surveys"
        },
        "create_survey": {
            "vi": "Tạo khảo sát mới",
            "en": "Create new survey"
        },
        "manage_forms": {
            "vi": "Quản lý biểu mẫu",
            "en": "Manage forms"
        },
        "answer_survey": {
            "vi": "Trả lời khảo sát",
            "en": "Answer survey"
        },
        "share_survey": {
            "vi": "Chia sẻ khảo sát",
            "en": "Share survey"
        },
        "analyze_data": {
            "vi": "Phân tích dữ liệu",
            "en": "Analyze data"
        },
        "manage_users": {
            "vi": "Quản lý người dùng",
            "en": "Manage users"
        },
        "settings": {
            "vi": "Cài đặt",
            "en": "Settings"
        },
        "language": {
            "vi": "Ngôn ngữ",
            "en": "Language"
        }
    }
    
    if key in translations and lang in translations[key]:
        return translations[key][lang]
    else:
        return key