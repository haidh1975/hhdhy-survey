import streamlit as st
import os
import json
import pandas as pd
import datetime

st.set_page_config(
    page_title="View Responses",
    page_icon="📊",
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

st.title("View Survey Responses")

if not st.session_state.surveys:
    st.info("No surveys created yet. Go to the 'Create Survey' page to create your first survey.")
else:
    # Survey selection
    selected_survey_id = st.selectbox(
        "Select a survey to view responses",
        options=list(st.session_state.surveys.keys()),
        format_func=lambda x: st.session_state.surveys[x]["title"]
    )
    
    selected_survey = st.session_state.surveys[selected_survey_id]
    survey_responses = st.session_state.responses.get(selected_survey_id, [])
    
    st.subheader(f"Survey: {selected_survey['title']}")
    st.write(f"Description: {selected_survey['description']}")
    
    # Response summary
    st.subheader("Response Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Responses", len(survey_responses))
    
    with col2:
        # Calculate the date of the most recent response
        if survey_responses:
            timestamps = [response.get("timestamp", "N/A") for response in survey_responses]
            timestamps = [ts for ts in timestamps if ts != "N/A"]
            latest_response = max(timestamps) if timestamps else "N/A"
            st.metric("Latest Response", latest_response)
        else:
            st.metric("Latest Response", "N/A")
    
    # Response data
    if survey_responses:
        st.subheader("Response Data")
        
        # Convert to DataFrame for easier display
        if survey_responses:
            df = pd.DataFrame(survey_responses)
            
            # Add functionality to filter responses
            st.subheader("Filter Responses")
            
            # Date filter if timestamp column exists
            if "timestamp" in df.columns:
                try:
                    # Convert timestamp strings to datetime
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    
                    # Get date range for filter
                    min_date = df["timestamp"].min().date()
                    max_date = df["timestamp"].max().date()
                    
                    # Date range selector
                    date_range = st.date_input(
                        "Filter by date range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    if len(date_range) == 2:
                        start_date, end_date = date_range
                        # Add a day to end_date to include the end date in the filter
                        end_date = datetime.datetime.combine(end_date, datetime.time.max)
                        mask = (df["timestamp"] >= pd.Timestamp(start_date)) & (df["timestamp"] <= pd.Timestamp(end_date))
                        df = df.loc[mask]
                except Exception as e:
                    st.error(f"Error processing date filters: {e}")
            
            # Display dataframe with all responses
            st.dataframe(df, use_container_width=True)
            
            # Display individual responses
            st.subheader("Individual Responses")
            for i, response in enumerate(df.to_dict("records")):
                with st.expander(f"Response #{i+1} - {response.get('timestamp', 'No timestamp')}"):
                    for key, value in response.items():
                        if key != "timestamp":
                            # Try to find the original question text
                            question_text = key
                            for question in selected_survey["questions"]:
                                if str(question.get("id", "")) == key or key.endswith(f"_{question.get('id', '')}"):
                                    question_text = question["question_text"]
                                    break
                            
                            st.markdown(f"**{question_text}**")
                            
                            # Format the response value based on type
                            if isinstance(value, list):
                                for item in value:
                                    st.markdown(f"- {item}")
                            else:
                                st.write(value)
    else:
        st.info("No responses received for this survey yet.")
        
        # Add a sample response form for testing
        if st.button("Add Test Response (for development only)"):
            sample_response = {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            
            # Create sample answers for each question
            for i, question in enumerate(selected_survey["questions"]):
                question_id = question.get("id", str(i))
                
                if question["type"] == "text" or question["type"] == "paragraph":
                    sample_response[question_id] = f"Sample text response for question {i+1}"
                
                elif question["type"] == "number":
                    sample_response[question_id] = i + 1
                
                elif question["type"] in ["multiple_choice", "dropdown"]:
                    if "options" in question and question["options"]:
                        sample_response[question_id] = question["options"][0]
                    else:
                        sample_response[question_id] = "No options available"
                
                elif question["type"] == "checkbox":
                    if "options" in question and question["options"]:
                        sample_response[question_id] = [question["options"][0]]
                        if len(question["options"]) > 1:
                            sample_response[question_id].append(question["options"][1])
                    else:
                        sample_response[question_id] = ["No options available"]
                
                elif question["type"] == "likert_scale":
                    sample_response[question_id] = question.get("scale_min", 1)
                
                elif question["type"] == "date":
                    sample_response[question_id] = datetime.datetime.now().strftime("%Y-%m-%d")
                
                elif question["type"] == "email":
                    sample_response[question_id] = "test@example.com"
                
                elif question["type"] == "phone":
                    sample_response[question_id] = "123-456-7890"
                
            # Add the sample response to the session state
            if selected_survey_id not in st.session_state.responses:
                st.session_state.responses[selected_survey_id] = []
            
            st.session_state.responses[selected_survey_id].append(sample_response)
            
            # Save updated responses
            with open('responses.json', 'w') as f:
                json.dump(st.session_state.responses, f, indent=2)
            
            st.success("Test response added. Refresh to see the results.")
            st.rerun()
