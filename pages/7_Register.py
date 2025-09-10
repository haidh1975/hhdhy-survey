import streamlit as st
from utils.auth import create_user, is_authenticated

st.set_page_config(
    page_title="Đăng ký - Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực",
    page_icon="📝",
    layout="wide",
)

# If already authenticated, redirect to main page
if is_authenticated():
    st.success("Bạn đã đăng nhập!")
    if st.button("Về trang chủ"):
        st.switch_page("app.py")
    st.stop()

st.title("📝 Đăng ký tài khoản")

# Create columns for better layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### Tạo tài khoản mới")
    
    # Registration form
    with st.form("register_form"):
        username = st.text_input(
            "Tên đăng nhập", 
            placeholder="Tối thiểu 3 ký tự", 
            help="Tên đăng nhập phải có ít nhất 3 ký tự và không chứa ký tự đặc biệt"
        )
        
        email = st.text_input(
            "Email", 
            placeholder="example@domain.com",
            help="Email sẽ được sử dụng để khôi phục mật khẩu và nhận thông báo"
        )
        
        password = st.text_input(
            "Mật khẩu", 
            type="password", 
            placeholder="Tối thiểu 6 ký tự",
            help="Mật khẩu phải có ít nhất 6 ký tự"
        )
        
        password_confirm = st.text_input(
            "Xác nhận mật khẩu", 
            type="password", 
            placeholder="Nhập lại mật khẩu"
        )
        
        # Terms and conditions
        agree_terms = st.checkbox(
            "Tôi đồng ý với các điều khoản sử dụng và chính sách bảo mật",
            help="Bạn cần đồng ý với điều khoản để tạo tài khoản"
        )
        
        col_register, col_login = st.columns(2)
        
        with col_register:
            register_clicked = st.form_submit_button("Đăng ký", use_container_width=True, type="primary")
        
        with col_login:
            login_clicked = st.form_submit_button("Đã có tài khoản? Đăng nhập", use_container_width=True)
    
    # Handle registration
    if register_clicked:
        # Validate form
        if not all([username, email, password, password_confirm]):
            st.error("Vui lòng điền đầy đủ tất cả các trường")
        elif password != password_confirm:
            st.error("Mật khẩu xác nhận không khớp")
        elif not agree_terms:
            st.error("Bạn cần đồng ý với điều khoản sử dụng")
        else:
            # Create user
            success, message = create_user(username, password, email)
            if success:
                st.success(message)
                st.success("Bạn có thể đăng nhập ngay bây giờ!")
                if st.button("Đi đến trang đăng nhập"):
                    st.switch_page("pages/6_Login.py")
            else:
                st.error(message)
    
    # Handle login redirect
    if login_clicked:
        st.switch_page("pages/6_Login.py")
    
    # Terms and conditions expandable section
    with st.expander("📋 Điều khoản sử dụng và Chính sách bảo mật"):
        st.markdown("""
        ### Điều khoản sử dụng
        
        1. **Mục đích sử dụng**: Hệ thống này được thiết kế để tạo và quản lý khảo sát nghiên cứu khoa học.
        
        2. **Trách nhiệm người dùng**:
           - Sử dụng hệ thống một cách có trách nhiệm
           - Không tạo nội dung có hại, bất hợp pháp hoặc vi phạm đạo đức
           - Bảo mật thông tin đăng nhập cá nhân
        
        3. **Quyền hạn**: 
           - Người dùng thường có thể tạo và quản lý khảo sát của mình
           - Quản trị viên có quyền giám sát và quản lý toàn bộ hệ thống
        
        ### Chính sách bảo mật
        
        1. **Thu thập thông tin**: Chúng tôi chỉ thu thập thông tin cần thiết để vận hành hệ thống.
        
        2. **Bảo vệ dữ liệu**: 
           - Mật khẩu được mã hóa trước khi lưu trữ
           - Dữ liệu khảo sát được bảo vệ bằng hệ thống phân quyền
        
        3. **Chia sẻ thông tin**: Thông tin cá nhân không được chia sẻ với bên thứ ba.
        
        4. **Quyền của người dùng**: Bạn có quyền yêu cầu xóa tài khoản và dữ liệu cá nhân.
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp</p>
        <p>Đăng ký để tham gia vào hệ thống khảo sát an toàn và chuyên nghiệp</p>
    </div>
    """, 
    unsafe_allow_html=True
)