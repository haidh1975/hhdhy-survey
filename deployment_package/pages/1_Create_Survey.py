import streamlit as st
import json
import uuid
import datetime
import os
from utils.survey_utils import save_surveys

st.set_page_config(
    page_title="Create Survey",
    page_icon="📝",
    layout="wide",
)

# Initialize session state variables if they don't exist
if 'surveys' not in st.session_state:
    if os.path.exists('surveys.json'):
        with open('surveys.json', 'r') as f:
            st.session_state.surveys = json.load(f)
    else:
        st.session_state.surveys = {}

if 'current_survey' not in st.session_state:
    st.session_state.current_survey = {
        "title": "",
        "description": "",
        "questions": []
    }
elif st.session_state.current_survey is None:
    st.session_state.current_survey = {
        "title": "",
        "description": "",
        "questions": []
    }

if 'current_survey_id' not in st.session_state:
    st.session_state.current_survey_id = None

if 'editing_question_index' not in st.session_state:
    st.session_state.editing_question_index = -1

st.title("Create Survey")

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
        st.error("Please provide a survey title.")
        return
    
    if not st.session_state.current_survey["questions"]:
        st.error("Please add at least one question to your survey.")
        return
    
    # Generate a new ID if not editing an existing survey
    if st.session_state.current_survey_id is None:
        survey_id = str(uuid.uuid4())
        st.session_state.current_survey_id = survey_id
    else:
        survey_id = st.session_state.current_survey_id
    
    # Add creation date
    st.session_state.current_survey["created_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save the survey
    st.session_state.surveys[survey_id] = st.session_state.current_survey
    save_surveys(st.session_state.surveys)
    
    st.success(f"Survey '{st.session_state.current_survey['title']}' saved successfully!")
    create_new_survey()

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
                for i, label in enumerate(question.get("scale_labels", [])):
                    st.markdown(f"- {question.get('scale_min', 1) + i}: {label}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Edit Question {i+1}", key=f"edit_{i}"):
                    edit_question(i)
                    st.rerun()
            with col2:
                if st.button(f"Delete Question {i+1}", key=f"delete_{i}"):
                    delete_question(i)
                    st.rerun()
