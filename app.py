import streamlit as st
import pandas as pd
import os
import json

# Set page configuration
st.set_page_config(
    page_title="Survey Application",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
st.title("Survey Application")

# Dashboard summary
st.header("Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total Surveys", value=len(st.session_state.surveys))

with col2:
    total_responses = sum(len(responses) for responses in st.session_state.responses.values())
    st.metric(label="Total Responses", value=total_responses)

with col3:
    avg_responses = total_responses / len(st.session_state.surveys) if st.session_state.surveys else 0
    st.metric(label="Average Responses per Survey", value=f"{avg_responses:.1f}")

# Recent surveys section
st.subheader("Recent Surveys")

if st.session_state.surveys:
    # Convert surveys to DataFrame for display
    survey_data = []
    for survey_id, survey in st.session_state.surveys.items():
        response_count = len(st.session_state.responses.get(survey_id, []))
        survey_data.append({
            "Survey ID": survey_id,
            "Title": survey["title"],
            "Created Date": survey.get("created_date", "N/A"),
            "Questions": len(survey["questions"]),
            "Responses": response_count
        })
    
    survey_df = pd.DataFrame(survey_data)
    st.dataframe(survey_df, use_container_width=True)
else:
    st.info("No surveys created yet. Go to the 'Create Survey' page to get started.")

# Getting started guide
st.subheader("Getting Started")
st.markdown("""
To use this application effectively:

1. **Create a Survey**: Go to the 'Create Survey' page to design your survey with various question types.
2. **Distribute Survey**: Share your survey via a unique link from the 'Distribute Survey' page.
3. **Answer Survey**: Complete a survey or share it with others to get responses.
4. **View Responses**: Check all responses received for your surveys on the 'View Responses' page.
5. **Analyze Data**: Go to the 'Data Analysis' page to visualize and analyze your survey data.

Use the navigation menu on the left to access these features.
""")

# Quick action buttons
st.subheader("Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ Create New Survey"):
        st.switch_page("pages/1_Create_Survey.py")

with col2:
    if st.button("📝 Answer a Survey"):
        st.switch_page("pages/5_Answer_Survey.py")

with col3:
    if st.button("📊 View Analysis"):
        st.switch_page("pages/4_Data_Analysis.py")

# Footer
st.markdown("---")
st.markdown("📊 Survey Application - A tool for form creation, data collection, and statistical analysis")
