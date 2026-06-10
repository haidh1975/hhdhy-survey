import streamlit as st
from utils.auth import login_user, is_authenticated
from utils.i18n import t, render_language_selector

st.set_page_config(
    page_title="HHD-HY — Đăng nhập / Login",
    page_icon="🔐",
    layout="wide",
)

render_language_selector()

# If already authenticated, redirect to main page
if is_authenticated():
    st.success("Bạn đã đăng nhập!" if st.session_state.get("lang", "vi") == "vi" else "You are already logged in!")
    if st.button(t("home")):
        st.switch_page("app.py")
    st.stop()

st.title(t("login_title"))

# Create columns for better layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(f"### {t('login_subtitle')}")

    # Login form
    with st.form("login_form"):
        username = st.text_input(t("username"), placeholder=t("username_placeholder"))
        password = st.text_input(t("password"), type="password", placeholder=t("password_placeholder"))

        col_login, col_register = st.columns(2)

        with col_login:
            login_clicked = st.form_submit_button(t("login"), use_container_width=True, type="primary")

        with col_register:
            register_clicked = st.form_submit_button(t("register_new"), use_container_width=True)

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
            st.error(t("fill_all_fields"))

    # Handle register redirect
    if register_clicked:
        st.switch_page("pages/7_Register.py")

    # Demo accounts info
    st.markdown("---")
    st.markdown(f"### {t('demo_account')}")
    st.info(t("demo_admin_info"))

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666;'>"
    f"<p><strong>HHD-HY</strong> — {t('footer_copy')}</p>"
    f"</div>",
    unsafe_allow_html=True,
)
