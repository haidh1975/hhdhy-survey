import streamlit as st
import json
import hashlib
import os
import datetime
from typing import Dict, Optional, Tuple

# File paths
USERS_FILE = "users.json"
SESSIONS_FILE = "sessions.json"

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> Dict:
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_users(users: Dict) -> None:
    """Save users to JSON file"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def load_sessions() -> Dict:
    """Load active sessions from JSON file"""
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_sessions(sessions: Dict) -> None:
    """Save sessions to JSON file"""
    with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

def create_user(username: str, password: str, email: str, role: str = "user") -> Tuple[bool, str]:
    """
    Create a new user account
    Returns (success, message)
    """
    users = load_users()
    
    # Check if username already exists
    if username in users:
        return False, "Tên đăng nhập đã tồn tại"
    
    # Check if email already exists
    for user_data in users.values():
        if user_data.get("email", "").lower() == email.lower():
            return False, "Email đã được sử dụng"
    
    # Validate input
    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự"
    
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
    
    if "@" not in email:
        return False, "Email không hợp lệ"
    
    # Create user
    users[username] = {
        "password": hash_password(password),
        "email": email,
        "role": role,
        "created_at": datetime.datetime.now().isoformat(),
        "last_login": None,
        "active": True
    }
    
    save_users(users)
    return True, "Tài khoản được tạo thành công"

def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Authenticate user credentials
    Returns (success, user_data, message)
    """
    users = load_users()
    
    if username not in users:
        return False, None, "Tên đăng nhập không tồn tại"
    
    user_data = users[username]
    
    if not user_data.get("active", True):
        return False, None, "Tài khoản đã bị vô hiệu hóa"
    
    if user_data["password"] != hash_password(password):
        return False, None, "Mật khẩu không chính xác"
    
    # Update last login
    user_data["last_login"] = datetime.datetime.now().isoformat()
    users[username] = user_data
    save_users(users)
    
    return True, user_data, "Đăng nhập thành công"

def login_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Login user and create session
    Returns (success, message)
    """
    success, user_data, message = authenticate_user(username, password)
    
    if success:
        # Create session
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_role = user_data["role"]
        st.session_state.user_email = user_data["email"]
        st.session_state.login_time = datetime.datetime.now().isoformat()
        
        # Save session
        sessions = load_sessions()
        sessions[username] = {
            "login_time": st.session_state.login_time,
            "user_role": user_data["role"]
        }
        save_sessions(sessions)
        
    return success, message

def logout_user() -> None:
    """Logout current user"""
    if "username" in st.session_state:
        # Remove from sessions
        sessions = load_sessions()
        if st.session_state.username in sessions:
            del sessions[st.session_state.username]
            save_sessions(sessions)
    
    # Clear session state
    for key in ["authenticated", "username", "user_role", "user_email", "login_time"]:
        if key in st.session_state:
            del st.session_state[key]

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)

def get_current_user() -> Optional[str]:
    """Get current username"""
    if is_authenticated():
        return st.session_state.get("username")
    return None

def get_user_role() -> Optional[str]:
    """Get current user role"""
    if is_authenticated():
        return st.session_state.get("user_role")
    return None

def is_admin() -> bool:
    """Check if current user is admin"""
    return get_user_role() == "admin"

def require_auth(redirect_page: str = "pages/6_Login.py") -> bool:
    """
    Require authentication - redirect to login if not authenticated
    Returns True if authenticated, False otherwise
    """
    if not is_authenticated():
        st.error("Bạn cần đăng nhập để truy cập trang này")
        if st.button("Đi đến trang đăng nhập"):
            st.switch_page(redirect_page)
        st.stop()
        return False
    return True

def require_admin() -> bool:
    """
    Require admin role - show error if not admin
    Returns True if admin, False otherwise
    """
    if not require_auth():
        return False
    
    if not is_admin():
        st.error("Bạn không có quyền truy cập trang này (chỉ dành cho quản trị viên)")
        st.stop()
        return False
    
    return True

def initialize_admin_user() -> None:
    """Initialize default admin user if no users exist"""
    users = load_users()
    
    if not users:  # No users exist, create default admin
        default_admin = {
            "password": hash_password("admin123"),
            "email": "admin@survey.app",
            "role": "admin",
            "created_at": datetime.datetime.now().isoformat(),
            "last_login": None,
            "active": True
        }
        
        users["admin"] = default_admin
        save_users(users)

def get_all_users() -> Dict:
    """Get all users (admin only)"""
    if not is_admin():
        return {}
    return load_users()

def update_user_status(username: str, active: bool) -> Tuple[bool, str]:
    """Update user active status (admin only)"""
    if not is_admin():
        return False, "Không có quyền thực hiện"
    
    users = load_users()
    if username not in users:
        return False, "Người dùng không tồn tại"
    
    if username == get_current_user():
        return False, "Không thể vô hiệu hóa tài khoản của chính mình"
    
    users[username]["active"] = active
    save_users(users)
    
    status_text = "kích hoạt" if active else "vô hiệu hóa"
    return True, f"Đã {status_text} tài khoản {username}"

def change_user_role(username: str, new_role: str) -> Tuple[bool, str]:
    """Change user role (admin only)"""
    if not is_admin():
        return False, "Không có quyền thực hiện"
    
    if new_role not in ["admin", "user"]:
        return False, "Vai trò không hợp lệ"
    
    users = load_users()
    if username not in users:
        return False, "Người dùng không tồn tại"
    
    users[username]["role"] = new_role
    save_users(users)
    
    return True, f"Đã thay đổi vai trò của {username} thành {new_role}"

def change_password(username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Change user password"""
    users = load_users()
    
    if username not in users:
        return False, "Người dùng không tồn tại"
    
    # Verify old password
    if users[username]["password"] != hash_password(old_password):
        return False, "Mật khẩu hiện tại không chính xác"
    
    # Validate new password
    if len(new_password) < 6:
        return False, "Mật khẩu mới phải có ít nhất 6 ký tự"
    
    # Update password
    users[username]["password"] = hash_password(new_password)
    save_users(users)
    
    return True, "Đã thay đổi mật khẩu thành công"