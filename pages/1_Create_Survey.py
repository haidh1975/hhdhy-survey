import streamlit as st
import json
import uuid
import datetime
import os
from utils.survey_utils import save_surveys
from utils.auth import require_auth, get_current_user
from utils.db_utils import create_survey_db, get_surveys_db, get_survey_by_uuid_db, update_survey_db
from utils.models import User
from utils.database import SessionLocal
from utils.i18n import render_language_selector, t, get_lang, get_question_types, get_default_likert_labels

# ── Survey Templates Library ──────────────────────────────────────────────────
# Market gap: SurveyMonkey/Typeform have templates; HHD-HY adds Vietnamese-first templates
# for education, training, and corporate culture surveys.

_LIKERT_VI = ["Rất không đồng ý", "Không đồng ý", "Trung lập", "Đồng ý", "Rất đồng ý"]
_LIKERT_EN = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
_SATISFY_VI = ["Rất không hài lòng", "Không hài lòng", "Bình thường", "Hài lòng", "Rất hài lòng"]
_SATISFY_EN = ["Very Dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very Satisfied"]


def _uid(n: int) -> str:
    import uuid as _uuid
    return str(_uuid.uuid4())[:8] + str(n)


SURVEY_TEMPLATES: dict = {
    "tpl_training": {
        "vi": {
            "title": "Đánh giá Khóa Đào tạo",
            "description": "Khảo sát đánh giá chất lượng và hiệu quả của khóa đào tạo",
            "questions": [
                {"id": _uid(1), "type": "likert_scale", "required": True,
                 "question_text": "Nội dung khóa đào tạo phù hợp với công việc thực tế",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(2), "type": "likert_scale", "required": True,
                 "question_text": "Giảng viên/huấn luyện viên truyền đạt rõ ràng, dễ hiểu",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(3), "type": "likert_scale", "required": True,
                 "question_text": "Tài liệu học tập đầy đủ và có chất lượng tốt",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(4), "type": "likert_scale", "required": True,
                 "question_text": "Thời lượng khóa học phù hợp với khối lượng nội dung",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(5), "type": "likert_scale", "required": True,
                 "question_text": "Khóa học đáp ứng được mục tiêu học tập của tôi",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(6), "type": "likert_scale", "required": True,
                 "question_text": "Tôi có thể áp dụng kiến thức từ khóa học vào công việc",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(7), "type": "multiple_choice", "required": True,
                 "question_text": "Hình thức học tập nào bạn thấy hiệu quả nhất?",
                 "options": ["Giảng dạy trực tiếp", "Thực hành thực tế", "Thảo luận nhóm",
                             "Video/eLearning", "Bài tập tình huống"]},
                {"id": _uid(8), "type": "paragraph", "required": False,
                 "question_text": "Điểm nào của khóa đào tạo bạn muốn được cải thiện?"},
                {"id": _uid(9), "type": "likert_scale", "required": True,
                 "question_text": "Tôi sẽ giới thiệu khóa học này cho đồng nghiệp",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(10), "type": "paragraph", "required": False,
                 "question_text": "Ý kiến khác / Góp ý bổ sung"},
            ]
        },
        "en": {
            "title": "Training Evaluation Survey",
            "description": "Evaluate the quality and effectiveness of the training course",
            "questions": [
                {"id": _uid(1), "type": "likert_scale", "required": True,
                 "question_text": "Course content is relevant to my actual work",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(2), "type": "likert_scale", "required": True,
                 "question_text": "The trainer communicated clearly and was easy to understand",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(3), "type": "likert_scale", "required": True,
                 "question_text": "Learning materials were comprehensive and high quality",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(4), "type": "likert_scale", "required": True,
                 "question_text": "The training duration was appropriate for the content volume",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(5), "type": "likert_scale", "required": True,
                 "question_text": "The course met my learning objectives",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(6), "type": "likert_scale", "required": True,
                 "question_text": "I can apply knowledge from this course to my work",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(7), "type": "multiple_choice", "required": True,
                 "question_text": "Which learning format did you find most effective?",
                 "options": ["Classroom instruction", "Hands-on practice", "Group discussion",
                             "Video/eLearning", "Case studies"]},
                {"id": _uid(8), "type": "paragraph", "required": False,
                 "question_text": "What aspects of the training would you like improved?"},
                {"id": _uid(9), "type": "likert_scale", "required": True,
                 "question_text": "I would recommend this course to a colleague",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(10), "type": "paragraph", "required": False,
                 "question_text": "Other comments / Additional feedback"},
            ]
        }
    },
    "tpl_satisfaction": {
        "vi": {
            "title": "Khảo sát Hài lòng Học viên",
            "description": "Đo lường mức độ hài lòng của học viên với khóa học/chương trình",
            "questions": [
                {"id": _uid(11), "type": "likert_scale", "required": True,
                 "question_text": "Nhìn chung, tôi hài lòng với chương trình học",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(12), "type": "likert_scale", "required": True,
                 "question_text": "Cơ sở vật chất / môi trường học tập tốt",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(13), "type": "likert_scale", "required": True,
                 "question_text": "Chương trình học đáp ứng nhu cầu của tôi",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(14), "type": "likert_scale", "required": True,
                 "question_text": "Đội ngũ giảng viên chuyên nghiệp và hỗ trợ tốt",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(15), "type": "multiple_choice", "required": True,
                 "question_text": "Bạn biết đến chương trình qua kênh nào?",
                 "options": ["Bạn bè / đồng nghiệp giới thiệu", "Mạng xã hội", "Website chính thức",
                             "Email marketing", "Khác"]},
                {"id": _uid(16), "type": "text", "required": False,
                 "question_text": "Điều bạn ấn tượng nhất với chương trình là gì?"},
                {"id": _uid(17), "type": "paragraph", "required": False,
                 "question_text": "Góp ý để cải thiện chương trình"},
            ]
        },
        "en": {
            "title": "Student Satisfaction Survey",
            "description": "Measure student satisfaction with the course/program",
            "questions": [
                {"id": _uid(11), "type": "likert_scale", "required": True,
                 "question_text": "Overall, I am satisfied with the program",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(12), "type": "likert_scale", "required": True,
                 "question_text": "Facilities / learning environment are good",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(13), "type": "likert_scale", "required": True,
                 "question_text": "The curriculum meets my needs",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(14), "type": "likert_scale", "required": True,
                 "question_text": "Faculty are professional and supportive",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(15), "type": "multiple_choice", "required": True,
                 "question_text": "How did you hear about the program?",
                 "options": ["Friend/colleague referral", "Social media", "Official website",
                             "Email marketing", "Other"]},
                {"id": _uid(16), "type": "text", "required": False,
                 "question_text": "What impressed you most about the program?"},
                {"id": _uid(17), "type": "paragraph", "required": False,
                 "question_text": "Suggestions to improve the program"},
            ]
        }
    },
    "tpl_culture": {
        "vi": {
            "title": "Khảo sát Văn hóa Doanh nghiệp",
            "description": "Đánh giá văn hóa tổ chức và gắn kết nhân viên (HHD Corporate Culture)",
            "questions": [
                {"id": _uid(21), "type": "likert_scale", "required": True,
                 "question_text": "Tôi hiểu rõ tầm nhìn và sứ mệnh của công ty",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(22), "type": "likert_scale", "required": True,
                 "question_text": "Môi trường làm việc tạo điều kiện cho sự sáng tạo và đổi mới",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(23), "type": "likert_scale", "required": True,
                 "question_text": "Đồng nghiệp hợp tác và hỗ trợ nhau tốt",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(24), "type": "likert_scale", "required": True,
                 "question_text": "Lãnh đạo lắng nghe và tôn trọng ý kiến nhân viên",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(25), "type": "likert_scale", "required": True,
                 "question_text": "Tôi cảm thấy gắn kết và muốn cống hiến lâu dài cho công ty",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(26), "type": "likert_scale", "required": True,
                 "question_text": "Các chính sách đãi ngộ công bằng và minh bạch",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(27), "type": "multiple_choice", "required": True,
                 "question_text": "Giá trị văn hóa nào bạn cảm nhận mạnh nhất tại công ty?",
                 "options": ["Tin tưởng và tôn trọng", "Đổi mới và sáng tạo",
                             "Khách hàng là trọng tâm", "Trách nhiệm cộng đồng", "Hiệu quả & kết quả"]},
                {"id": _uid(28), "type": "paragraph", "required": False,
                 "question_text": "Bạn muốn thay đổi điều gì trong văn hóa doanh nghiệp hiện tại?"},
            ]
        },
        "en": {
            "title": "Corporate Culture Survey",
            "description": "Assess organizational culture and employee engagement",
            "questions": [
                {"id": _uid(21), "type": "likert_scale", "required": True,
                 "question_text": "I clearly understand the company's vision and mission",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(22), "type": "likert_scale", "required": True,
                 "question_text": "The work environment fosters creativity and innovation",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(23), "type": "likert_scale", "required": True,
                 "question_text": "Colleagues collaborate and support each other well",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(24), "type": "likert_scale", "required": True,
                 "question_text": "Leadership listens to and respects employee input",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(25), "type": "likert_scale", "required": True,
                 "question_text": "I feel connected and want to contribute long-term",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(26), "type": "likert_scale", "required": True,
                 "question_text": "Compensation and benefits policies are fair and transparent",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(27), "type": "multiple_choice", "required": True,
                 "question_text": "Which cultural value do you feel most strongly at the company?",
                 "options": ["Trust & Respect", "Innovation & Creativity",
                             "Customer Focus", "Community Responsibility", "Results & Efficiency"]},
                {"id": _uid(28), "type": "paragraph", "required": False,
                 "question_text": "What would you change about the current corporate culture?"},
            ]
        }
    },
    "tpl_quiz": {
        "vi": {
            "title": "Kiểm tra kiến thức sau đào tạo",
            "description": "Đánh giá mức độ tiếp thu kiến thức sau khóa học",
            "questions": [
                {"id": _uid(31), "type": "multiple_choice", "required": True,
                 "question_text": "Mục tiêu chính của khóa đào tạo này là gì?",
                 "options": ["Nâng cao kỹ năng nghề nghiệp", "Xây dựng tinh thần đội nhóm",
                             "Tuân thủ quy trình nội bộ", "Phát triển tư duy lãnh đạo"]},
                {"id": _uid(32), "type": "multiple_choice", "required": True,
                 "question_text": "Khi gặp vấn đề trong công việc, bước đầu tiên bạn nên làm là?",
                 "options": ["Báo cáo ngay lên cấp trên", "Xác định nguyên nhân gốc rễ",
                             "Bỏ qua nếu không ảnh hưởng đến mình", "Hỏi đồng nghiệp để tìm cách xử lý"]},
                {"id": _uid(33), "type": "likert_scale", "required": True,
                 "question_text": "Tôi tự tin áp dụng kiến thức đã học vào công việc",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_VI},
                {"id": _uid(34), "type": "text", "required": True,
                 "question_text": "Nêu một điều quan trọng nhất bạn học được từ khóa đào tạo này"},
                {"id": _uid(35), "type": "multiple_choice", "required": True,
                 "question_text": "Bạn có kế hoạch áp dụng kiến thức này trong bao lâu?",
                 "options": ["Ngay lập tức (trong tuần này)", "Trong tháng tới",
                             "Trong 3 tháng tới", "Chưa có kế hoạch cụ thể"]},
            ]
        },
        "en": {
            "title": "Post-Training Knowledge Quiz",
            "description": "Assess knowledge retention after the training course",
            "questions": [
                {"id": _uid(31), "type": "multiple_choice", "required": True,
                 "question_text": "What is the primary objective of this training?",
                 "options": ["Enhance professional skills", "Build team spirit",
                             "Comply with internal processes", "Develop leadership thinking"]},
                {"id": _uid(32), "type": "multiple_choice", "required": True,
                 "question_text": "When you encounter a problem at work, the first step should be?",
                 "options": ["Report immediately to supervisor", "Identify the root cause",
                             "Ignore if it doesn't affect you", "Ask colleagues for solutions"]},
                {"id": _uid(33), "type": "likert_scale", "required": True,
                 "question_text": "I am confident in applying the learned knowledge to my work",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _LIKERT_EN},
                {"id": _uid(34), "type": "text", "required": True,
                 "question_text": "State the most important thing you learned from this training"},
                {"id": _uid(35), "type": "multiple_choice", "required": True,
                 "question_text": "When do you plan to apply this knowledge?",
                 "options": ["Immediately (this week)", "Next month",
                             "Within 3 months", "No specific plan yet"]},
            ]
        }
    },
    "tpl_feedback": {
        "vi": {
            "title": "Phản hồi sản phẩm / dịch vụ",
            "description": "Thu thập phản hồi từ khách hàng về sản phẩm hoặc dịch vụ",
            "questions": [
                {"id": _uid(41), "type": "likert_scale", "required": True,
                 "question_text": "Sản phẩm/dịch vụ đáp ứng đúng nhu cầu của tôi",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(42), "type": "likert_scale", "required": True,
                 "question_text": "Chất lượng tổng thể xứng đáng với giá trị chi trả",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(43), "type": "likert_scale", "required": True,
                 "question_text": "Dịch vụ hỗ trợ khách hàng nhanh chóng và chuyên nghiệp",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_VI},
                {"id": _uid(44), "type": "multiple_choice", "required": True,
                 "question_text": "Bạn có khả năng giới thiệu sản phẩm này cho người khác không?",
                 "options": ["Chắc chắn có", "Có thể", "Chưa chắc", "Không"]},
                {"id": _uid(45), "type": "paragraph", "required": False,
                 "question_text": "Tính năng nào bạn muốn được bổ sung hoặc cải thiện?"},
            ]
        },
        "en": {
            "title": "Product / Service Feedback",
            "description": "Collect customer feedback on product or service",
            "questions": [
                {"id": _uid(41), "type": "likert_scale", "required": True,
                 "question_text": "The product/service meets my needs",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(42), "type": "likert_scale", "required": True,
                 "question_text": "Overall quality is worth the price paid",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(43), "type": "likert_scale", "required": True,
                 "question_text": "Customer support is fast and professional",
                 "scale_min": 1, "scale_max": 5, "scale_labels": _SATISFY_EN},
                {"id": _uid(44), "type": "multiple_choice", "required": True,
                 "question_text": "Would you recommend this product to others?",
                 "options": ["Definitely yes", "Probably yes", "Unsure", "No"]},
                {"id": _uid(45), "type": "paragraph", "required": False,
                 "question_text": "Which features would you like added or improved?"},
            ]
        }
    },
}

# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HHD-HY — Tạo Khảo Sát / Create Survey",
    page_icon="📝",
    layout="wide",
)

render_language_selector()

# Require authentication to access this page
require_auth()

# Load surveys from database
@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_surveys_from_db():
    """Load surveys from database"""
    surveys = get_surveys_db()
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

# Load surveys from database
st.session_state.surveys = load_surveys_from_db()

def get_current_user_id():
    """Get current user ID from database"""
    current_username = get_current_user()
    if not current_username:
        return None
    
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == current_username).first()
        return user.id if user else None
    finally:
        session.close()

if 'current_survey' not in st.session_state or st.session_state.current_survey is None:
    # Tự động tải khảo sát đầu tiên nếu có
    if st.session_state.surveys:
        default_survey_id = list(st.session_state.surveys.keys())[0]
        st.session_state.current_survey = st.session_state.surveys[default_survey_id].copy()
        st.session_state.current_survey_id = default_survey_id
    else:
        st.session_state.current_survey = {
            "title": "",
            "description": "",
            "questions": []
        }
        st.session_state.current_survey_id = None

if 'current_survey_id' not in st.session_state:
    st.session_state.current_survey_id = None

if 'editing_question_index' not in st.session_state:
    st.session_state.editing_question_index = -1

_page_title = "✏️ Tạo / Chỉnh sửa Khảo Sát" if get_lang() == "vi" else "✏️ Create / Edit Survey"
st.title(_page_title)

# Function to create a new survey
def create_new_survey():
    st.session_state.current_survey = {
        "title": "",
        "description": "",
        "questions": []
    }
    st.session_state.current_survey_id = None
    st.session_state.editing_question_index = -1

# Function to save the current survey
def save_survey():
    if not st.session_state.current_survey["title"]:
        st.error("Vui lòng nhập tiêu đề khảo sát.")
        return
    
    if not st.session_state.current_survey["questions"]:
        st.error("Vui lòng thêm ít nhất một câu hỏi vào khảo sát.")
        return
    
    # Get current user ID
    user_id = get_current_user_id()
    if not user_id:
        st.error("Không thể xác định người dùng hiện tại.")
        return
    
    title = st.session_state.current_survey["title"]
    description = st.session_state.current_survey.get("description", "")
    questions = st.session_state.current_survey["questions"]
    
    if st.session_state.current_survey_id is None:
        # Create new survey
        success, message, survey_uuid = create_survey_db(title, description, questions, user_id)
        if success:
            st.success(f"Khảo sát '{title}' đã được tạo thành công!")
            st.session_state.current_survey_id = survey_uuid
            # Refresh surveys list
            st.session_state.surveys = load_surveys_from_db()
            create_new_survey()
        else:
            st.error(f"Lỗi tạo khảo sát: {message}")
    else:
        # Update existing survey
        success, message = update_survey_db(st.session_state.current_survey_id, title, description, questions)
        if success:
            st.success(f"Khảo sát '{title}' đã được cập nhật thành công!")
            # Refresh surveys list
            st.session_state.surveys = load_surveys_from_db()
        else:
            st.error(f"Lỗi cập nhật khảo sát: {message}")

# Function to add a question to the survey
def add_question(question_type):
    new_question = {
        "type": question_type,
        "question_text": "",
        "required": False
    }
    
    if question_type in ["multiple_choice", "dropdown", "checkbox"]:
        new_question["options"] = []
    elif question_type == "likert_scale":
        new_question["scale_min"] = 1
        new_question["scale_max"] = 5
        new_question["scale_labels"] = ["Hoàn toàn không đồng ý", "Không đồng ý", "Trung lập", "Đồng ý", "Hoàn toàn đồng ý"]
    
    if st.session_state.editing_question_index >= 0:
        st.session_state.current_survey["questions"][st.session_state.editing_question_index] = new_question
    else:
        st.session_state.current_survey["questions"].append(new_question)
    
    st.session_state.editing_question_index = len(st.session_state.current_survey["questions"]) - 1

# Function to edit a question
def edit_question(index):
    st.session_state.editing_question_index = index

# Function to delete a question
def delete_question(index):
    del st.session_state.current_survey["questions"][index]
    st.session_state.editing_question_index = -1

# Move question up (swap with previous) — GeeksforGeeks in-place array swap
def move_question_up(index):
    if index > 0:
        qs = st.session_state.current_survey["questions"]
        qs[index], qs[index - 1] = qs[index - 1], qs[index]
        st.session_state.editing_question_index = -1

# Move question down (swap with next)
def move_question_down(index):
    qs = st.session_state.current_survey["questions"]
    if index < len(qs) - 1:
        qs[index], qs[index + 1] = qs[index + 1], qs[index]
        st.session_state.editing_question_index = -1

# Duplicate question
def duplicate_question(index):
    import copy
    qs = st.session_state.current_survey["questions"]
    new_q = copy.deepcopy(qs[index])
    new_q["id"] = str(__import__("uuid").uuid4())[:8]
    qs.insert(index + 1, new_q)
    st.session_state.editing_question_index = -1

# Interface to select existing survey or create new one
st.sidebar.header(t("manage_surveys"))

if st.sidebar.button(t("create_new_survey")):
    create_new_survey()

if st.session_state.surveys:
    selected_survey = st.sidebar.selectbox(
        t("edit_existing"),
        options=list(st.session_state.surveys.keys()),
        format_func=lambda x: st.session_state.surveys[x]["title"],
        index=None,
    )

    if selected_survey and st.sidebar.button(t("load_selected")):
        st.session_state.current_survey = st.session_state.surveys[selected_survey]
        st.session_state.current_survey_id = selected_survey
        st.session_state.editing_question_index = -1
        st.rerun()

    # Sidebar: survey question count badge
    st.sidebar.markdown("---")
    _badge_lbl = "Câu hỏi hiện tại" if get_lang() == "vi" else "Current questions"
    n_qs = len(st.session_state.current_survey.get("questions", []))
    st.sidebar.metric(_badge_lbl, n_qs)

# ── Survey Templates (sidebar) ────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {t('survey_templates')}")

_tpl_opts = {
    "tpl_training": t("tpl_training"),
    "tpl_satisfaction": t("tpl_satisfaction"),
    "tpl_culture": t("tpl_culture"),
    "tpl_quiz": t("tpl_quiz"),
    "tpl_feedback": t("tpl_feedback"),
}
_tpl_key = st.sidebar.selectbox(
    t("select_template"),
    options=list(_tpl_opts.keys()),
    format_func=lambda k: _tpl_opts[k],
    key="_tpl_selector",
)

if st.sidebar.button(t("load_template_btn"), use_container_width=True):
    import copy as _copy
    _tpl_data = SURVEY_TEMPLATES.get(_tpl_key, {})
    _lang = get_lang()
    _tpl_lang = _tpl_data.get(_lang, _tpl_data.get("vi", {}))
    if _tpl_lang:
        st.session_state.current_survey = {
            "title": _tpl_lang.get("title", ""),
            "description": _tpl_lang.get("description", ""),
            "questions": _copy.deepcopy(_tpl_lang.get("questions", [])),
        }
        st.session_state.current_survey_id = None
        st.session_state.editing_question_index = -1
        st.sidebar.success(t("template_loaded"))
        st.rerun()

# Form thông tin khảo sát
with st.form(key="survey_form"):
    st.subheader(t("survey_info"))
    survey_title = st.text_input(t("survey_title"), value=st.session_state.current_survey["title"])
    survey_description = st.text_area(t("survey_description"), value=st.session_state.current_survey["description"])
    # Character counter
    st.caption(f"{'Tiêu đề' if get_lang() == 'vi' else 'Title'}: {len(survey_title)}/200  |  "
               f"{'Mô tả' if get_lang() == 'vi' else 'Description'}: {len(survey_description)}/1000")

    st.session_state.current_survey["title"] = survey_title
    st.session_state.current_survey["description"] = survey_description

    submitted = st.form_submit_button(t("save_survey"))
    if submitted:
        save_survey()

# Chọn loại câu hỏi
st.subheader(t("add_questions"))
question_types = get_question_types()

col1, col2 = st.columns(2)
with col1:
    selected_type = st.selectbox(
        t("question_type"),
        options=list(question_types.keys()),
        format_func=lambda x: question_types[x],
    )
with col2:
    st.button(t("add_question_btn"), on_click=add_question, args=(selected_type,))

# Trình chỉnh sửa câu hỏi
if st.session_state.editing_question_index >= 0:
    _edit_qs_idx = st.session_state.editing_question_index
    if _edit_qs_idx < len(st.session_state.current_survey["questions"]):
        st.subheader(t("edit_question"))
        question = st.session_state.current_survey["questions"][_edit_qs_idx]

        q_text = st.text_input(t("question_text"), value=question.get("question_text", ""))
        question["question_text"] = q_text
        st.caption(f"{len(q_text)}/300")

        question["required"] = st.checkbox(t("required_question"), value=question.get("required", False))

        if question["type"] in ["multiple_choice", "dropdown", "checkbox"]:
            options_text = st.text_area(
                t("options_per_line"),
                value="\n".join(question.get("options", [])),
                height=150,
            )
            question["options"] = [opt.strip() for opt in options_text.split("\n") if opt.strip()]

        elif question["type"] == "likert_scale":
            col1, col2 = st.columns(2)
            with col1:
                question["scale_min"] = st.number_input(t("scale_min"), value=question.get("scale_min", 1), min_value=1)
            with col2:
                question["scale_max"] = st.number_input(t("scale_max"), value=question.get("scale_max", 5), min_value=2)

            scale_range = range(question["scale_min"], question["scale_max"] + 1)
            current_labels = question.get("scale_labels", get_default_likert_labels())
            while len(current_labels) < len(scale_range):
                current_labels.append(f"Nhãn {len(current_labels) + 1}")
            current_labels = current_labels[:len(scale_range)]

            st.subheader(t("scale_labels"))
            updated_labels = []
            for i, value in enumerate(scale_range):
                updated_labels.append(
                    st.text_input(f"{t('label_for')} {value}", value=current_labels[i], key=f"lbl_{i}")
                )
            question["scale_labels"] = updated_labels

        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("save_question")):
                st.session_state.editing_question_index = -1
                st.rerun()
        with col2:
            if st.button(t("cancel")):
                st.session_state.editing_question_index = -1
                st.rerun()

# Hiển thị danh sách câu hỏi
if st.session_state.current_survey["questions"]:
    n_total = len(st.session_state.current_survey["questions"])
    _ql_title = f"📋 {t('question_list')} ({n_total} {'câu hỏi' if get_lang() == 'vi' else 'questions'})"
    st.subheader(_ql_title)

    for i, question in enumerate(st.session_state.current_survey["questions"]):
        req_badge = "🔴" if question.get("required") else "⚪"
        expander_label = f"{req_badge} {i+1}. {question['question_text'][:55] or '(chưa có nội dung)' if get_lang() == 'vi' else '(no content yet)'}"
        with st.expander(expander_label, expanded=False):
            _type_lbl = "Loại" if get_lang() == "vi" else "Type"
            _req_lbl = "Bắt buộc" if get_lang() == "vi" else "Required"
            _yes = "Có" if get_lang() == "vi" else "Yes"
            _no = "Không" if get_lang() == "vi" else "No"
            st.write(f"**{_type_lbl}:** {question_types.get(question['type'], question['type'])}")
            st.write(f"**{_req_lbl}:** {_yes if question.get('required', False) else _no}")

            if question["type"] in ["multiple_choice", "dropdown", "checkbox"] and "options" in question:
                _opts_lbl = "Các lựa chọn" if get_lang() == "vi" else "Options"
                st.write(f"**{_opts_lbl}:**")
                for opt in question["options"]:
                    st.markdown(f"- {opt}")

            elif question["type"] == "likert_scale":
                _scale_lbl = "Thang đo" if get_lang() == "vi" else "Scale"
                _label_lbl = "Nhãn" if get_lang() == "vi" else "Labels"
                st.write(f"**{_scale_lbl}:** {question.get('scale_min', 1)} → {question.get('scale_max', 5)}")
                st.write(f"**{_label_lbl}:**")
                for j, label in enumerate(question.get("scale_labels", [])):
                    st.markdown(f"- {question.get('scale_min', 1) + j}: {label}")

            # Action buttons: Edit | Duplicate | ↑ | ↓ | Delete
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                _edit_lbl = "✏️ Sửa" if get_lang() == "vi" else "✏️ Edit"
                if st.button(_edit_lbl, key=f"edit_{i}"):
                    edit_question(i)
                    st.rerun()
            with c2:
                _dup_lbl = "📋 Nhân bản" if get_lang() == "vi" else "📋 Duplicate"
                if st.button(_dup_lbl, key=f"dup_{i}"):
                    duplicate_question(i)
                    st.rerun()
            with c3:
                if st.button("⬆️", key=f"up_{i}", disabled=(i == 0)):
                    move_question_up(i)
                    st.rerun()
            with c4:
                if st.button("⬇️", key=f"dn_{i}", disabled=(i == n_total - 1)):
                    move_question_down(i)
                    st.rerun()
            with c5:
                _del_lbl = "🗑️ Xóa" if get_lang() == "vi" else "🗑️ Delete"
                if st.button(_del_lbl, key=f"del_{i}"):
                    delete_question(i)
                    st.rerun()
