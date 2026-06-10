import streamlit as st
import pandas as pd
from utils.auth import (
    require_admin,
    get_all_users,
    update_user_status,
    change_user_role,
    get_current_user,
    change_password,
)
from utils.database import check_database_health
from utils.i18n import render_language_selector, t, get_lang

st.set_page_config(
    page_title="HHD-HY — Quản trị hệ thống / Admin",
    page_icon="⚙️",
    layout="wide",
)

render_language_selector()

# Require admin authentication
require_admin()

st.title("⚙️ Quản trị hệ thống")

# Admin dashboard
st.header("Bảng điều khiển quản trị")

# Load current user and user data
users = get_all_users()
current_user = get_current_user()

# Statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_users = len(users)
    st.metric("Tổng số người dùng", total_users)

with col2:
    active_users = sum(1 for user in users.values() if user.get("active", True))
    st.metric("Người dùng đang hoạt động", active_users)

with col3:
    admin_users = sum(1 for user in users.values() if user.get("role") == "admin")
    st.metric("Quản trị viên", admin_users)

with col4:
    inactive_users = total_users - active_users
    st.metric("Tài khoản bị khóa", inactive_users)

# User management section
st.header("Quản lý người dùng")

if users:
    # Convert users data to DataFrame for display
    user_data = []
    for username, user_info in users.items():
        user_data.append({
            "Tên đăng nhập": username,
            "Email": user_info.get("email", "N/A"),
            "Vai trò": user_info.get("role", "user"),
            "Trạng thái": "Hoạt động" if user_info.get("active", True) else "Bị khóa",
            "Ngày tạo": user_info.get("created_at", "N/A")[:10] if user_info.get("created_at") else "N/A",
            "Đăng nhập cuối": user_info.get("last_login", "Chưa từng")[:10] if user_info.get("last_login") else "Chưa từng"
        })
    
    users_df = pd.DataFrame(user_data)
    st.dataframe(users_df, use_container_width=True)
    
    # User actions
    st.subheader("Thao tác với người dùng")
    
    # Select user for actions
    usernames = [u for u in users.keys() if u != current_user]  # Exclude current admin
    
    if usernames:
        selected_user = st.selectbox(
            "Chọn người dùng để thao tác",
            options=usernames,
            format_func=lambda x: f"{x} ({users[x].get('email', 'N/A')})"
        )
        
        if selected_user:
            selected_user_info = users[selected_user]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Thay đổi trạng thái tài khoản")
                current_status = selected_user_info.get("active", True)
                new_status = st.radio(
                    f"Trạng thái tài khoản của {selected_user}",
                    options=[True, False],
                    format_func=lambda x: "Hoạt động" if x else "Bị khóa",
                    index=0 if current_status else 1
                )
                
                if st.button("Cập nhật trạng thái", key="status"):
                    if current_status != new_status:
                        success, message = update_user_status(selected_user, new_status)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.info("Trạng thái không thay đổi")
            
            with col2:
                st.markdown("### Thay đổi vai trò")
                current_role = selected_user_info.get("role", "user")
                new_role = st.radio(
                    f"Vai trò của {selected_user}",
                    options=["user", "admin"],
                    format_func=lambda x: "Người dùng thường" if x == "user" else "Quản trị viên",
                    index=0 if current_role == "user" else 1
                )
                
                if st.button("Cập nhật vai trò", key="role"):
                    if current_role != new_role:
                        success, message = change_user_role(selected_user, new_role)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.info("Vai trò không thay đổi")
    else:
        st.info("Chỉ có tài khoản của bạn trong hệ thống. Không có người dùng nào khác để quản lý.")

else:
    st.info("Không có người dùng nào trong hệ thống.")

# Đổi mật khẩu cho tài khoản admin đang đăng nhập
st.header("🔑 Đổi mật khẩu tài khoản của bạn")

with st.expander("Nhấn để đổi mật khẩu"):
    with st.form("change_password_form"):
        old_pw = st.text_input("Mật khẩu hiện tại", type="password")
        new_pw = st.text_input("Mật khẩu mới", type="password")
        confirm_pw = st.text_input("Xác nhận mật khẩu mới", type="password")
        change_btn = st.form_submit_button("Đổi mật khẩu")

    if change_btn:
        if not old_pw or not new_pw or not confirm_pw:
            st.error("Vui lòng điền đầy đủ tất cả các trường")
        elif new_pw != confirm_pw:
            st.error("Mật khẩu mới và xác nhận không khớp")
        elif len(new_pw) < 6:
            st.error("Mật khẩu mới phải có ít nhất 6 ký tự")
        else:
            ok, msg = change_password(current_user, old_pw, new_pw)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

# Thông tin hệ thống
st.header("Thông tin hệ thống")

db_health = check_database_health()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Cấu hình hệ thống")
    db_type = db_health.get("db_type", "PostgreSQL")
    db_status = db_health.get("status", "unknown")
    db_tables = db_health.get("tables_count", "?")
    status_icon = "✅" if db_status == "healthy" else "❌"
    st.info(f"""
    **Phiên bản**: 2.0.0
    **Cơ sở dữ liệu**: {db_type} {status_icon}
    **Số bảng**: {db_tables}
    **Xác thực**: Database-based (SHA-256)
    **Phân quyền**: Admin/User roles
    """)

with col2:
    st.subheader("Bảo mật")
    st.warning("""
    **Lưu ý bảo mật**:
    - Mật khẩu được mã hóa SHA-256
    - Session được quản lý qua Streamlit session_state
    - Khuyến nghị dùng PostgreSQL trong production
    - Nên bật HTTPS khi triển khai thực tế
    """)

# Quick actions
st.header("Thao tác nhanh")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("📈 Dashboard Nâng cao", use_container_width=True):
        st.switch_page("pages/9_Dashboard_Admin.py")

with col2:
    if st.button("☁️ Google Drive Backup", use_container_width=True):
        st.switch_page("pages/10_Google_Drive_Backup.py")

with col3:
    if st.button("📊 Phân tích dữ liệu", use_container_width=True):
        st.switch_page("pages/4_Data_Analysis.py")

with col4:
    if st.button("👥 Quản lý khảo sát", use_container_width=True):
        st.switch_page("pages/1_Create_Survey.py")

with col5:
    if st.button("🏠 Về trang chủ", use_container_width=True):
        st.switch_page("app.py")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p><strong>Panel Quản trị Hệ thống Khảo sát</strong></p>
        <p>Chỉ dành cho quản trị viên - Sử dụng cẩn thận các thao tác trên</p>
    </div>
    """, 
    unsafe_allow_html=True
)