import streamlit as st
import json
import uuid
import datetime
import os

def save_surveys(surveys):
    """
    Save surveys to a JSON file.
    
    Args:
        surveys (dict): Dictionary of survey data
    """
    with open('surveys.json', 'w') as f:
        json.dump(surveys, f, indent=2)

def save_responses(responses):
    """
    Save survey responses to a JSON file.
    
    Args:
        responses (dict): Dictionary of response data
    """
    with open('responses.json', 'w') as f:
        json.dump(responses, f, indent=2)

def generate_survey_id():
    """
    Generate a unique survey ID.
    
    Returns:
        str: Unique survey ID
    """
    return str(uuid.uuid4())

def get_current_timestamp():
    """
    Get the current timestamp in a formatted string.
    
    Returns:
        str: Formatted timestamp string
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_surveys():
    """
    Load surveys from the JSON file.
    
    Returns:
        dict: Dictionary of survey data
    """
    if os.path.exists('surveys.json'):
        with open('surveys.json', 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def load_responses():
    """
    Load responses from the JSON file.
    
    Returns:
        dict: Dictionary of response data
    """
    if os.path.exists('responses.json'):
        with open('responses.json', 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def render_survey_form(survey, submit_action=None):
    """
    Render a survey form for user to fill out.
    
    Args:
        survey (dict): Survey data
        submit_action (function, optional): Function to call on form submit
        
    Returns:
        dict: Collected responses
    """
    st.title(survey["title"])
    st.write(survey["description"])
    
    responses = {}
    
    with st.form("survey_form"):
        for i, question in enumerate(survey["questions"]):
            st.write(f"**{i+1}. {question['question_text']}**")
            
            if question.get('required', False):
                st.markdown("*Required*")
            
            question_id = question.get("id", str(i))
            
            # Render different input types based on question type
            if question["type"] == "text":
                responses[question_id] = st.text_input(
                    "Your answer", 
                    key=f"q_{i}",
                    placeholder="Enter your answer here"
                )
            
            elif question["type"] == "paragraph":
                responses[question_id] = st.text_area(
                    "Your answer", 
                    key=f"q_{i}",
                    placeholder="Enter your answer here"
                )
            
            elif question["type"] == "number":
                responses[question_id] = st.number_input(
                    "Your answer", 
                    key=f"q_{i}"
                )
            
            elif question["type"] == "multiple_choice":
                if "options" in question and question["options"]:
                    responses[question_id] = st.radio(
                        "Select one option", 
                        options=question["options"],
                        key=f"q_{i}"
                    )
                else:
                    st.warning("No options defined for this question")
            
            elif question["type"] == "checkbox":
                if "options" in question and question["options"]:
                    responses[question_id] = st.multiselect(
                        "Select all that apply", 
                        options=question["options"],
                        key=f"q_{i}"
                    )
                else:
                    st.warning("No options defined for this question")
            
            elif question["type"] == "dropdown":
                if "options" in question and question["options"]:
                    responses[question_id] = st.selectbox(
                        "Select an option", 
                        options=question["options"],
                        key=f"q_{i}"
                    )
                else:
                    st.warning("No options defined for this question")
            
            elif question["type"] == "likert_scale":
                scale_min = question.get("scale_min", 1)
                scale_max = question.get("scale_max", 5)
                
                responses[question_id] = st.slider(
                    "Your rating",
                    min_value=scale_min,
                    max_value=scale_max,
                    value=scale_min,
                    key=f"q_{i}"
                )
                
                # Display scale labels if they exist
                if "scale_labels" in question:
                    scale_labels = question["scale_labels"]
                    if len(scale_labels) == (scale_max - scale_min + 1):
                        # Create columns for each label
                        cols = st.columns(len(scale_labels))
                        for j, (val, label) in enumerate(zip(range(scale_min, scale_max + 1), scale_labels)):
                            with cols[j]:
                                st.write(f"{val}: {label}")
            
            elif question["type"] == "date":
                responses[question_id] = st.date_input(
                    "Your answer",
                    key=f"q_{i}"
                )
            
            elif question["type"] == "email":
                responses[question_id] = st.text_input(
                    "Your email",
                    key=f"q_{i}",
                    placeholder="name@example.com"
                )
            
            elif question["type"] == "phone":
                responses[question_id] = st.text_input(
                    "Your phone number",
                    key=f"q_{i}",
                    placeholder="e.g., 123-456-7890"
                )
            
            st.write("---")
        
        # Add timestamp to responses
        responses["timestamp"] = get_current_timestamp()
        
        # Submit button
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            # Validate required fields
            missing_required = []
            for i, question in enumerate(survey["questions"]):
                question_id = question.get("id", str(i))
                if question.get('required', False):
                    if question_id not in responses or not responses[question_id]:
                        missing_required.append(question["question_text"])
            
            if missing_required:
                error_msg = "Please fill in the following required questions:\n"
                for q in missing_required:
                    error_msg += f"- {q}\n"
                st.error(error_msg)
                return None
            
            # Call submit action if provided
            if submit_action:
                submit_action(responses)
            
            return responses
    
    return None

def submit_survey_response(survey_id, response):
    """
    Submit a survey response vào database.

    Args:
        survey_id (str): UUID của khảo sát
        response (dict): Dữ liệu phản hồi

    Returns:
        bool: True nếu thành công
    """
    try:
        from utils.db_utils import save_response_db
        success, message = save_response_db(survey_id, response)
        if not success:
            st.error(f"Lỗi lưu phản hồi: {message}")
        return success
    except Exception as e:
        st.error(f"Lỗi lưu phản hồi: {e}")
        return False
