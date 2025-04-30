import streamlit as st
import os
import json
import datetime
from utils.survey_utils import render_survey_form, submit_survey_response, load_surveys

st.set_page_config(
    page_title="Answer Survey",
    page_icon="✅",
    layout="wide",
)

# Initialize session state variables if they don't exist
if 'surveys' not in st.session_state:
    if os.path.exists('surveys.json'):
        with open('surveys.json', 'r') as f:
            st.session_state.surveys = json.load(f)
    else:
        st.session_state.surveys = {}

# Get survey id from query params if available
params = st.query_params

# Title and introduction
st.title("Answer Survey")

# Choose survey to answer
if "survey" in params:
    survey_id = params.get("survey")
    if survey_id in st.session_state.surveys:
        st.session_state.active_survey_id = survey_id
    else:
        st.error("Survey not found. Please select a valid survey.")
        st.session_state.active_survey_id = None
else:
    # Allow user to select a survey from the list
    st.subheader("Select a Survey to Answer")
    
    if not st.session_state.surveys:
        st.info("No surveys available yet. Please ask the survey creator to share a survey with you.")
    else:
        survey_options = list(st.session_state.surveys.keys())
        selected_survey = st.selectbox(
            "Choose a survey",
            options=survey_options,
            format_func=lambda x: st.session_state.surveys[x]["title"],
            index=0 if survey_options else None
        )
        
        if selected_survey:
            st.session_state.active_survey_id = selected_survey
            
            # Option to generate a shareable link
            survey_url = f"{st.get_option('browser.serverAddress')}:5000/Answer_Survey?survey={selected_survey}"
            st.subheader("Share this survey")
            st.code(survey_url, language="text")
            
            # Create a button to copy the link
            st.markdown(f'''
            <input type="text" value="{survey_url}" id="survey_link" readonly style="width:100%;padding:8px;">
            <button onclick="copyLink()" style="margin-top:10px;">Copy Link</button>
            <script>
            function copyLink() {{
              var copyText = document.getElementById("survey_link");
              copyText.select();
              copyText.setSelectionRange(0, 99999);
              navigator.clipboard.writeText(copyText.value);
              alert("Link copied to clipboard!");
            }}
            </script>
            ''', unsafe_allow_html=True)

# Display the selected survey for answering
if hasattr(st.session_state, 'active_survey_id') and st.session_state.active_survey_id in st.session_state.surveys:
    survey_id = st.session_state.active_survey_id
    survey = st.session_state.surveys[survey_id]
    
    st.markdown("---")
    
    # Check if the user has already submitted a response
    if hasattr(st.session_state, f'submitted_{survey_id}') and st.session_state[f'submitted_{survey_id}']:
        st.success("Thank you for your response! Your answers have been recorded.")
        
        if st.button("Submit Another Response"):
            st.session_state[f'submitted_{survey_id}'] = False
            st.rerun()
    else:
        # Display the survey form
        st.header(survey["title"])
        st.write(survey["description"])
        
        # Function to handle survey submission
        def handle_submit(response):
            if submit_survey_response(survey_id, response):
                st.session_state[f'submitted_{survey_id}'] = True
                st.success("Thank you for your response! Your answers have been recorded.")
                st.balloons()
            else:
                st.error("There was an error submitting your response. Please try again.")
        
        # Create the form
        with st.form(key=f"survey_response_form_{survey_id}"):
            responses = {}
            
            # Render questions
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
                        responses[question_id] = "No options available"
                
                elif question["type"] == "checkbox":
                    if "options" in question and question["options"]:
                        responses[question_id] = st.multiselect(
                            "Select all that apply", 
                            options=question["options"],
                            key=f"q_{i}"
                        )
                    else:
                        st.warning("No options defined for this question")
                        responses[question_id] = []
                
                elif question["type"] == "dropdown":
                    if "options" in question and question["options"]:
                        responses[question_id] = st.selectbox(
                            "Select an option", 
                            options=question["options"],
                            key=f"q_{i}"
                        )
                    else:
                        st.warning("No options defined for this question")
                        responses[question_id] = "No options available"
                
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
            responses["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Submit button
            submitted = st.form_submit_button("Submit Response")
            
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
                else:
                    # Submit the response
                    if submit_survey_response(survey_id, responses):
                        st.session_state[f'submitted_{survey_id}'] = True
                        st.success("Thank you for your response! Your answers have been recorded.")
                        st.balloons()
                    else:
                        st.error("There was an error submitting your response. Please try again.")