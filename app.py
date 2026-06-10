import streamlit as st
import pandas as pd
import os
import json
import plotly.graph_objects as go
import plotly.express as px
from utils.auth import (
    initialize_admin_user,
    is_authenticated,
    get_current_user,
    get_user_role,
    logout_user,
    is_admin
)
from utils.db_utils import get_surveys_db, get_system_stats_db
from utils.ui_components import apply_custom_css, add_footer
from utils.i18n import t, get_lang, render_language_selector

# Set page configuration
st.set_page_config(
    page_title="HHD-HY — Bản quyền thuộc về Đỗ Hữu Hải",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize authentication system
initialize_admin_user()

# Apply custom CSS styling
apply_custom_css()

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
    st.markdown(f"### 👤 {t('user_info')}")

    if is_authenticated():
        current_user = get_current_user()
        user_role = get_user_role()

        st.success(f"{t('logged_in_as')} **{current_user}**")

        role_display = t("role_admin") if user_role == "admin" else t("role_user")
        st.info(f"{t('role')} {role_display}")

        # Admin quick access
        if is_admin():
            st.markdown(f"### ⚙️ {t('role_admin')}")
            if st.button(t("admin_panel_short"), use_container_width=True):
                st.switch_page("pages/8_Admin.py")

        # Logout button
        if st.button(f"🚪 {t('logout')}", use_container_width=True):
            logout_user()
            st.rerun()
    else:
        st.warning(t("not_logged_in"))
        if st.button(f"🔐 {t('login')}", use_container_width=True):
            st.switch_page("pages/6_Login.py")
        if st.button(f"📝 {t('register')}", use_container_width=True):
            st.switch_page("pages/7_Register.py")

    # Language selector
    render_language_selector()

# Main page
st.title(f"📊 {t('app_name')} — {t('app_subtitle')}")

# Dashboard summary
st.header(t("dashboard"))

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_surveys = stats.get('surveys', {}).get('total', 0)
    st.metric(label=t("total_surveys"), value=total_surveys)

with col2:
    total_responses = stats.get('responses', {}).get('total', 0)
    st.metric(label=t("total_responses"), value=total_responses)

with col3:
    avg_responses = total_responses / total_surveys if total_surveys > 0 else 0
    st.metric(label=t("avg_responses"), value=f"{avg_responses:.1f}")

with col4:
    total_questions = sum(len(survey["questions"]) for survey in st.session_state.surveys.values())
    st.metric(label=t("total_questions"), value=total_questions)

# ── Response trend sparkline ─────────────────────────────────────────────────
if stats.get('surveys', {}).get('total', 0) > 0:
    db_surveys_all = get_surveys_db()
    if db_surveys_all:
        _trend_title = "📈 Phản hồi theo từng khảo sát" if get_lang() == "vi" else "📈 Responses per Survey"
        st.subheader(_trend_title)
        survey_resp_data = [
            {"title": s["title"][:28] + ("…" if len(s["title"]) > 28 else ""),
             "responses": s.get("response_count", 0)}
            for s in db_surveys_all
        ]
        df_sparkline = pd.DataFrame(survey_resp_data)
        if not df_sparkline.empty and df_sparkline["responses"].sum() > 0:
            fig_spark = go.Figure(go.Bar(
                x=df_sparkline["title"],
                y=df_sparkline["responses"],
                marker_color="#0066cc",
                text=df_sparkline["responses"],
                textposition="outside",
            ))
            fig_spark.update_layout(
                xaxis_tickangle=-30,
                yaxis_title="",
                height=260,
                margin=dict(t=10, b=70, l=30, r=10),
                xaxis_title="",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_spark, use_container_width=True)

st.markdown("---")

# Recent surveys section
st.subheader(t("available_surveys"))

if st.session_state.surveys:
    # Convert surveys to DataFrame for display using database data
    survey_data = []
    db_surveys = get_surveys_db()

    for survey in db_surveys:
        survey_data.append({
            t("survey_id"): survey['uuid'][:8] + "...",
            t("survey_title_short"): survey["title"],
            t("created_date"): survey.get("created_at", "N/A")[:10] if survey.get("created_at") else "N/A",
            t("num_questions"): len(survey["questions"]),
            t("num_responses"): survey.get("response_count", 0)
        })

    survey_df = pd.DataFrame(survey_data)
    st.dataframe(survey_df, use_container_width=True)

    # Hiển thị thông tin chi tiết về khảo sát
    st.subheader(t("survey_detail"))

    # Chọn một khảo sát để xem chi tiết
    selected_survey_title = st.selectbox(
        t("select_survey"),
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
        st.write(f"**{t('survey_title')}:** {selected_survey['title']}")
        st.write(f"**{t('survey_description')}:** {selected_survey.get('description', 'Không có mô tả')}")
        st.write(f"**{t('created_date')}:** {selected_survey.get('created_date', 'N/A')}")
        st.write(f"**{t('num_questions')}:** {len(selected_survey['questions'])}")
        from utils.db_utils import get_responses_db
        response_count = len(get_responses_db(selected_survey_id))
        st.write(f"**{t('num_responses')}:** {response_count}")

        _sample_label = "Câu hỏi mẫu" if get_lang() == "vi" else "Sample questions"
        st.write(f"**{_sample_label}:**")
        sample_questions = selected_survey['questions'][:5]
        for i, question in enumerate(sample_questions):
            st.write(f"{i+1}. {question['question_text']} ({question['type']})")

        if len(selected_survey['questions']) > 5:
            _more = f"... và {len(selected_survey['questions']) - 5} câu hỏi khác" if get_lang() == "vi" \
                    else f"... and {len(selected_survey['questions']) - 5} more questions"
            st.write(_more)
else:
    st.info(t("no_surveys_yet"))

# Quick action buttons
st.subheader(t("quick_actions"))
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button(t("create_new_survey"), use_container_width=True):
        st.switch_page("pages/1_Create_Survey.py")

with col2:
    if st.button(t("answer_survey"), use_container_width=True):
        st.switch_page("pages/5_Answer_Survey.py")

with col3:
    if st.button(t("share_survey"), use_container_width=True):
        st.switch_page("pages/2_Distribute_Survey.py")

with col4:
    if st.button(t("data_analysis"), use_container_width=True):
        st.switch_page("pages/4_Data_Analysis.py")

# About section
st.subheader(f"📌 {t('app_title_full')}")
if get_lang() == "vi":
    st.markdown("""
Ứng dụng này thu thập và phân tích dữ liệu khảo sát về các yếu tố ảnh hưởng đến phát triển bền vững, bao gồm:

- **Vốn xã hội trong doanh nghiệp**: Mức độ tin tưởng, kết nối và hợp tác nội bộ
- **Vốn nhân lực**: Kỹ năng, kiến thức, kinh nghiệm và khả năng đổi mới
- **Phát triển bền vững**: Các khía cạnh kinh tế, xã hội và môi trường
- **Các nhân tố ảnh hưởng**: Yếu tố bên trong và bên ngoài doanh nghiệp
- **Thông tin doanh nghiệp**: Quy mô, lĩnh vực, thời gian thành lập
""")
else:
    st.markdown("""
This application collects and analyzes survey data on factors affecting sustainable business development, including:

- **Social Capital**: Trust, connectivity, and internal cooperation levels
- **Human Capital**: Skills, knowledge, experience, and innovation capacity
- **Sustainable Development**: Economic, social, and environmental dimensions
- **Influencing Factors**: Internal and external business factors
- **Business Information**: Scale, sector, and establishment period
""")

# Getting started guide
st.subheader(t("getting_started"))
if get_lang() == "vi":
    st.markdown("""
1. **Tạo Khảo Sát**: Thiết kế khảo sát với nhiều loại câu hỏi khác nhau.
2. **Chia Sẻ Khảo Sát**: Chia sẻ qua đường link hoặc mã QR.
3. **Trả Lời Khảo Sát**: Điền khảo sát để thu thập phản hồi.
4. **Xem Phản Hồi**: Kiểm tra tất cả phản hồi nhận được.
5. **Phân Tích Dữ Liệu**: Trực quan hóa và phân tích dữ liệu thống kê.

Sử dụng menu điều hướng bên trái để truy cập các tính năng này.
""")
else:
    st.markdown("""
1. **Create Survey**: Design surveys with various question types.
2. **Share Survey**: Share via link or QR code.
3. **Answer Survey**: Fill in the survey to collect responses.
4. **View Responses**: Check all responses received.
5. **Data Analysis**: Visualize and statistically analyze data.

Use the left navigation menu to access these features.
""")

# Footer
st.markdown("---")
st.markdown(f"📊 **{t('footer_system')}** — {t('footer_copy')}")
