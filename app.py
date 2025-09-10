import streamlit as st
import pandas as pd
import os
import json
from utils.auth import (
    initialize_admin_user, 
    is_authenticated, 
    get_current_user, 
    get_user_role, 
    logout_user,
    is_admin
)
from utils.db_utils import get_surveys_db, get_system_stats_db

# Set page configuration
st.set_page_config(
    page_title="Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize authentication system
initialize_admin_user()

# Load surveys from database instead of session state
@st.cache_data(ttl=60)  # Cache for 1 minute
def load_surveys_from_db():
    """Load surveys from database with caching"""
    surveys = get_surveys_db()
    # Convert to format compatible with existing code
    surveys_dict = {}
    for survey in surveys:
        surveys_dict[survey['uuid']] = {
            'title': survey['title'],
            'description': survey['description'],
            'questions': survey['questions'],
            'created_date': survey['created_at'][:19] if survey['created_at'] else '',
            'created_by': survey['created_by']
        }
    return surveys_dict

@st.cache_data(ttl=60)  # Cache for 1 minute  
def load_system_stats():
    """Load system statistics from database"""
    return get_system_stats_db()

# Load current surveys
surveys_data = load_surveys_from_db()
st.session_state.surveys = surveys_data

# Load system stats
stats = load_system_stats()

if 'current_survey' not in st.session_state:
    st.session_state.current_survey = None

if 'current_survey_id' not in st.session_state:
    st.session_state.current_survey_id = None

# Sidebar authentication info
with st.sidebar:
    st.markdown("### 👤 Thông tin người dùng")
    
    if is_authenticated():
        current_user = get_current_user()
        user_role = get_user_role()
        
        st.success(f"Đã đăng nhập: **{current_user}**")
        
        role_display = "Quản trị viên" if user_role == "admin" else "Người dùng"
        st.info(f"Vai trò: {role_display}")
        
        # Admin quick access
        if is_admin():
            st.markdown("### ⚙️ Quản trị viên")
            if st.button("🔧 Panel quản trị", use_container_width=True):
                st.switch_page("pages/8_Admin.py")
        
        # Logout button
        if st.button("🚪 Đăng xuất", use_container_width=True):
            logout_user()
            st.rerun()
    else:
        st.warning("Chưa đăng nhập")
        if st.button("🔐 Đăng nhập", use_container_width=True):
            st.switch_page("pages/6_Login.py")
        if st.button("📝 Đăng ký", use_container_width=True):
            st.switch_page("pages/7_Register.py")
    
    st.markdown("---")

# Main page
st.title("Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên")

# Dashboard summary
st.header("Bảng Điều Khiển")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_surveys = stats.get('surveys', {}).get('total', 0)
    st.metric(label="Tổng Số Khảo Sát", value=total_surveys)

with col2:
    total_responses = stats.get('responses', {}).get('total', 0)
    st.metric(label="Tổng Số Phản Hồi", value=total_responses)

with col3:
    avg_responses = total_responses / total_surveys if total_surveys > 0 else 0
    st.metric(label="Phản Hồi Trung Bình", value=f"{avg_responses:.1f}")

with col4:
    # Tính tổng số câu hỏi trong tất cả các khảo sát
    total_questions = sum(len(survey["questions"]) for survey in st.session_state.surveys.values())
    st.metric(label="Tổng Số Câu Hỏi", value=total_questions)

# Recent surveys section
st.subheader("Khảo Sát Hiện Có")

if st.session_state.surveys:
    # Convert surveys to DataFrame for display using database data
    survey_data = []
    db_surveys = get_surveys_db()
    
    for survey in db_surveys:
        survey_data.append({
            "ID Khảo Sát": survey['uuid'][:8] + "...",  # Hiển thị rút gọn ID
            "Tiêu Đề": survey["title"],
            "Ngày Tạo": survey.get("created_at", "N/A")[:10] if survey.get("created_at") else "N/A",
            "Số Câu Hỏi": len(survey["questions"]),
            "Số Phản Hồi": survey.get("response_count", 0)
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
    selected_survey = None
    for survey_id, survey in st.session_state.surveys.items():
        if survey["title"] == selected_survey_title:
            selected_survey_id = survey_id
            selected_survey = survey
            break
    
    if selected_survey_id and selected_survey:
        st.write(f"**Tiêu đề:** {selected_survey['title']}")
        st.write(f"**Mô tả:** {selected_survey.get('description', 'Không có mô tả')}")
        st.write(f"**Ngày tạo:** {selected_survey.get('created_date', 'N/A')}")
        st.write(f"**Số câu hỏi:** {len(selected_survey['questions'])}")
        # Get response count from database for this survey
        from utils.db_utils import get_responses_db
        response_count = len(get_responses_db(selected_survey_id))
        st.write(f"**Số phản hồi:** {response_count}")
        
        # Hiển thị một số câu hỏi mẫu từ khảo sát
        st.write("**Các câu hỏi mẫu:**")
        sample_questions = selected_survey['questions'][:5]  # Lấy 5 câu hỏi đầu tiên
        for i, question in enumerate(sample_questions):
            st.write(f"{i+1}. {question['question_text']} ({question['type']})")
        
        if len(selected_survey['questions']) > 5:
            st.write(f"... và {len(selected_survey['questions']) - 5} câu hỏi khác")
else:
    st.info("Chưa có khảo sát nào được tạo. Vào trang 'Create Survey' để bắt đầu.")

# Quick action buttons
st.subheader("Các Tác Vụ Nhanh")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("➕ Tạo Khảo Sát Mới", use_container_width=True):
        st.switch_page("pages/1_Create_Survey.py")

with col2:
    if st.button("📝 Trả Lời Khảo Sát", use_container_width=True):
        st.switch_page("pages/5_Answer_Survey.py")

with col3:
    if st.button("🔗 Chia Sẻ Khảo Sát", use_container_width=True):
        st.switch_page("pages/2_Distribute_Survey.py")

with col4:
    if st.button("📊 Phân Tích Dữ Liệu", use_container_width=True):
        st.switch_page("pages/4_Data_Analysis.py")

# Thông tin thêm về khảo sát động lực làm việc
st.subheader("📌 Giới Thiệu Về Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên")
st.markdown("""
Ứng dụng này hiện đang chứa dữ liệu khảo sát về các yếu tố ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên, bao gồm:

- **Vốn xã hội trong doanh nghiệp**: Đánh giá mức độ tin tưởng, kết nối và hợp tác giữa các thành viên trong doanh nghiệp
- **Vốn nhân lực của doanh nghiệp**: Đánh giá về kỹ năng, kiến thức, kinh nghiệm và khả năng đổi mới của nhân lực
- **Phát triển bền vững của doanh nghiệp**: Đánh giá về khía cạnh kinh tế, xã hội và môi trường
- **Các nhân tố ảnh hưởng**: Xác định các yếu tố bên trong và bên ngoài ảnh hưởng đến sự phát triển
- **Thông tin doanh nghiệp**: Thu thập dữ liệu về quy mô, lĩnh vực hoạt động, thời gian thành lập

Dữ liệu này sẽ được sử dụng để phân tích và đưa ra các đề xuất cho việc phát triển bền vững của doanh nghiệp tại tỉnh Hưng Yên.
""")

# Getting started guide
st.subheader("Hướng Dẫn Sử Dụng")
st.markdown("""
Để sử dụng ứng dụng hiệu quả:

1. **Tạo Khảo Sát**: Vào trang 'Create Survey' để thiết kế khảo sát với nhiều loại câu hỏi khác nhau.
2. **Chia Sẻ Khảo Sát**: Chia sẻ khảo sát thông qua đường link hoặc mã QR từ trang 'Distribute Survey'.
3. **Trả Lời Khảo Sát**: Điền khảo sát hoặc chia sẻ cho người khác để thu thập phản hồi.
4. **Xem Phản Hồi**: Kiểm tra tất cả phản hồi nhận được cho khảo sát của bạn tại trang 'View Responses'.
5. **Phân Tích Dữ Liệu**: Vào trang 'Data Analysis' để trực quan hóa và phân tích dữ liệu khảo sát.

Sử dụng menu điều hướng bên trái để truy cập các tính năng này.
""")

# Footer
st.markdown("---")
st.markdown("📊 Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên - Công cụ tạo biểu mẫu, thu thập dữ liệu và phân tích thống kê")
