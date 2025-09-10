import streamlit as st
import pandas as pd
from utils.auth import (
    require_admin, 
    get_all_users, 
    update_user_status, 
    change_user_role,
    get_current_user
)

st.set_page_config(
    page_title="Quản trị hệ thống - Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực",
    page_icon="⚙️",
    layout="wide",
)

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

# System information
st.header("Thông tin hệ thống")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cấu hình hệ thống")
    st.info("""
    **Phiên bản**: 1.0.0  
    **Hệ thống xác thực**: File-based JSON  
    **Lưu trữ dữ liệu**: Local JSON files  
    **Phân quyền**: Admin/User roles  
    """)

with col2:
    st.subheader("Bảo mật")
    st.warning("""
    **Lưu ý bảo mật**:
    - Mật khẩu được mã hóa SHA-256
    - Session được quản lý tự động
    - Cần backup định kỳ file dữ liệu
    - Khuyến nghị sử dụng HTTPS trong production
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