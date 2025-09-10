import streamlit as st
from utils.auth import login_user, is_authenticated

st.set_page_config(
    page_title="Đăng nhập - Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực",
    page_icon="🔐",
    layout="wide",
)

# If already authenticated, redirect to main page
if is_authenticated():
    st.success("Bạn đã đăng nhập!")
    if st.button("Về trang chủ"):
        st.switch_page("app.py")
    st.stop()

st.title("🔐 Đăng nhập")

# Create columns for better layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### Đăng nhập vào hệ thống khảo sát")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập của bạn")
        password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
        
        col_login, col_register = st.columns(2)
        
        with col_login:
            login_clicked = st.form_submit_button("Đăng nhập", use_container_width=True, type="primary")
        
        with col_register:
            register_clicked = st.form_submit_button("Đăng ký tài khoản mới", use_container_width=True)
    
    # Handle login
    if login_clicked:
        if username and password:
            success, message = login_user(username, password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        else:
            st.error("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu")
    
    # Handle register redirect
    if register_clicked:
        st.switch_page("pages/7_Register.py")
    
    # Demo accounts info
    st.markdown("---")
    st.markdown("### 🔧 Tài khoản demo")
    st.info("""
    **Tài khoản quản trị viên:**
    - Tên đăng nhập: `admin`
    - Mật khẩu: `admin123`
    
    **Hoặc tạo tài khoản người dùng mới bằng cách nhấn "Đăng ký tài khoản mới"**
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp</p>
        <p>Hệ thống bảo mật cho phép quản lý khảo sát một cách an toàn</p>
    </div>
    """, 
    unsafe_allow_html=True
)