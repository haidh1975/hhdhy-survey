"""
Hệ thống đa ngôn ngữ (i18n) cho ứng dụng HHD-HY
Hỗ trợ: Tiếng Việt (vi) và Tiếng Anh (en)
"""
import streamlit as st

# ─── Bộ từ điển ────────────────────────────────────────────────────────────────
TRANSLATIONS: dict = {
    # ── Chung / General ──────────────────────────────────────────────────────
    "app_name": {
        "vi": "HHD-HY",
        "en": "HHD-HY",
    },
    "app_subtitle": {
        "vi": "Khảo sát Vốn xã hội & Vốn nhân lực — Phát triển bền vững doanh nghiệp Hưng Yên",
        "en": "Social & Human Capital Survey — Sustainable Business Development in Hung Yen",
    },
    "app_title_full": {
        "vi": "Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên",
        "en": "Survey on the Impact of Social Capital and Human Capital on Sustainable Business Development in Hung Yen Province",
    },
    "copyright": {
        "vi": "© Bản quyền thuộc về Đỗ Hữu Hải — HHD-HY",
        "en": "© Copyright by Đỗ Hữu Hải — HHD-HY",
    },
    "version": {
        "vi": "Phiên bản 2.0",
        "en": "Version 2.0",
    },
    "language": {
        "vi": "Ngôn ngữ",
        "en": "Language",
    },

    # ── Xác thực / Auth ───────────────────────────────────────────────────────
    "user_info": {
        "vi": "Thông tin người dùng",
        "en": "User Information",
    },
    "logged_in_as": {
        "vi": "Đã đăng nhập:",
        "en": "Logged in as:",
    },
    "role": {
        "vi": "Vai trò:",
        "en": "Role:",
    },
    "role_admin": {
        "vi": "Quản trị viên",
        "en": "Administrator",
    },
    "role_user": {
        "vi": "Người dùng",
        "en": "User",
    },
    "not_logged_in": {
        "vi": "Chưa đăng nhập",
        "en": "Not logged in",
    },
    "login": {
        "vi": "Đăng nhập",
        "en": "Login",
    },
    "logout": {
        "vi": "Đăng xuất",
        "en": "Logout",
    },
    "register": {
        "vi": "Đăng ký",
        "en": "Register",
    },
    "login_title": {
        "vi": "🔐 Đăng nhập",
        "en": "🔐 Login",
    },
    "login_subtitle": {
        "vi": "Đăng nhập vào hệ thống khảo sát",
        "en": "Sign in to the survey system",
    },
    "username": {
        "vi": "Tên đăng nhập",
        "en": "Username",
    },
    "username_placeholder": {
        "vi": "Nhập tên đăng nhập của bạn",
        "en": "Enter your username",
    },
    "password": {
        "vi": "Mật khẩu",
        "en": "Password",
    },
    "password_placeholder": {
        "vi": "Nhập mật khẩu",
        "en": "Enter your password",
    },
    "register_new": {
        "vi": "Đăng ký tài khoản mới",
        "en": "Create new account",
    },
    "demo_account": {
        "vi": "🔧 Tài khoản demo",
        "en": "🔧 Demo account",
    },
    "demo_admin_info": {
        "vi": "**Tài khoản quản trị viên:**\n- Tên đăng nhập: `admin`\n- Mật khẩu: `admin123`",
        "en": "**Admin account:**\n- Username: `admin`\n- Password: `admin123`",
    },
    "login_required": {
        "vi": "Bạn cần đăng nhập để truy cập trang này",
        "en": "You need to log in to access this page",
    },
    "go_to_login": {
        "vi": "Đi đến trang đăng nhập",
        "en": "Go to login page",
    },
    "admin_required": {
        "vi": "Bạn không có quyền truy cập trang này (chỉ dành cho quản trị viên)",
        "en": "You don't have permission to access this page (admin only)",
    },
    "fill_all_fields": {
        "vi": "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu",
        "en": "Please enter both username and password",
    },

    # ── Dashboard / Trang chủ ─────────────────────────────────────────────────
    "dashboard": {
        "vi": "Bảng Điều Khiển",
        "en": "Dashboard",
    },
    "total_surveys": {
        "vi": "Tổng Số Khảo Sát",
        "en": "Total Surveys",
    },
    "total_responses": {
        "vi": "Tổng Số Phản Hồi",
        "en": "Total Responses",
    },
    "avg_responses": {
        "vi": "Phản Hồi Trung Bình",
        "en": "Avg. Responses",
    },
    "total_questions": {
        "vi": "Tổng Số Câu Hỏi",
        "en": "Total Questions",
    },
    "available_surveys": {
        "vi": "Khảo Sát Hiện Có",
        "en": "Available Surveys",
    },
    "survey_detail": {
        "vi": "Thông Tin Chi Tiết Khảo Sát",
        "en": "Survey Details",
    },
    "select_survey": {
        "vi": "Chọn khảo sát:",
        "en": "Select survey:",
    },
    "quick_actions": {
        "vi": "Các Tác Vụ Nhanh",
        "en": "Quick Actions",
    },
    "create_new_survey": {
        "vi": "➕ Tạo Khảo Sát Mới",
        "en": "➕ Create New Survey",
    },
    "answer_survey": {
        "vi": "📝 Trả Lời Khảo Sát",
        "en": "📝 Answer Survey",
    },
    "share_survey": {
        "vi": "🔗 Chia Sẻ Khảo Sát",
        "en": "🔗 Share Survey",
    },
    "data_analysis": {
        "vi": "📊 Phân Tích Dữ Liệu",
        "en": "📊 Data Analysis",
    },
    "no_surveys_yet": {
        "vi": "Chưa có khảo sát nào được tạo. Vào trang 'Create Survey' để bắt đầu.",
        "en": "No surveys created yet. Go to 'Create Survey' to get started.",
    },
    "getting_started": {
        "vi": "Hướng Dẫn Sử Dụng",
        "en": "Getting Started",
    },

    # ── Khảo sát / Survey ─────────────────────────────────────────────────────
    "survey_id": {
        "vi": "ID Khảo Sát",
        "en": "Survey ID",
    },
    "survey_title": {
        "vi": "Tiêu đề khảo sát",
        "en": "Survey title",
    },
    "survey_title_short": {
        "vi": "Tiêu Đề",
        "en": "Title",
    },
    "survey_description": {
        "vi": "Mô tả khảo sát",
        "en": "Survey description",
    },
    "created_date": {
        "vi": "Ngày Tạo",
        "en": "Created Date",
    },
    "num_questions": {
        "vi": "Số Câu Hỏi",
        "en": "Questions",
    },
    "num_responses": {
        "vi": "Số Phản Hồi",
        "en": "Responses",
    },
    "save_survey": {
        "vi": "💾 Lưu khảo sát",
        "en": "💾 Save Survey",
    },
    "create_survey_page": {
        "vi": "Tạo Khảo Sát",
        "en": "Create Survey",
    },
    "manage_surveys": {
        "vi": "Quản lý khảo sát",
        "en": "Manage Surveys",
    },
    "edit_existing": {
        "vi": "Chỉnh sửa khảo sát có sẵn",
        "en": "Edit existing survey",
    },
    "load_selected": {
        "vi": "📂 Tải khảo sát đã chọn",
        "en": "📂 Load Selected Survey",
    },
    "survey_info": {
        "vi": "Thông tin khảo sát",
        "en": "Survey Information",
    },
    "add_questions": {
        "vi": "Thêm câu hỏi",
        "en": "Add Questions",
    },
    "question_type": {
        "vi": "Loại câu hỏi",
        "en": "Question Type",
    },
    "add_question_btn": {
        "vi": "➕ Thêm câu hỏi",
        "en": "➕ Add Question",
    },
    "edit_question": {
        "vi": "Chỉnh sửa câu hỏi",
        "en": "Edit Question",
    },
    "question_text": {
        "vi": "Nội dung câu hỏi",
        "en": "Question text",
    },
    "required_question": {
        "vi": "Câu hỏi bắt buộc",
        "en": "Required question",
    },
    "save_question": {
        "vi": "✅ Lưu câu hỏi",
        "en": "✅ Save Question",
    },
    "cancel": {
        "vi": "❌ Hủy",
        "en": "❌ Cancel",
    },
    "question_list": {
        "vi": "Danh sách câu hỏi",
        "en": "Question List",
    },
    "options_per_line": {
        "vi": "Các lựa chọn (mỗi dòng một lựa chọn)",
        "en": "Options (one per line)",
    },
    "scale_min": {
        "vi": "Giá trị nhỏ nhất",
        "en": "Minimum value",
    },
    "scale_max": {
        "vi": "Giá trị lớn nhất",
        "en": "Maximum value",
    },
    "scale_labels": {
        "vi": "Nhãn thang đo",
        "en": "Scale Labels",
    },
    "label_for": {
        "vi": "Nhãn cho",
        "en": "Label for",
    },
    "required_mark": {
        "vi": "(bắt buộc)",
        "en": "(required)",
    },
    "required_missing": {
        "vi": "Vui lòng trả lời các câu hỏi bắt buộc sau:",
        "en": "Please answer the following required questions:",
    },
    "submit_response": {
        "vi": "📤 Nộp phản hồi",
        "en": "📤 Submit Response",
    },
    "thank_you": {
        "vi": "✅ Cảm ơn bạn đã tham gia khảo sát! Phản hồi của bạn đã được ghi nhận.",
        "en": "✅ Thank you for participating! Your response has been recorded.",
    },
    "submit_another": {
        "vi": "📝 Nộp phản hồi khác",
        "en": "📝 Submit Another Response",
    },
    "answer_survey_page": {
        "vi": "📋 Trả Lời Khảo Sát",
        "en": "📋 Answer Survey",
    },
    "choose_survey_to_answer": {
        "vi": "Chọn khảo sát để trả lời",
        "en": "Choose a survey to answer",
    },
    "your_answer": {
        "vi": "Câu trả lời của bạn",
        "en": "Your answer",
    },
    "select_one": {
        "vi": "Chọn một đáp án",
        "en": "Select one option",
    },
    "select_all": {
        "vi": "Chọn tất cả đáp án phù hợp",
        "en": "Select all that apply",
    },
    "your_rating": {
        "vi": "Đánh giá của bạn",
        "en": "Your rating",
    },
    "enter_answer": {
        "vi": "Nhập câu trả lời...",
        "en": "Enter your answer...",
    },

    # Loại câu hỏi
    "q_text": {"vi": "Văn bản ngắn", "en": "Short Text"},
    "q_paragraph": {"vi": "Đoạn văn bản dài", "en": "Long Text"},
    "q_number": {"vi": "Số", "en": "Number"},
    "q_multiple_choice": {"vi": "Một lựa chọn (Radio)", "en": "Single Choice (Radio)"},
    "q_checkbox": {"vi": "Nhiều lựa chọn (Checkbox)", "en": "Multiple Choice (Checkbox)"},
    "q_dropdown": {"vi": "Danh sách thả xuống", "en": "Dropdown"},
    "q_likert_scale": {"vi": "Thang đo Likert", "en": "Likert Scale"},
    "q_date": {"vi": "Ngày tháng", "en": "Date"},
    "q_email": {"vi": "Địa chỉ Email", "en": "Email Address"},
    "q_phone": {"vi": "Số điện thoại", "en": "Phone Number"},

    # Likert labels mặc định
    "likert_1": {"vi": "Hoàn toàn không đồng ý", "en": "Strongly Disagree"},
    "likert_2": {"vi": "Không đồng ý", "en": "Disagree"},
    "likert_3": {"vi": "Trung lập", "en": "Neutral"},
    "likert_4": {"vi": "Đồng ý", "en": "Agree"},
    "likert_5": {"vi": "Hoàn toàn đồng ý", "en": "Strongly Agree"},

    # ── Phân phối / Distribute ────────────────────────────────────────────────
    "distribute_page": {
        "vi": "🔗 Phân Phối Khảo Sát",
        "en": "🔗 Distribute Survey",
    },
    "choose_to_distribute": {
        "vi": "Chọn khảo sát để phân phối",
        "en": "Choose a survey to distribute",
    },
    "survey_link": {
        "vi": "🔗 Đường dẫn khảo sát",
        "en": "🔗 Survey Link",
    },
    "preview_survey": {
        "vi": "👁️ Xem trước",
        "en": "👁️ Preview",
    },
    "preview_btn": {
        "vi": "Xem trước khảo sát",
        "en": "Preview Survey",
    },
    "open_form": {
        "vi": "📝 Trả lời ngay",
        "en": "📝 Answer Now",
    },
    "open_form_btn": {
        "vi": "Mở form trả lời",
        "en": "Open Answer Form",
    },
    "qr_code": {
        "vi": "📱 Mã QR",
        "en": "📱 QR Code",
    },
    "scan_qr": {
        "vi": "Quét để trả lời khảo sát",
        "en": "Scan to answer survey",
    },
    "download_qr": {
        "vi": "⬇️ Tải QR Code",
        "en": "⬇️ Download QR Code",
    },
    "export_data": {
        "vi": "📤 Xuất dữ liệu phản hồi",
        "en": "📤 Export Response Data",
    },
    "export_csv": {
        "vi": "📄 Xuất CSV",
        "en": "📄 Export CSV",
    },
    "export_json": {
        "vi": "🗂️ Xuất JSON",
        "en": "🗂️ Export JSON",
    },
    "export_excel": {
        "vi": "📊 Xuất Excel",
        "en": "📊 Export Excel",
    },
    "no_responses_export": {
        "vi": "Chưa có phản hồi nào để xuất.",
        "en": "No responses to export yet.",
    },
    "close_preview": {
        "vi": "❌ Đóng xem trước",
        "en": "❌ Close Preview",
    },
    "distribute_guide": {
        "vi": "📌 Hướng dẫn phân phối khảo sát",
        "en": "📌 Distribution Guide",
    },

    # ── Xem phản hồi / View Responses ────────────────────────────────────────
    "view_responses_page": {
        "vi": "📊 Xem Phản Hồi Khảo Sát",
        "en": "📊 View Survey Responses",
    },
    "choose_to_view": {
        "vi": "Chọn khảo sát để xem phản hồi",
        "en": "Choose a survey to view responses",
    },
    "latest_response": {
        "vi": "Phản hồi mới nhất",
        "en": "Latest Response",
    },
    "data_table": {
        "vi": "📋 Bảng dữ liệu tổng hợp",
        "en": "📋 Data Summary Table",
    },
    "filter_date": {
        "vi": "Lọc theo ngày",
        "en": "Filter by date",
    },
    "show_meta": {
        "vi": "Hiển thị thông tin bổ sung (thời gian, IP)",
        "en": "Show metadata (time, IP)",
    },
    "download_excel": {
        "vi": "📥 Tải xuống Excel",
        "en": "📥 Download Excel",
    },
    "view_detail": {
        "vi": "🔍 Xem chi tiết từng phản hồi",
        "en": "🔍 View Individual Responses",
    },
    "response_num": {
        "vi": "Phản hồi",
        "en": "Response",
    },
    "no_responses_yet": {
        "vi": "Chưa có phản hồi nào cho khảo sát này.",
        "en": "No responses received for this survey yet.",
    },
    "no_answer": {
        "vi": "_(không có)_",
        "en": "_(no answer)_",
    },

    # ── Admin ─────────────────────────────────────────────────────────────────
    "admin_panel": {
        "vi": "⚙️ Quản Trị Hệ Thống",
        "en": "⚙️ System Administration",
    },
    "admin_panel_short": {
        "vi": "🔧 Panel quản trị",
        "en": "🔧 Admin Panel",
    },
    "home": {
        "vi": "🏠 Trang chủ",
        "en": "🏠 Home",
    },

    # ── Footer ────────────────────────────────────────────────────────────────
    "footer_system": {
        "vi": "Hệ thống Khảo sát HHD-HY",
        "en": "HHD-HY Survey System",
    },
    "footer_copy": {
        "vi": "© Bản quyền thuộc về Đỗ Hữu Hải",
        "en": "© Copyright by Đỗ Hữu Hải",
    },

    # ── AI Insights (page 11) ─────────────────────────────────────────────────
    "ai_insights_page": {
        "vi": "🤖 AI Insights & Phân tích Thông minh",
        "en": "🤖 AI Insights & Smart Analysis",
    },
    "ai_insights_subtitle": {
        "vi": "Phân tích tự động và khuyến nghị từ dữ liệu khảo sát",
        "en": "Automated analysis and recommendations from survey data",
    },
    "select_survey_insights": {
        "vi": "Chọn khảo sát để phân tích AI",
        "en": "Select survey for AI analysis",
    },
    "auto_insights_tab": {
        "vi": "💡 Insights tự động",
        "en": "💡 Auto Insights",
    },
    "knowledge_gap_tab": {
        "vi": "🎯 Khoảng cách kiến thức",
        "en": "🎯 Knowledge Gap",
    },
    "radar_tab": {
        "vi": "🕸️ Biểu đồ Radar",
        "en": "🕸️ Radar Chart",
    },
    "recommendations_tab": {
        "vi": "📋 Khuyến nghị",
        "en": "📋 Recommendations",
    },
    "no_insights": {
        "vi": "Chưa đủ dữ liệu để tạo insights. Hãy thu thập thêm phản hồi.",
        "en": "Not enough data for insights. Please collect more responses.",
    },
    "knowledge_gap_title": {
        "vi": "🎯 Phân tích Khoảng cách Kiến thức",
        "en": "🎯 Knowledge Gap Analysis",
    },
    "knowledge_gap_desc": {
        "vi": "Các câu hỏi có điểm số dưới ngưỡng — cần cải thiện",
        "en": "Questions scoring below threshold — need improvement",
    },
    "no_knowledge_gaps": {
        "vi": "✅ Không phát hiện khoảng cách kiến thức đáng lo ngại (tất cả câu hỏi ≥ ngưỡng).",
        "en": "✅ No significant knowledge gaps detected (all questions above threshold).",
    },
    "gap_threshold": {
        "vi": "Ngưỡng khoảng cách (%)",
        "en": "Gap threshold (%)",
    },
    "radar_title": {
        "vi": "🕸️ Bản đồ điểm số theo câu hỏi (Radar)",
        "en": "🕸️ Question Score Map (Radar)",
    },
    "radar_no_likert": {
        "vi": "Cần ít nhất 3 câu hỏi Likert để vẽ biểu đồ Radar.",
        "en": "At least 3 Likert questions needed for Radar chart.",
    },
    "ai_recommend_title": {
        "vi": "📋 Khuyến nghị cải thiện",
        "en": "📋 Improvement Recommendations",
    },
    "generate_report_btn": {
        "vi": "📄 Tạo báo cáo AI",
        "en": "📄 Generate AI Report",
    },
    "report_generated": {
        "vi": "Báo cáo đã được tạo:",
        "en": "Report generated:",
    },

    # ── Survey Templates ───────────────────────────────────────────────────────
    "survey_templates": {
        "vi": "📋 Mẫu khảo sát có sẵn",
        "en": "📋 Survey Templates",
    },
    "load_template_btn": {
        "vi": "📥 Tải mẫu này",
        "en": "📥 Load this template",
    },
    "template_loaded": {
        "vi": "✅ Đã tải mẫu khảo sát! Chỉnh sửa và lưu theo nhu cầu.",
        "en": "✅ Template loaded! Edit and save as needed.",
    },
    "select_template": {
        "vi": "Chọn mẫu:",
        "en": "Select template:",
    },
    "tpl_training": {
        "vi": "Đánh giá khóa đào tạo (Likert 5 điểm)",
        "en": "Training Evaluation (5-pt Likert)",
    },
    "tpl_satisfaction": {
        "vi": "Hài lòng khóa học / Course Satisfaction",
        "en": "Course Satisfaction Survey",
    },
    "tpl_culture": {
        "vi": "Văn hóa doanh nghiệp / Corporate Culture",
        "en": "Corporate Culture Survey",
    },
    "tpl_quiz": {
        "vi": "Kiểm tra kiến thức / Knowledge Quiz",
        "en": "Knowledge Quiz",
    },
    "tpl_feedback": {
        "vi": "Phản hồi sản phẩm / Product Feedback",
        "en": "Product Feedback",
    },

    # ── Deploy / Mobile hints ──────────────────────────────────────────────────
    "deploy_guide": {
        "vi": "🚀 Hướng dẫn triển khai",
        "en": "🚀 Deployment Guide",
    },
}


# ─── API công khai ─────────────────────────────────────────────────────────────

def get_lang() -> str:
    """Trả về ngôn ngữ hiện tại từ session state ('vi' hoặc 'en')."""
    return st.session_state.get("lang", "vi")


def t(key: str, lang: str | None = None) -> str:
    """
    Tra cứu chuỗi dịch theo key.
    Nếu không tìm thấy key trả về chính key đó.
    """
    if lang is None:
        lang = get_lang()
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("vi", key))


def render_language_selector() -> None:
    """
    Hiển thị bộ chọn ngôn ngữ En / Vi trên sidebar.
    Gọi trong mỗi trang sau khi st.set_page_config.
    """
    if "lang" not in st.session_state:
        st.session_state.lang = "vi"

    current = st.session_state.lang

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"🌐 **{t('language')}**")

    col_vi, col_en = st.sidebar.columns(2)

    with col_vi:
        vi_type = "primary" if current == "vi" else "secondary"
        if st.button("🇻🇳 Tiếng Việt", key="_lang_vi",
                     use_container_width=True, type=vi_type):
            st.session_state.lang = "vi"
            st.rerun()

    with col_en:
        en_type = "primary" if current == "en" else "secondary"
        if st.button("🇬🇧 English", key="_lang_en",
                     use_container_width=True, type=en_type):
            st.session_state.lang = "en"
            st.rerun()

    st.sidebar.markdown("---")


def get_question_types(lang: str | None = None) -> dict:
    """Trả về dict loại câu hỏi đã dịch."""
    return {
        "text": t("q_text", lang),
        "paragraph": t("q_paragraph", lang),
        "number": t("q_number", lang),
        "multiple_choice": t("q_multiple_choice", lang),
        "checkbox": t("q_checkbox", lang),
        "dropdown": t("q_dropdown", lang),
        "likert_scale": t("q_likert_scale", lang),
        "date": t("q_date", lang),
        "email": t("q_email", lang),
        "phone": t("q_phone", lang),
    }


def get_default_likert_labels(lang: str | None = None) -> list:
    """Trả về nhãn Likert mặc định theo ngôn ngữ."""
    return [
        t("likert_1", lang),
        t("likert_2", lang),
        t("likert_3", lang),
        t("likert_4", lang),
        t("likert_5", lang),
    ]
