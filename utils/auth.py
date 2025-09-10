import streamlit as st
import json
import hashlib
import os
import datetime
from typing import Dict, Optional, Tuple
import logging
from utils.db_utils import (
    create_user_db, authenticate_user_db, get_all_users_db,
    update_user_status_db, change_user_role_db
)
from utils.database import init_database

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str, email: str, role: str = "user") -> Tuple[bool, str]:
    """
    Create a new user account using database
    Returns (success, message)
    """
    return create_user_db(username, email, password, role)

def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Authenticate user credentials using database
    Returns (success, user_data, message)
    """
    success, user_data, message = authenticate_user_db(username, password)
    return success, user_data, message

def login_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Login user and create session
    Returns (success, message)
    """
    success, user_data, message = authenticate_user(username, password)
    
    if success and user_data:
        # Create session
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_role = user_data["role"]
        st.session_state.user_email = user_data["email"]
        st.session_state.login_time = datetime.datetime.now().isoformat()
        
        logger.info(f"User {username} logged in successfully")
        
    return success, message

def logout_user() -> None:
    """Logout current user"""
    if "username" in st.session_state:
        logger.info(f"User {st.session_state.username} logged out")
    
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
    """Initialize database and ensure default admin exists"""
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def get_all_users() -> Dict:
    """Get all users from database (admin only)"""
    if not is_admin():
        return {}
    
    users_list = get_all_users_db()
    # Convert list to dict for compatibility with existing code
    return {user['username']: user for user in users_list}

def update_user_status(username: str, active: bool) -> Tuple[bool, str]:
    """Update user active status using database (admin only)"""
    if not is_admin():
        return False, "Không có quyền thực hiện"
    
    if username == get_current_user():
        return False, "Không thể vô hiệu hóa tài khoản của chính mình"
    
    return update_user_status_db(username, active)

def change_user_role(username: str, new_role: str) -> Tuple[bool, str]:
    """Change user role using database (admin only)"""
    if not is_admin():
        return False, "Không có quyền thực hiện"
    
    return change_user_role_db(username, new_role)

def change_password(username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Change user password - TODO: Implement with database"""
    # This would need to be implemented with database functions
    # For now, return not implemented
    return False, "Tính năng đổi mật khẩu chưa được triển khai với database"

# Legacy functions for backward compatibility (using JSON files as fallback)
def load_users() -> Dict:
    """Load users from JSON file (legacy fallback)"""
    if os.path.exists("users.json"):
        try:
            with open("users.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_users(users: Dict) -> None:
    """Save users to JSON file (legacy fallback)"""
    with open("users.json", 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def load_sessions() -> Dict:
    """Load active sessions from JSON file (legacy fallback)"""
    if os.path.exists("sessions.json"):
        try:
            with open("sessions.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_sessions(sessions: Dict) -> None:
    """Save sessions to JSON file (legacy fallback)"""
    with open("sessions.json", 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)