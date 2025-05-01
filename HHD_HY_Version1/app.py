import streamlit as st
import pandas as pd
import os
import json
from PIL import Image
import base64
from utils.auth import init_auth, require_login, show_login_form, logout, get_translation, switch_language

# Khởi tạo hệ thống xác thực
init_auth()

# Set page configuration
st.set_page_config(
    page_title="Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS để làm đẹp giao diện
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(45deg, #4a89dc, #8e44ad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    .dashboard-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    
    .dashboard-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #4a89dc;
    }
    
    .action-button {
        background-color: #4a89dc;
        color: white;
        border-radius: 20px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .action-button:hover {
        background-color: #3a6bac;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    .stButton button {
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Logo và thanh ngôn ngữ ở phía trên
col1, col2, col3 = st.columns([1, 8, 1])

with col1:
    # Tạo logo đơn giản khi chưa có logo thực
    logo_html = """
    <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="80" height="80" rx="20" fill="#4a89dc"/>
        <path d="M20 40 L40 20 L60 40 L40 60 Z" fill="white"/>
        <circle cx="40" cy="40" r="10" fill="#8e44ad"/>
        <text x="40" y="43" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="10" fill="white">HHD</text>
    </svg>
    """
    st.markdown(logo_html, unsafe_allow_html=True)

with col3:
    # Chuyển đổi ngôn ngữ
    if st.button("🌐 " + st.session_state.language.upper()):
        switch_language()
        st.rerun()

# Sidebar cho điều hướng và đăng nhập
with st.sidebar:
    st.markdown(f"## {get_translation('app_title')}")
    
    # Hiển thị thông tin người dùng và nút đăng xuất nếu đã đăng nhập
    if st.session_state.user:
        st.success(f"{get_translation('welcome')}, {st.session_state.user['name']}!")
        st.write(f"Role: {st.session_state.user['role'].capitalize()}")
        if st.button(get_translation('logout')):
            logout()
            st.rerun()
    else:
        # Hiển thị form đăng nhập nếu chưa đăng nhập
        show_login_form()
    
    st.divider()
    
    # Menu điều hướng
    st.markdown("### 📌 Menu")
    
    if st.button(f"🏠 {get_translation('dashboard')}", key="nav_dashboard"):
        st.session_state.page = "dashboard"
    
    if st.button(f"➕ {get_translation('create_survey')}", key="nav_create"):
        st.switch_page("pages/1_Create_Survey.py")
        
    if st.button(f"📋 {get_translation('manage_forms')}", key="nav_answer"):
        st.switch_page("pages/5_Answer_Survey.py")
        
    if st.button(f"🔗 {get_translation('share_survey')}", key="nav_share"):
        st.switch_page("pages/2_Distribute_Survey.py")
        
    if st.button(f"📊 {get_translation('analyze_data')}", key="nav_analyze"):
        st.switch_page("pages/4_Data_Analysis.py")

    if st.session_state.user and st.session_state.user["role"] == "admin":
        if st.button(f"👥 {get_translation('manage_users')}", key="nav_users"):
            st.switch_page("pages/6_Manage_Users.py")
        
    st.divider()
    
    # Cài đặt và thông tin phụ
    st.markdown("### ⚙️ " + get_translation('settings'))
    
    st.selectbox(
        get_translation('language'),
        options=[
            "Tiếng Việt (Vietnamese)", 
            "English"
        ],
        index=0 if st.session_state.language == "vi" else 1,
        key="language_select"
    )
    
    if st.session_state.language_select == "English" and st.session_state.language == "vi":
        st.session_state.language = "en"
        st.rerun()
    elif st.session_state.language_select == "Tiếng Việt (Vietnamese)" and st.session_state.language == "en":
        st.session_state.language = "vi"
        st.rerun()

# Initialize session state variables if they don't exist
if 'surveys' not in st.session_state:
    # Check if there are saved surveys
    if os.path.exists('surveys.json'):
        with open('surveys.json', 'r') as f:
            st.session_state.surveys = json.load(f)
    else:
        st.session_state.surveys = {}

if 'responses' not in st.session_state:
    # Check if there are saved responses
    if os.path.exists('responses.json'):
        with open('responses.json', 'r') as f:
            st.session_state.responses = json.load(f)
    else:
        st.session_state.responses = {}

if 'current_survey' not in st.session_state:
    st.session_state.current_survey = None

if 'current_survey_id' not in st.session_state:
    st.session_state.current_survey_id = None

# Main page
st.markdown(f"<h1 class='main-header'>{get_translation('app_title')}</h1>", unsafe_allow_html=True)

# Dashboard summary
st.markdown(f"## {get_translation('dashboard')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-label'>{get_translation('total_surveys')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{len(st.session_state.surveys)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    total_responses = sum(len(responses) for responses in st.session_state.responses.values())
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-label'>{get_translation('total_responses')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{total_responses}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    avg_responses = total_responses / len(st.session_state.surveys) if st.session_state.surveys else 0
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-label'>{get_translation('average_responses')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{avg_responses:.1f}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    # Tính tổng số câu hỏi trong tất cả các khảo sát
    total_questions = sum(len(survey["questions"]) for survey in st.session_state.surveys.values())
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-label'>{get_translation('total_questions')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{total_questions}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Recent surveys section
st.markdown(f"### {get_translation('existing_surveys')}")

if st.session_state.surveys:
    # Convert surveys to DataFrame for display
    survey_data = []
    for survey_id, survey in st.session_state.surveys.items():
        response_count = len(st.session_state.responses.get(survey_id, []))
        survey_data.append({
            "ID": survey_id[:8] + "...",
            "Tiêu đề": survey["title"],
            "Ngày tạo": survey.get("created_date", "N/A"),
            "Số câu hỏi": len(survey["questions"]),
            "Số phản hồi": response_count
        })
    
    survey_df = pd.DataFrame(survey_data)
    st.dataframe(survey_df, use_container_width=True)
    
    # Hiển thị thông tin chi tiết về khảo sát
    st.subheader("Thông Tin Chi Tiết Khảo Sát")
    
    # Chọn một khảo sát để xem chi tiết
    selected_survey_title = st.selectbox(
        "Chọn khảo sát:",
        options=[survey["title"] for survey in st.session_state.surveys.values()]
    )
    
    # Tìm ID khảo sát từ tiêu đề
    selected_survey_id = None
    for survey_id, survey in st.session_state.surveys.items():
        if survey["title"] == selected_survey_title:
            selected_survey_id = survey_id
            selected_survey = survey
            break
    
    if selected_survey_id:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
            st.write(f"**Tiêu đề:** {selected_survey['title']}")
            st.write(f"**Mô tả:** {selected_survey.get('description', 'Không có mô tả')}")
            st.write(f"**Ngày tạo:** {selected_survey.get('created_date', 'N/A')}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
            st.write(f"**Số câu hỏi:** {len(selected_survey['questions'])}")
            st.write(f"**Số phản hồi:** {len(st.session_state.responses.get(selected_survey_id, []))}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Hiển thị một số câu hỏi mẫu từ khảo sát
        st.write("**Các câu hỏi mẫu:**")
        sample_questions = selected_survey['questions'][:5]  # Lấy 5 câu hỏi đầu tiên
        for i, question in enumerate(sample_questions):
            st.markdown(f"{i+1}. {question['question_text']} ({question['type']})")
        
        if len(selected_survey['questions']) > 5:
            st.write(f"... và {len(selected_survey['questions']) - 5} câu hỏi khác")
else:
    st.info("Chưa có khảo sát nào được tạo. Vào trang 'Create Survey' để bắt đầu.")

# Quick action buttons
st.subheader("Các Tác Vụ Nhanh")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    if st.button("➕ Tạo Khảo Sát Mới", use_container_width=True):
        st.switch_page("pages/1_Create_Survey.py")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    if st.button("📋 Quản lý biểu mẫu", use_container_width=True):
        st.switch_page("pages/5_Answer_Survey.py")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    if st.button("🔗 Chia Sẻ Khảo Sát", use_container_width=True):
        st.switch_page("pages/2_Distribute_Survey.py")
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
    if st.button("📊 Phân Tích Dữ Liệu", use_container_width=True):
        st.switch_page("pages/4_Data_Analysis.py")
    st.markdown("</div>", unsafe_allow_html=True)

# Thông tin thêm về khảo sát động lực làm việc
st.subheader("📌 Giới Thiệu Về Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên")
st.markdown("""
<div class='dashboard-card'>
Ứng dụng Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên là công cụ mạnh mẽ được thiết kế cho:

- **Khảo sát doanh nghiệp**: Đánh giá vốn xã hội và vốn nhân lực trong doanh nghiệp tại Hưng Yên
- **Nghiên cứu học thuật**: Thu thập dữ liệu có cấu trúc cho nghiên cứu về phát triển bền vững
- **Phân tích nhân tố**: Xác định các yếu tố ảnh hưởng đến sự phát triển của doanh nghiệp

Với các tính năng ưu việt:
- Hỗ trợ song ngữ Tiếng Việt/Tiếng Anh
- Đa dạng loại câu hỏi (đơn lựa chọn, đa lựa chọn, thang đo Likert)
- Phân quyền quản trị để nhiều người cùng quản lý
- Giới hạn mỗi email chỉ trả lời 1 lần
- Phân tích dữ liệu và biểu đồ trực quan
</div>
""", unsafe_allow_html=True)

# Chỉ hiển thị phần hướng dẫn sử dụng nếu người dùng chưa đăng nhập
if not st.session_state.user:
    # Getting started guide
    st.subheader("Hướng Dẫn Sử Dụng")
    st.markdown("""
    <div class='dashboard-card'>
    Để sử dụng ứng dụng Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên:
    
    1. **Đăng nhập**: Đăng nhập hoặc đăng ký tài khoản mới ở sidebar bên trái
    2. **Tạo Khảo Sát**: Vào trang 'Create Survey' để thiết kế khảo sát tùy chỉnh
    3. **Chia Sẻ Khảo Sát**: Gửi link khảo sát hoặc QR code cho đối tượng cần khảo sát
    4. **Quản lý Phản Hồi**: Xem và xuất dữ liệu phản hồi đã thu thập được
    5. **Phân Tích Dữ Liệu**: Tạo các biểu đồ và báo cáo thống kê từ dữ liệu
    
    Để được hỗ trợ thêm, vui lòng liên hệ admin@hhd.one
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<div class='footer'>📊 Khảo sát về động lực làm việc của nhân viên - Công cụ tạo biểu mẫu, thu thập dữ liệu và phân tích thống kê</div>", unsafe_allow_html=True)