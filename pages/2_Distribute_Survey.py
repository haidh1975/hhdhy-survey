import streamlit as st
import os
import json
import pandas as pd
import base64
from io import StringIO
import csv

st.set_page_config(
    page_title="Distribute Survey",
    page_icon="🔗",
    layout="wide",
)

# Initialize session state variables if they don't exist
if 'surveys' not in st.session_state:
    if os.path.exists('surveys.json'):
        with open('surveys.json', 'r') as f:
            st.session_state.surveys = json.load(f)
    else:
        st.session_state.surveys = {}

if 'responses' not in st.session_state:
    if os.path.exists('responses.json'):
        with open('responses.json', 'r') as f:
            st.session_state.responses = json.load(f)
    else:
        st.session_state.responses = {}

if 'survey_link' not in st.session_state:
    st.session_state.survey_link = None

st.title("Distribute Survey")

if not st.session_state.surveys:
    st.info("No surveys created yet. Go to the 'Create Survey' page to create your first survey.")
else:
    # Survey selection
    selected_survey_id = st.selectbox(
        "Select a survey to distribute",
        options=list(st.session_state.surveys.keys()),
        format_func=lambda x: st.session_state.surveys[x]["title"]
    )
    
    selected_survey = st.session_state.surveys[selected_survey_id]
    
    st.subheader(f"Survey: {selected_survey['title']}")
    st.write(f"Description: {selected_survey['description']}")
    st.write(f"Questions: {len(selected_survey['questions'])}")
    
    # Response statistics
    response_count = len(st.session_state.responses.get(selected_survey_id, []))
    st.metric("Total Responses", response_count)
    
    # Survey link
    st.subheader("Survey Link")
    
    survey_url = f"{st.get_option('browser.serverAddress')}:5000/survey?id={selected_survey_id}"
    st.code(survey_url, language="text")
    
    st.markdown("#### Preview Survey")
    if st.button("Preview Survey"):
        st.session_state.preview_survey_id = selected_survey_id
        st.rerun()
    
    # Export responses
    st.subheader("Export Responses")
    
    if response_count > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export as CSV"):
                # Convert responses to a DataFrame
                responses = st.session_state.responses.get(selected_survey_id, [])
                df = pd.DataFrame(responses)
                
                # Convert DataFrame to CSV
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                
                # Encode as base64
                csv_str = csv_buffer.getvalue()
                b64 = base64.b64encode(csv_str.encode()).decode()
                
                # Create download link
                href = f'<a href="data:file/csv;base64,{b64}" download="{selected_survey["title"]}_responses.csv">Download CSV file</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            if st.button("Export as JSON"):
                # Get responses
                responses = st.session_state.responses.get(selected_survey_id, [])
                
                # Convert to JSON string
                json_str = json.dumps(responses, indent=2)
                
                # Encode as base64
                b64 = base64.b64encode(json_str.encode()).decode()
                
                # Create download link
                href = f'<a href="data:file/json;base64,{b64}" download="{selected_survey["title"]}_responses.json">Download JSON file</a>'
                st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("No responses to export yet.")

# Preview survey if requested
if hasattr(st.session_state, 'preview_survey_id'):
    survey_id = st.session_state.preview_survey_id
    survey = st.session_state.surveys[survey_id]
    
    st.markdown("---")
    st.subheader("Survey Preview")
    
    st.title(survey["title"])
    st.write(survey["description"])
    
    # Display each question in the survey
    for i, question in enumerate(survey["questions"]):
        st.markdown(f"### Question {i+1}: {question['question_text']}")
        if question.get('required', False):
            st.markdown("*Required*")
        
        # Display different input types based on question type
        if question["type"] == "text":
            st.text_input(f"Your answer", key=f"preview_{i}", disabled=True)
        
        elif question["type"] == "paragraph":
            st.text_area(f"Your answer", key=f"preview_{i}", disabled=True)
        
        elif question["type"] == "number":
            st.number_input(f"Your answer", key=f"preview_{i}", disabled=True)
        
        elif question["type"] == "multiple_choice":
            if "options" in question and question["options"]:
                st.radio("Select one option", options=question["options"], key=f"preview_{i}", disabled=True)
            else:
                st.warning("No options defined for this question")
        
        elif question["type"] == "checkbox":
            if "options" in question and question["options"]:
                st.multiselect("Select all that apply", options=question["options"], key=f"preview_{i}", disabled=True)
            else:
                st.warning("No options defined for this question")
        
        elif question["type"] == "dropdown":
            if "options" in question and question["options"]:
                st.selectbox("Select an option", options=question["options"], key=f"preview_{i}", disabled=True)
            else:
                st.warning("No options defined for this question")
        
        elif question["type"] == "likert_scale":
            scale_min = question.get("scale_min", 1)
            scale_max = question.get("scale_max", 5)
            options = list(range(scale_min, scale_max + 1))
            
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                st.slider(
                    "Your rating",
                    min_value=scale_min,
                    max_value=scale_max,
                    value=scale_min,
                    key=f"preview_{i}",
                    disabled=True
                )
                
                # Display scale labels if they exist
                if "scale_labels" in question and len(question["scale_labels"]) == len(options):
                    scale_cols = st.columns(len(options))
                    for j, (val, label) in enumerate(zip(options, question["scale_labels"])):
                        with scale_cols[j]:
                            st.write(f"{val}: {label}")
        
        elif question["type"] == "date":
            st.date_input(f"Your answer", key=f"preview_{i}", disabled=True)
        
        elif question["type"] == "email":
            st.text_input(f"Your email", key=f"preview_{i}", disabled=True)
        
        elif question["type"] == "phone":
            st.text_input(f"Your phone number", key=f"preview_{i}", disabled=True)
    
    # Submit button (disabled in preview)
    st.button("Submit", disabled=True)
    
    # Close preview button
    if st.button("Close Preview"):
        del st.session_state.preview_survey_id
        st.rerun()

# Create a route for the survey page
st.markdown("---")
st.subheader("How to Distribute Your Survey")
st.markdown("""
To distribute your survey, share the survey link with your respondents. They can access and complete the survey 
through their web browser.

#### Distribution Tips:
1. **Email**: Send the survey link directly to respondents via email
2. **Social Media**: Share the link on social media platforms
3. **QR Code**: Generate a QR code linking to your survey for print materials
4. **Embedded in Website**: Embed the survey in your website

Remember to regularly check the 'View Responses' page to monitor incoming responses.
""")
