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

st.set_page_config(
    page_title="Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp trên địa bàn tỉnh Hưng Yên",
    page_icon="📝",
    layout="wide",
)

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

st.title("Tạo khảo sát - Khảo sát về Ảnh hưởng của Vốn xã hội, Vốn nhân lực đến phát triển bền vững của doanh nghiệp")

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
        new_question["scale_labels"] = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
    
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

# Interface to select existing survey or create new one
st.sidebar.header("Survey Operations")

if st.sidebar.button("Create New Survey"):
    create_new_survey()

if st.session_state.surveys:
    selected_survey = st.sidebar.selectbox(
        "Edit existing survey",
        options=list(st.session_state.surveys.keys()),
        format_func=lambda x: st.session_state.surveys[x]["title"],
        index=None
    )
    
    if selected_survey and st.sidebar.button("Load Selected Survey"):
        st.session_state.current_survey = st.session_state.surveys[selected_survey]
        st.session_state.current_survey_id = selected_survey
        st.session_state.editing_question_index = -1
        st.rerun()

# Survey form
with st.form(key="survey_form"):
    st.subheader("Survey Information")
    survey_title = st.text_input("Survey Title", value=st.session_state.current_survey["title"])
    survey_description = st.text_area("Survey Description", value=st.session_state.current_survey["description"])
    
    # Update session state
    st.session_state.current_survey["title"] = survey_title
    st.session_state.current_survey["description"] = survey_description
    
    # Submit button
    submitted = st.form_submit_button("Save Survey")
    if submitted:
        save_survey()

# Question Type Selection
st.subheader("Add Questions")
question_types = {
    "text": "Text Input",
    "paragraph": "Paragraph Text",
    "number": "Number Input",
    "multiple_choice": "Multiple Choice",
    "checkbox": "Checkbox (Multiple Selection)",
    "dropdown": "Dropdown",
    "likert_scale": "Likert Scale",
    "date": "Date Picker",
    "email": "Email Address",
    "phone": "Phone Number"
}

col1, col2 = st.columns(2)
with col1:
    selected_type = st.selectbox("Select Question Type", options=list(question_types.keys()), format_func=lambda x: question_types[x])
with col2:
    st.button("Add Question", on_click=add_question, args=(selected_type,))

# Question Editor
if st.session_state.editing_question_index >= 0:
    st.subheader("Edit Question")
    question = st.session_state.current_survey["questions"][st.session_state.editing_question_index]
    
    # Common fields for all question types
    question["question_text"] = st.text_input("Question Text", value=question.get("question_text", ""))
    question["required"] = st.checkbox("Required Question", value=question.get("required", False))
    
    # Type-specific fields
    if question["type"] in ["multiple_choice", "dropdown", "checkbox"]:
        options_text = st.text_area(
            "Options (one per line)",
            value="\n".join(question.get("options", [])),
            height=150
        )
        question["options"] = [opt.strip() for opt in options_text.split("\n") if opt.strip()]
    
    elif question["type"] == "likert_scale":
        col1, col2 = st.columns(2)
        with col1:
            question["scale_min"] = st.number_input("Minimum Scale Value", value=question.get("scale_min", 1), min_value=1)
        with col2:
            question["scale_max"] = st.number_input("Maximum Scale Value", value=question.get("scale_max", 5), min_value=2)
        
        scale_range = range(question["scale_min"], question["scale_max"] + 1)
        
        # Ensure we have enough labels
        current_labels = question.get("scale_labels", [])
        while len(current_labels) < len(scale_range):
            current_labels.append(f"Label {len(current_labels) + 1}")
        
        # Only keep the number of labels we need
        current_labels = current_labels[:len(scale_range)]
        
        st.subheader("Scale Labels")
        updated_labels = []
        for i, value in enumerate(scale_range):
            updated_labels.append(st.text_input(f"Label for {value}", value=current_labels[i]))
        
        question["scale_labels"] = updated_labels
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Question"):
            st.session_state.editing_question_index = -1
            st.rerun()
    with col2:
        if st.button("Cancel"):
            st.session_state.editing_question_index = -1
            st.rerun()

# Display current questions
if st.session_state.current_survey["questions"]:
    st.subheader("Survey Questions")
    for i, question in enumerate(st.session_state.current_survey["questions"]):
        question_index = i  # Thêm biến question_index để tránh trùng lặp key
        with st.expander(f"Question {i+1}: {question['question_text']}", expanded=False):
            st.write(f"**Type:** {question_types[question['type']]}")
            st.write(f"**Required:** {'Yes' if question.get('required', False) else 'No'}")
            
            if question["type"] in ["multiple_choice", "dropdown", "checkbox"] and "options" in question:
                st.write("**Options:**")
                for opt in question["options"]:
                    st.markdown(f"- {opt}")
            
            elif question["type"] == "likert_scale":
                st.write(f"**Scale:** {question.get('scale_min', 1)} to {question.get('scale_max', 5)}")
                st.write("**Labels:**")
                for j, label in enumerate(question.get("scale_labels", [])):
                    st.markdown(f"- {question.get('scale_min', 1) + j}: {label}")
            
            col1, col2 = st.columns(2)
            with col1:
                # Thêm unique_key để tránh trùng lặp
                unique_key = f"edit_{i}_{str(i)}_{question_index}"
                if st.button(f"Edit Question {i+1}", key=unique_key):
                    edit_question(i)
                    st.rerun()
            with col2:
                # Thêm unique_key để tránh trùng lặp
                unique_key = f"delete_{i}_{str(i)}_{question_index}"
                if st.button(f"Delete Question {i+1}", key=unique_key):
                    delete_question(i)
                    st.rerun()
