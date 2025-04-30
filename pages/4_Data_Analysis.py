import streamlit as st
import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_analysis import calculate_statistics
from utils.visualization import create_chart

st.set_page_config(
    page_title="Data Analysis",
    page_icon="📈",
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

st.title("Survey Data Analysis")

if not st.session_state.surveys:
    st.info("No surveys created yet. Go to the 'Create Survey' page to create your first survey.")
else:
    # Survey selection
    selected_survey_id = st.selectbox(
        "Select a survey to analyze",
        options=list(st.session_state.surveys.keys()),
        format_func=lambda x: st.session_state.surveys[x]["title"]
    )
    
    selected_survey = st.session_state.surveys[selected_survey_id]
    survey_responses = st.session_state.responses.get(selected_survey_id, [])
    
    st.subheader(f"Analysis for: {selected_survey['title']}")
    
    if not survey_responses:
        st.info("No responses received for this survey yet.")
    else:
        # Convert responses to DataFrame
        df = pd.DataFrame(survey_responses)
        
        # Overview metrics
        st.subheader("Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Responses", len(survey_responses))
        
        # Add completion time if available
        if "start_time" in df.columns and "end_time" in df.columns:
            try:
                df["start_time"] = pd.to_datetime(df["start_time"])
                df["end_time"] = pd.to_datetime(df["end_time"])
                df["completion_time"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 60  # in minutes
                
                with col2:
                    avg_time = df["completion_time"].mean()
                    st.metric("Avg. Completion Time", f"{avg_time:.1f} min")
                
                with col3:
                    median_time = df["completion_time"].median()
                    st.metric("Median Completion Time", f"{median_time:.1f} min")
            except:
                pass
        
        # Question analysis
        st.subheader("Question Analysis")
        
        # Create tabs for different visualization methods
        tab1, tab2, tab3, tab4 = st.tabs(["Charts", "Statistics", "Comparisons", "Response Breakdown"])
        
        with tab1:
            # Select questions to visualize
            questions = selected_survey["questions"]
            
            question_ids = []
            question_texts = []
            question_types = []
            
            for i, question in enumerate(questions):
                question_id = question.get("id", str(i))
                question_ids.append(question_id)
                question_texts.append(question["question_text"])
                question_types.append(question["type"])
            
            question_df = pd.DataFrame({
                "id": question_ids,
                "text": question_texts,
                "type": question_types
            })
            
            # Allow selecting multiple questions to compare
            selected_questions = st.multiselect(
                "Select questions to visualize",
                options=question_df.index.tolist(),
                format_func=lambda i: question_df.loc[i, "text"],
                default=[0] if len(question_df) > 0 else []
            )
            
            if selected_questions:
                for q_index in selected_questions:
                    q_id = question_df.loc[q_index, "id"]
                    q_text = question_df.loc[q_index, "text"]
                    q_type = question_df.loc[q_index, "type"]
                    
                    st.markdown(f"### {q_text}")
                    
                    # Check if the column exists in the dataframe
                    column_name = q_id
                    if column_name not in df.columns:
                        # Try with index prefixed
                        column_name = f"q_{q_index}"
                        if column_name not in df.columns:
                            st.warning(f"No data found for this question (looking for columns: {q_id}, {column_name})")
                            continue
                    
                    # Create appropriate visualization based on question type
                    if q_type in ["multiple_choice", "dropdown", "checkbox"]:
                        # Handle multiple selection questions (checkbox)
                        if q_type == "checkbox":
                            # For checkbox responses (lists), explode the data
                            if isinstance(df[column_name].iloc[0], list):
                                exploded = df[column_name].explode()
                                value_counts = exploded.value_counts().reset_index()
                                value_counts.columns = ["option", "count"]
                                
                                # Create bar chart
                                fig = px.bar(
                                    value_counts,
                                    x="option",
                                    y="count",
                                    title=f"Responses for: {q_text}",
                                    labels={"option": "Option", "count": "Count"}
                                )
                                st.plotly_chart(fig, use_container_width=True, key="chart_1")
                                
                                # Show percentage
                                total_responses = len(df)
                                value_counts["percentage"] = (value_counts["count"] / total_responses) * 100
                                value_counts["percentage"] = value_counts["percentage"].round(1)
                                value_counts["display"] = value_counts.apply(lambda x: f"{x['option']}: {x['count']} ({x['percentage']}%)", axis=1)
                                
                                st.table(value_counts[["option", "count", "percentage"]])
                        else:
                            # For single selection questions
                            value_counts = df[column_name].value_counts().reset_index()
                            value_counts.columns = ["option", "count"]
                            
                            # Create visualization
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                # Create bar chart
                                fig = px.bar(
                                    value_counts,
                                    x="option",
                                    y="count",
                                    title=f"Responses for: {q_text}",
                                    labels={"option": "Option", "count": "Count"}
                                )
                                st.plotly_chart(fig, use_container_width=True, key="chart_2")
                            
                            with col2:
                                # Create pie chart
                                fig = px.pie(
                                    value_counts,
                                    values="count",
                                    names="option",
                                    title="Distribution"
                                )
                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                st.plotly_chart(fig, use_container_width=True, key="chart_3")
                    
                    elif q_type == "likert_scale":
                        # For Likert scale questions
                        value_counts = df[column_name].value_counts().sort_index().reset_index()
                        value_counts.columns = ["rating", "count"]
                        
                        # Get scale information from the question
                        question = questions[q_index]
                        scale_min = question.get("scale_min", 1)
                        scale_max = question.get("scale_max", 5)
                        scale_labels = question.get("scale_labels", [])
                        
                        # Map numeric values to labels if available
                        if len(scale_labels) == (scale_max - scale_min + 1):
                            label_map = {i: label for i, label in zip(range(scale_min, scale_max + 1), scale_labels)}
                            value_counts["label"] = value_counts["rating"].map(label_map)
                        else:
                            value_counts["label"] = value_counts["rating"]
                        
                        # Create horizontal bar chart
                        fig = px.bar(
                            value_counts,
                            y="label" if "label" in value_counts.columns else "rating",
                            x="count",
                            title=f"Responses for: {q_text}",
                            labels={"count": "Count", "label": "Rating", "rating": "Rating"},
                            orientation='h'
                        )
                        st.plotly_chart(fig, use_container_width=True, key="chart_4")
                        
                        # Display statistics
                        if df[column_name].dtype in [np.int64, np.float64]:
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Average Rating", f"{df[column_name].mean():.2f}")
                            with col2:
                                st.metric("Median Rating", f"{df[column_name].median():.1f}")
                            with col3:
                                st.metric("Std. Deviation", f"{df[column_name].std():.2f}")
                            with col4:
                                st.metric("Most Common", df[column_name].mode()[0])
                    
                    elif q_type == "number":
                        # For numeric questions
                        if df[column_name].dtype in [np.int64, np.float64]:
                            # Display histogram
                            fig = px.histogram(
                                df,
                                x=column_name,
                                nbins=10,
                                title=f"Distribution for: {q_text}"
                            )
                            st.plotly_chart(fig, use_container_width=True, key="chart_5")
                            
                            # Display statistics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Average", f"{df[column_name].mean():.2f}")
                            with col2:
                                st.metric("Median", f"{df[column_name].median():.2f}")
                            with col3:
                                st.metric("Min", f"{df[column_name].min():.2f}")
                            with col4:
                                st.metric("Max", f"{df[column_name].max():.2f}")
                        else:
                            st.warning("This column contains non-numeric data.")
                    
                    elif q_type in ["text", "paragraph", "email", "phone"]:
                        # For text-based questions
                        responses = df[column_name].dropna().tolist()
                        
                        # Display word cloud or text summary
                        if responses:
                            st.write(f"**Total responses:** {len(responses)}")
                            
                            # Show a sample of responses
                            with st.expander("View text responses"):
                                for i, resp in enumerate(responses[:10]):  # Show first 10
                                    st.write(f"{i+1}. {resp}")
                                
                                if len(responses) > 10:
                                    st.write(f"... and {len(responses) - 10} more responses")
                        else:
                            st.write("No text responses received.")
                    
                    elif q_type == "date":
                        # For date questions
                        try:
                            date_series = pd.to_datetime(df[column_name])
                            
                            # Create date histogram
                            fig = px.histogram(
                                date_series,
                                nbins=20,
                                title=f"Date Distribution for: {q_text}"
                            )
                            st.plotly_chart(fig, use_container_width=True, key="chart_6")
                            
                            # Display statistics
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Earliest Date", date_series.min().strftime("%Y-%m-%d"))
                            with col2:
                                st.metric("Latest Date", date_series.max().strftime("%Y-%m-%d"))
                        except:
                            st.warning("Unable to parse dates from this column.")
            else:
                st.info("Select questions to visualize them.")
        
        with tab3:
            # Comparison tab - compare two questions
            st.subheader("Question Comparisons")
            st.write("Select two questions to compare their relationships and correlations.")
            
            # Get questions that can be compared (multiple choice, scale, number)
            comparable_questions = []
            
            for i, question in enumerate(questions):
                question_id = question.get("id", str(i))
                column_name = question_id
                
                # Check if column exists
                if column_name not in df.columns:
                    column_name = f"q_{i}"
                    if column_name not in df.columns:
                        continue
                
                # Only include certain question types that make sense to compare
                if question["type"] in ["multiple_choice", "dropdown", "likert_scale", "number"]:
                    comparable_questions.append({
                        "index": i,
                        "id": question_id,
                        "text": question["question_text"],
                        "type": question["type"],
                        "column": column_name
                    })
            
            if len(comparable_questions) >= 2:
                # Create two columns for selecting questions
                col1, col2 = st.columns(2)
                
                with col1:
                    q1_index = st.selectbox(
                        "First Question",
                        options=range(len(comparable_questions)),
                        format_func=lambda i: comparable_questions[i]["text"],
                        key="q1_compare"
                    )
                
                with col2:
                    q2_index = st.selectbox(
                        "Second Question",
                        options=range(len(comparable_questions)),
                        format_func=lambda i: comparable_questions[i]["text"],
                        key="q2_compare",
                        index=min(1, len(comparable_questions)-1)  # Default to second question
                    )
                
                # Get selected questions
                q1 = comparable_questions[q1_index]
                q2 = comparable_questions[q2_index]
                
                # Check if same question is selected twice
                if q1["index"] == q2["index"]:
                    st.warning("Please select two different questions to compare.")
                else:
                    st.subheader(f"Comparing: {q1['text']} vs {q2['text']}")
                    
                    # Determine chart type based on question types
                    q1_type = q1["type"]
                    q2_type = q2["type"]
                    
                    # Create different comparison visualizations based on question types
                    if q1_type in ["multiple_choice", "dropdown"] and q2_type in ["multiple_choice", "dropdown"]:
                        # Create contingency table
                        try:
                            # Create cross-tabulation
                            crosstab = pd.crosstab(
                                df[q1["column"]], 
                                df[q2["column"]], 
                                normalize='index'
                            ) * 100
                            
                            # Create heatmap
                            fig = px.imshow(
                                crosstab,
                                labels=dict(x=q2["text"], y=q1["text"], color="Percentage (%)"),
                                color_continuous_scale="Blues",
                                text_auto='.1f'
                            )
                            st.plotly_chart(fig, use_container_width=True, key="chart_7")
                            
                            st.write("The heatmap shows the percentage distribution of responses across both questions.")
                            
                            # Add the raw contingency table
                            raw_counts = pd.crosstab(df[q1["column"]], df[q2["column"]])
                            st.subheader("Response Counts")
                            st.dataframe(raw_counts)
                            
                        except Exception as e:
                            st.error(f"Error creating comparison: {e}")
                    
                    elif (q1_type in ["likert_scale", "number"] and q2_type in ["likert_scale", "number"]):
                        try:
                            # Check if data is numeric
                            if df[q1["column"]].dtype in [np.int64, np.float64] and df[q2["column"]].dtype in [np.int64, np.float64]:
                                # Create scatter plot
                                fig = px.scatter(
                                    df,
                                    x=q1["column"],
                                    y=q2["column"],
                                    trendline="ols",
                                    labels={q1["column"]: q1["text"], q2["column"]: q2["text"]},
                                    title=f"Correlation between {q1['text']} and {q2['text']}"
                                )
                                st.plotly_chart(fig, use_container_width=True, key="chart_8")
                                
                                # Calculate correlation coefficient
                                correlation = df[q1["column"]].corr(df[q2["column"]])
                                st.metric("Correlation Coefficient", f"{correlation:.2f}")
                                
                                if abs(correlation) < 0.3:
                                    st.write("There is a weak correlation between these two variables.")
                                elif abs(correlation) < 0.7:
                                    st.write("There is a moderate correlation between these two variables.")
                                else:
                                    st.write("There is a strong correlation between these two variables.")
                            else:
                                st.warning("One or both selected columns contain non-numeric data.")
                        except Exception as e:
                            st.error(f"Error creating comparison: {e}")
                    
                    elif (q1_type in ["multiple_choice", "dropdown"] and q2_type in ["likert_scale", "number"]):
                        try:
                            # Check if second question is numeric
                            if df[q2["column"]].dtype in [np.int64, np.float64]:
                                # Create box plot
                                fig = px.box(
                                    df,
                                    x=q1["column"],
                                    y=q2["column"],
                                    labels={q1["column"]: q1["text"], q2["column"]: q2["text"]},
                                    title=f"Distribution of {q2['text']} by {q1['text']}"
                                )
                                st.plotly_chart(fig, use_container_width=True, key="chart_9")
                                
                                # Add group statistics
                                grouped_stats = df.groupby(q1["column"])[q2["column"]].agg(['mean', 'median', 'std', 'count']).reset_index()
                                grouped_stats = grouped_stats.round(2)
                                st.subheader("Group Statistics")
                                st.dataframe(grouped_stats)
                            else:
                                st.warning("The second selected column contains non-numeric data.")
                        except Exception as e:
                            st.error(f"Error creating comparison: {e}")
                    
                    elif (q1_type in ["likert_scale", "number"] and q2_type in ["multiple_choice", "dropdown"]):
                        try:
                            # Check if first question is numeric
                            if df[q1["column"]].dtype in [np.int64, np.float64]:
                                # Create box plot
                                fig = px.box(
                                    df,
                                    x=q2["column"],
                                    y=q1["column"],
                                    labels={q2["column"]: q2["text"], q1["column"]: q1["text"]},
                                    title=f"Distribution of {q1['text']} by {q2['text']}"
                                )
                                st.plotly_chart(fig, use_container_width=True, key="chart_10")
                                
                                # Add group statistics
                                grouped_stats = df.groupby(q2["column"])[q1["column"]].agg(['mean', 'median', 'std', 'count']).reset_index()
                                grouped_stats = grouped_stats.round(2)
                                st.subheader("Group Statistics")
                                st.dataframe(grouped_stats)
                            else:
                                st.warning("The first selected column contains non-numeric data.")
                        except Exception as e:
                            st.error(f"Error creating comparison: {e}")
                    
                    else:
                        st.info("Comparison between these question types is not supported.")
            else:
                st.info("Need at least two comparable questions (multiple choice, scale, or number) to generate comparisons.")
                
        with tab2:
            # Calculating statistics for each question
            st.subheader("Question Statistics")
            
            stats_data = []
            
            for i, question in enumerate(questions):
                question_id = question.get("id", str(i))
                question_text = question["question_text"]
                question_type = question["type"]
                
                # Check if the column exists in the dataframe
                column_name = question_id
                if column_name not in df.columns:
                    # Try with index prefixed
                    column_name = f"q_{i}"
                    if column_name not in df.columns:
                        continue
                
                # Calculate statistics based on question type
                stats = calculate_statistics(df, column_name, question_type, question)
                
                if stats:
                    stats["Question"] = question_text
                    stats["Type"] = question_type
                    stats_data.append(stats)
            
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                # Reorder columns to have Question and Type first
                cols = ["Question", "Type"] + [col for col in stats_df.columns if col not in ["Question", "Type"]]
                stats_df = stats_df[cols]
                st.dataframe(stats_df, use_container_width=True)
            else:
                st.info("No statistical data available.")
        
        with tab4:
            # Response breakdown - show raw counts and percentages
            for i, question in enumerate(questions):
                question_id = question.get("id", str(i))
                question_text = question["question_text"]
                question_type = question["type"]
                
                # Check if the column exists in the dataframe
                column_name = question_id
                if column_name not in df.columns:
                    # Try with index prefixed
                    column_name = f"q_{i}"
                    if column_name not in df.columns:
                        continue
                
                st.markdown(f"### {question_text}")
                
                # Handle different question types
                if question_type in ["multiple_choice", "dropdown"]:
                    value_counts = df[column_name].value_counts()
                    total = len(df)
                    
                    # Create a dataframe with counts and percentages
                    breakdown_df = pd.DataFrame({
                        "Count": value_counts,
                        "Percentage": (value_counts / total * 100).round(1)
                    })
                    
                    st.dataframe(breakdown_df, use_container_width=True)
                
                elif question_type == "checkbox":
                    if isinstance(df[column_name].iloc[0], list):
                        exploded = df[column_name].explode()
                        value_counts = exploded.value_counts()
                        total = len(df)
                        
                        # Create a dataframe with counts and percentages
                        breakdown_df = pd.DataFrame({
                            "Count": value_counts,
                            "Percentage": (value_counts / total * 100).round(1)
                        })
                        
                        st.dataframe(breakdown_df, use_container_width=True)
                    else:
                        st.write("Unable to process checkbox data.")
                
                elif question_type == "likert_scale":
                    value_counts = df[column_name].value_counts().sort_index()
                    total = len(df)
                    
                    # Create a dataframe with counts and percentages
                    breakdown_df = pd.DataFrame({
                        "Count": value_counts,
                        "Percentage": (value_counts / total * 100).round(1)
                    })
                    
                    # Get scale information from the question
                    scale_min = question.get("scale_min", 1)
                    scale_max = question.get("scale_max", 5)
                    scale_labels = question.get("scale_labels", [])
                    
                    # Map numeric values to labels if available
                    if len(scale_labels) == (scale_max - scale_min + 1):
                        label_map = {i: f"{i} - {label}" for i, label in zip(range(scale_min, scale_max + 1), scale_labels)}
                        breakdown_df = breakdown_df.rename(index=label_map)
                    
                    st.dataframe(breakdown_df, use_container_width=True)
                
                elif question_type in ["text", "paragraph", "email", "phone"]:
                    # Count non-empty responses
                    response_count = df[column_name].notna().sum()
                    empty_count = len(df) - response_count
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Responses Provided", response_count)
                    with col2:
                        st.metric("Blank Responses", empty_count)
                
                elif question_type == "number":
                    if df[column_name].dtype in [np.int64, np.float64]:
                        # Create a frequency table
                        value_counts = df[column_name].value_counts().sort_index()
                        total = len(df)
                        
                        # Create a dataframe with counts and percentages
                        breakdown_df = pd.DataFrame({
                            "Count": value_counts,
                            "Percentage": (value_counts / total * 100).round(1)
                        })
                        
                        st.dataframe(breakdown_df, use_container_width=True)
                    else:
                        st.write("This column contains non-numeric data.")
                
                elif question_type == "date":
                    try:
                        date_series = pd.to_datetime(df[column_name])
                        
                        # Group by month or day depending on the date range
                        date_range = (date_series.max() - date_series.min()).days
                        
                        if date_range > 60:
                            # Group by month
                            date_counts = date_series.dt.to_period('M').value_counts().sort_index()
                            date_counts.index = date_counts.index.astype(str)
                        else:
                            # Group by day
                            date_counts = date_series.dt.date.value_counts().sort_index()
                        
                        total = len(df)
                        
                        # Create a dataframe with counts and percentages
                        breakdown_df = pd.DataFrame({
                            "Count": date_counts,
                            "Percentage": (date_counts / total * 100).round(1)
                        })
                        
                        st.dataframe(breakdown_df, use_container_width=True)
                    except:
                        st.write("Unable to parse dates from this column.")
                
                st.markdown("---")

        # Cross-question analysis
        st.subheader("Cross-Question Analysis")
        
        # First, identify questions suitable for comparison (categorical or numeric)
        suitable_questions = []
        for i, question in enumerate(questions):
            question_id = question.get("id", str(i))
            q_type = question["type"]
            
            # Check if the column exists in the dataframe
            column_name = question_id
            if column_name not in df.columns:
                # Try with index prefixed
                column_name = f"q_{i}"
                if column_name not in df.columns:
                    continue
            
            # Add to suitable questions if it's a type we can compare
            if q_type in ["multiple_choice", "dropdown", "checkbox", "likert_scale", "number"]:
                suitable_questions.append({
                    "id": i,
                    "column": column_name,
                    "text": question["question_text"],
                    "type": q_type
                })
        
        if len(suitable_questions) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                q1_index = st.selectbox(
                    "Select first question",
                    options=range(len(suitable_questions)),
                    format_func=lambda i: suitable_questions[i]["text"]
                )
            
            with col2:
                q2_index = st.selectbox(
                    "Select second question",
                    options=range(len(suitable_questions)),
                    format_func=lambda i: suitable_questions[i]["text"],
                    index=min(1, len(suitable_questions)-1)  # Default to second question
                )
            
            if q1_index != q2_index:
                q1 = suitable_questions[q1_index]
                q2 = suitable_questions[q2_index]
                
                st.subheader(f"Comparing '{q1['text']}' with '{q2['text']}'")
                
                # Check if both questions can be compared
                if q1["type"] in ["multiple_choice", "dropdown"] and q2["type"] in ["multiple_choice", "dropdown"]:
                    # Create a contingency table
                    contingency = pd.crosstab(
                        df[q1["column"]],
                        df[q2["column"]],
                        normalize='index',
                        margins=True
                    ) * 100
                    
                    # Display as heatmap
                    fig = px.imshow(
                        contingency.iloc[:-1, :-1],  # Remove the 'All' row and column
                        labels=dict(x=q2["text"], y=q1["text"], color="Percentage"),
                        x=contingency.columns[:-1],  # Remove the 'All' column
                        y=contingency.index[:-1],    # Remove the 'All' row
                        text_auto='.1f',
                        color_continuous_scale="Blues",
                        aspect="auto"
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True, key="chart_11")
                    
                    # Also show raw counts
                    st.subheader("Raw Counts")
                    raw_counts = pd.crosstab(df[q1["column"]], df[q2["column"]])
                    st.dataframe(raw_counts, use_container_width=True)
                
                elif q1["type"] in ["likert_scale", "number"] and q2["type"] in ["likert_scale", "number"]:
                    # Create a scatter plot
                    fig = px.scatter(
                        df,
                        x=q1["column"],
                        y=q2["column"],
                        labels={q1["column"]: q1["text"], q2["column"]: q2["text"]},
                        trendline="ols",
                        title=f"Correlation between {q1['text']} and {q2['text']}"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="chart_12")
                    
                    # Calculate correlation
                    correlation = df[q1["column"]].corr(df[q2["column"]])
                    st.metric("Correlation Coefficient", f"{correlation:.3f}")
                    
                    # Interpret correlation
                    if abs(correlation) < 0.3:
                        st.info("Weak correlation between these questions.")
                    elif abs(correlation) < 0.7:
                        st.info("Moderate correlation between these questions.")
                    else:
                        st.info("Strong correlation between these questions.")
                
                elif q1["type"] in ["likert_scale", "number"] and q2["type"] in ["multiple_choice", "dropdown"]:
                    # Box plot for numeric vs categorical
                    fig = px.box(
                        df,
                        x=q2["column"],
                        y=q1["column"],
                        labels={q1["column"]: q1["text"], q2["column"]: q2["text"]},
                        title=f"{q1['text']} by {q2['text']}"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="chart_13")
                    
                    # Show averages by category
                    grouped = df.groupby(q2["column"])[q1["column"]].agg(['mean', 'count']).reset_index()
                    grouped['mean'] = grouped['mean'].round(2)
                    st.dataframe(grouped, use_container_width=True)
                
                elif q1["type"] in ["multiple_choice", "dropdown"] and q2["type"] in ["likert_scale", "number"]:
                    # Box plot for categorical vs numeric (swapped axes)
                    fig = px.box(
                        df,
                        x=q1["column"],
                        y=q2["column"],
                        labels={q1["column"]: q1["text"], q2["column"]: q2["text"]},
                        title=f"{q2['text']} by {q1['text']}"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="chart_14")
                    
                    # Show averages by category
                    grouped = df.groupby(q1["column"])[q2["column"]].agg(['mean', 'count']).reset_index()
                    grouped['mean'] = grouped['mean'].round(2)
                    st.dataframe(grouped, use_container_width=True)
                
                else:
                    st.warning("These question types cannot be directly compared in a meaningful way.")
            else:
                st.info("Please select two different questions to compare.")
        else:
            st.info("Need at least two suitable questions (multiple choice, dropdown, likert, or numeric) for comparison.")
