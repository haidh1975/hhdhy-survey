import streamlit as st
from utils.auth import create_user, is_authenticated
from utils.i18n import t, get_lang, render_language_selector

st.set_page_config(
    page_title="HHD-HY — Đăng ký / Register",
    page_icon="📝",
    layout="wide",
)

render_language_selector()

# If already authenticated, redirect to main page
if is_authenticated():
    already_msg = "Bạn đã đăng nhập!" if get_lang() == "vi" else "You are already logged in!"
    st.success(already_msg)
    if st.button(t("home")):
        st.switch_page("app.py")
    st.stop()

reg_title = "📝 Đăng ký tài khoản" if get_lang() == "vi" else "📝 Register Account"
st.title(reg_title)

# Create columns for better layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    new_acc_label = "Tạo tài khoản mới" if get_lang() == "vi" else "Create a new account"
    st.markdown(f"### {new_acc_label}")

    # Registration form
    with st.form("register_form"):
        uname_help = "Tên đăng nhập phải có ít nhất 3 ký tự" if get_lang() == "vi" else "Username must be at least 3 characters"
        uname_placeholder = "Tối thiểu 3 ký tự" if get_lang() == "vi" else "Minimum 3 characters"
        username = st.text_input(
            t("username"),
            placeholder=uname_placeholder,
            help=uname_help,
        )

        email_help = "Email dùng để khôi phục mật khẩu" if get_lang() == "vi" else "Email used for password recovery"
        email = st.text_input(
            "Email",
            placeholder="example@domain.com",
            help=email_help,
        )

        pw_help = "Mật khẩu phải có ít nhất 6 ký tự" if get_lang() == "vi" else "Password must be at least 6 characters"
        pw_placeholder = "Tối thiểu 6 ký tự" if get_lang() == "vi" else "Minimum 6 characters"
        password = st.text_input(
            t("password"),
            type="password",
            placeholder=pw_placeholder,
            help=pw_help,
        )

        confirm_label = "Xác nhận mật khẩu" if get_lang() == "vi" else "Confirm Password"
        confirm_placeholder = "Nhập lại mật khẩu" if get_lang() == "vi" else "Re-enter password"
        password_confirm = st.text_input(
            confirm_label,
            type="password",
            placeholder=confirm_placeholder,
        )

        terms_label = "Tôi đồng ý với các điều khoản sử dụng và chính sách bảo mật" if get_lang() == "vi" \
                      else "I agree to the Terms of Service and Privacy Policy"
        agree_terms = st.checkbox(terms_label)

        col_register, col_login = st.columns(2)

        register_label = "Đăng ký" if get_lang() == "vi" else "Register"
        login_label = "Đã có tài khoản? Đăng nhập" if get_lang() == "vi" else "Already have an account? Login"
        with col_register:
            register_clicked = st.form_submit_button(register_label, use_container_width=True, type="primary")

        with col_login:
            login_clicked = st.form_submit_button(login_label, use_container_width=True)

    # Handle registration
    if register_clicked:
        if not all([username, email, password, password_confirm]):
            err_fill = "Vui lòng điền đầy đủ tất cả các trường" if get_lang() == "vi" else "Please fill in all fields"
            st.error(err_fill)
        elif password != password_confirm:
            err_pw = "Mật khẩu xác nhận không khớp" if get_lang() == "vi" else "Passwords do not match"
            st.error(err_pw)
        elif not agree_terms:
            err_terms = "Bạn cần đồng ý với điều khoản sử dụng" if get_lang() == "vi" else "You must agree to the terms"
            st.error(err_terms)
        else:
            success, message = create_user(username, password, email)
            if success:
                st.success(message)
                ok_msg = "Bạn có thể đăng nhập ngay bây giờ!" if get_lang() == "vi" else "You can log in now!"
                st.success(ok_msg)
                go_login = "Đi đến trang đăng nhập" if get_lang() == "vi" else "Go to login page"
                if st.button(go_login):
                    st.switch_page("pages/6_Login.py")
            else:
                st.error(message)

    # Handle login redirect
    if login_clicked:
        st.switch_page("pages/6_Login.py")

    # Terms and conditions expandable section
    terms_expander_label = "📋 Điều khoản sử dụng và Chính sách bảo mật" if get_lang() == "vi" \
                           else "📋 Terms of Service and Privacy Policy"
    with st.expander(terms_expander_label):
        if get_lang() == "vi":
            st.markdown("""
### Điều khoản sử dụng

1. **Mục đích sử dụng**: Hệ thống được thiết kế để tạo và quản lý khảo sát nghiên cứu khoa học.
2. **Trách nhiệm người dùng**: Sử dụng hệ thống có trách nhiệm, không tạo nội dung vi phạm pháp luật.
3. **Bảo mật thông tin**: Người dùng có trách nhiệm bảo mật thông tin đăng nhập cá nhân.

### Chính sách bảo mật

1. **Thu thập thông tin**: Chỉ thu thập thông tin cần thiết để vận hành hệ thống.
2. **Bảo vệ dữ liệu**: Mật khẩu được mã hóa; dữ liệu khảo sát được bảo vệ bằng phân quyền.
3. **Chia sẻ thông tin**: Thông tin cá nhân không được chia sẻ với bên thứ ba.
""")
        else:
            st.markdown("""
### Terms of Service

1. **Purpose**: This system is designed for creating and managing scientific research surveys.
2. **User responsibility**: Use the system responsibly; do not create unlawful content.
3. **Security**: Users are responsible for keeping their login credentials secure.

### Privacy Policy

1. **Data collection**: Only data necessary for system operation is collected.
2. **Data protection**: Passwords are encrypted; survey data is protected by access control.
3. **Data sharing**: Personal information is not shared with third parties.
""")

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666;'>"
    f"<p><strong>HHD-HY</strong> — {t('footer_copy')}</p>"
    f"</div>",
    unsafe_allow_html=True,
)
