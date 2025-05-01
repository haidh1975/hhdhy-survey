import streamlit as st
import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_analysis import calculate_statistics
from utils.visualization import create_chart
from utils.advanced_analysis import calculate_cronbach_alpha, perform_efa, perform_regression, simple_cfa_evaluation

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
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Charts", "Statistics", "Comparisons", "Summary Table", "Response Breakdown"])
        
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
            # Summary Table - show variables, mean, and standard deviation
            st.subheader("Bảng Thống Kê Tóm Tắt")
            
            # Create a dataframe to hold summary statistics
            summary_data = []
            
            # Process each question to get statistics
            for i, question in enumerate(questions):
                question_id = question.get("id", str(i))
                question_text = question["question_text"]
                question_type = question["type"]
                
                # Check if column exists
                column_name = question_id
                if column_name not in df.columns:
                    column_name = f"q_{i}"
                    if column_name not in df.columns:
                        continue
                
                # Skip non-numeric columns or try to convert
                if df[column_name].dtype not in [np.int64, np.float64]:
                    # Try to convert to numeric if possible
                    try:
                        numeric_values = pd.to_numeric(df[column_name], errors='coerce')
                        if numeric_values.isna().all():  # If all values are NaN after conversion
                            continue
                        # Create temporary dataframe with numeric values for statistics calculation
                        temp_df = df.copy()
                        temp_df[column_name] = numeric_values
                    except:
                        continue
                else:
                    temp_df = df
                
                # Calculate statistics
                mean_value = temp_df[column_name].mean()
                std_value = temp_df[column_name].std()
                min_value = temp_df[column_name].min()
                max_value = temp_df[column_name].max()
                
                # Add to summary data
                summary_data.append({
                    "Biến số": question_text,
                    "Giá trị trung bình": f"{mean_value:.2f}",
                    "Độ lệch chuẩn": f"{std_value:.2f}",
                    "Giá trị nhỏ nhất": f"{min_value:.2f}",
                    "Giá trị lớn nhất": f"{max_value:.2f}"
                })
            
            # Create dataframe from summary data
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                
                # Option to download the summary table as CSV
                csv = summary_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Tải xuống bảng thống kê (CSV)",
                    data=csv,
                    file_name="survey_statistics_summary.csv",
                    mime="text/csv",
                )
            else:
                st.info("Không có biến số nào có thể tính toán thống kê.")
        
        with tab5:
            # Response breakdown - show raw counts and percentages
            st.subheader("Phân tích chi tiết dữ liệu")
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

        # Advanced Analysis Tab
        st.subheader("Phân tích nâng cao")
        
        # Quản lý nhóm biến cho phân tích nâng cao
        with st.expander("Quản lý nhóm biến cho phân tích", expanded=False):
            st.write("Tạo và quản lý các nhóm biến để sử dụng trong các phân tích nâng cao:")
            
            # Khởi tạo các nhóm biến trong session state nếu chưa có
            if "variable_groups" not in st.session_state:
                st.session_state.variable_groups = {}
            
            # Giao diện để tạo nhóm biến mới
            col1, col2 = st.columns([1, 3])
            
            with col1:
                new_group_name = st.text_input("Tên nhóm biến mới", key="new_group_name")
            
            with col2:
                new_group_vars = st.multiselect(
                    "Chọn các biến cho nhóm mới",
                    options=[q["column"] for q in numeric_questions],
                    format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                    key="new_group_vars"
                )
            
            # Nút để lưu nhóm biến mới
            if st.button("Lưu nhóm biến", key="save_var_group"):
                if new_group_name and new_group_vars:
                    st.session_state.variable_groups[new_group_name] = new_group_vars
                    st.success(f"Đã lưu nhóm biến '{new_group_name}' với {len(new_group_vars)} biến")
                else:
                    st.warning("Vui lòng nhập tên nhóm và chọn ít nhất một biến")
            
            # Hiển thị các nhóm biến hiện có
            if st.session_state.variable_groups:
                st.subheader("Các nhóm biến hiện có")
                
                for group_name, variables in st.session_state.variable_groups.items():
                    with st.expander(f"{group_name} ({len(variables)} biến)"):
                        # Hiển thị danh sách biến trong nhóm
                        for var in variables:
                            var_text = next((q["text"] for q in numeric_questions if q["column"] == var), var)
                            st.write(f"- {var_text}")
                        
                        # Nút để xóa nhóm biến
                        if st.button("Xóa nhóm này", key=f"delete_{group_name}"):
                            del st.session_state.variable_groups[group_name]
                            st.rerun()
        
        # Create tabs for different advanced analysis methods
        adv_tab1, adv_tab2, adv_tab3, adv_tab4, adv_tab5 = st.tabs([
            "Cronbach's Alpha", 
            "Phân tích nhân tố (EFA)", 
            "Hồi quy đa biến",
            "Phân tích nhân tố khẳng định (CFA)",
            "Mô hình cấu trúc (SEM)"
        ])
        
        # Find numeric questions for advanced analysis
        numeric_questions = []
        for i, question in enumerate(questions):
            question_id = question.get("id", str(i))
            column_name = question_id
            
            # Check if column exists
            if column_name not in df.columns:
                column_name = f"q_{i}"
                if column_name not in df.columns:
                    continue
            
            # Check if data is numeric or can be converted to numeric
            if df[column_name].dtype in [np.int64, np.float64]:
                numeric_questions.append({
                    "index": i,
                    "id": question_id,
                    "text": question["question_text"],
                    "column": column_name
                })
            else:
                # Try to convert to numeric
                try:
                    numeric_values = pd.to_numeric(df[column_name], errors='coerce')
                    if not numeric_values.isna().all():  # If not all values are NaN
                        numeric_questions.append({
                            "index": i,
                            "id": question_id,
                            "text": question["question_text"],
                            "column": column_name,
                            "needs_conversion": True
                        })
                except:
                    pass
        
        # Create a clean dataframe with only numeric columns for analysis
        numeric_df = pd.DataFrame()
        for q in numeric_questions:
            col_name = q["column"]
            if q.get("needs_conversion", False):
                numeric_df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            else:
                numeric_df[col_name] = df[col_name]
        
        # 1. Cronbach's Alpha Tab
        with adv_tab1:
            st.subheader("Phân tích độ tin cậy - Cronbach's Alpha")
            st.write("""
            Cronbach's Alpha là hệ số đo lường độ tin cậy nhất quán nội bộ của một tập hợp các biến. 
            Giá trị Alpha > 0.7 được coi là có độ tin cậy tốt.
            """)
            
            # Allow user to select a group of questions for reliability analysis
            if len(numeric_questions) >= 2:
                # Tùy chọn sử dụng nhóm biến đã lưu
                use_saved_group = False
                if st.session_state.variable_groups:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        use_saved_group = st.checkbox("Sử dụng nhóm biến đã lưu", key="use_saved_group_ca")
                    
                    if use_saved_group:
                        with col2:
                            selected_group = st.selectbox(
                                "Chọn nhóm biến",
                                options=list(st.session_state.variable_groups.keys()),
                                key="selected_group_ca"
                            )
                            selected_reliability_qs = st.session_state.variable_groups.get(selected_group, [])
                            
                            # Hiển thị danh sách biến trong nhóm đã chọn
                            if selected_reliability_qs:
                                with st.expander(f"Các biến trong nhóm '{selected_group}'"):
                                    for var in selected_reliability_qs:
                                        var_text = next((q["text"] for q in numeric_questions if q["column"] == var), var)
                                        st.write(f"- {var_text}")
                    else:
                        # Chọn biến thủ công nếu không sử dụng nhóm biến đã lưu
                        selected_reliability_qs = st.multiselect(
                            "Chọn các biến để phân tích độ tin cậy",
                            options=[q["column"] for q in numeric_questions],
                            format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                            default=[q["column"] for q in numeric_questions[:min(5, len(numeric_questions))]]
                        )
                        
                        # Tùy chọn lưu nhóm biến đã chọn
                        save_group = st.checkbox("Lưu nhóm biến này để tái sử dụng", key="save_group_ca")
                        if save_group:
                            group_name = st.text_input("Nhập tên nhóm biến", key="group_name_ca")
                            if st.button("Lưu lại", key="save_btn_ca"):
                                if group_name and selected_reliability_qs:
                                    st.session_state.variable_groups[group_name] = selected_reliability_qs
                                    st.success(f"Đã lưu nhóm biến '{group_name}' với {len(selected_reliability_qs)} biến")
                                else:
                                    st.warning("Vui lòng nhập tên nhóm và chọn ít nhất một biến")
                else:
                    # Không có nhóm biến nào đã lưu
                    selected_reliability_qs = st.multiselect(
                        "Chọn các biến để phân tích độ tin cậy",
                        options=[q["column"] for q in numeric_questions],
                        format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                        default=[q["column"] for q in numeric_questions[:min(5, len(numeric_questions))]]
                    )
                    
                    # Tùy chọn lưu nhóm biến đã chọn
                    save_group = st.checkbox("Lưu nhóm biến này để tái sử dụng", key="save_group_ca")
                    if save_group:
                        group_name = st.text_input("Nhập tên nhóm biến", key="group_name_ca")
                        if st.button("Lưu lại", key="save_btn_ca"):
                            if group_name and selected_reliability_qs:
                                st.session_state.variable_groups[group_name] = selected_reliability_qs
                                st.success(f"Đã lưu nhóm biến '{group_name}' với {len(selected_reliability_qs)} biến")
                            else:
                                st.warning("Vui lòng nhập tên nhóm và chọn ít nhất một biến")
                
                if selected_reliability_qs and len(selected_reliability_qs) >= 2:
                    # Perform Cronbach's Alpha analysis
                    reliability_results = calculate_cronbach_alpha(numeric_df, selected_reliability_qs)
                    
                    if reliability_results.get("success", False) and reliability_results.get("alpha") is not None:
                        # Display the results
                        alpha_value = reliability_results["alpha"]
                        alpha_color = "green" if alpha_value >= 0.7 else "orange" if alpha_value >= 0.6 else "red"
                        
                        st.markdown(f"""
                        ### Kết quả phân tích:
                        - **Hệ số Cronbach's Alpha**: <span style='color:{alpha_color}'>{alpha_value:.3f}</span>
                        - **Số lượng biến**: {reliability_results['n_items']}
                        - **Số lượng quan sát hợp lệ**: {reliability_results['n_cases']}
                        """, unsafe_allow_html=True)
                        
                        # Display item statistics
                        if "item_stats" in reliability_results:
                            st.subheader("Thống kê theo từng biến")
                            
                            item_stats_df = pd.DataFrame(reliability_results["item_stats"])
                            # Map column names back to question text
                            item_stats_df["item"] = item_stats_df["item"].apply(
                                lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col)
                            )
                            # Rename columns for display
                            item_stats_df.columns = ["Biến", "Tương quan biến-tổng", "Alpha nếu loại biến"]
                            
                            st.dataframe(item_stats_df)
                            
                            # Insights
                            low_correlations = item_stats_df[item_stats_df["Tương quan biến-tổng"] < 0.3]
                            if not low_correlations.empty:
                                st.warning(f"""
                                **Lưu ý**: Các biến sau có tương quan biến-tổng thấp (<0.3) và có thể xem xét loại bỏ:
                                {', '.join(low_correlations['Biến'].tolist())}
                                """)
                            
                            improve_items = item_stats_df[item_stats_df["Alpha nếu loại biến"] > alpha_value]
                            if not improve_items.empty:
                                st.info(f"""
                                **Gợi ý cải thiện**: Loại bỏ các biến sau có thể cải thiện độ tin cậy:
                                {', '.join(improve_items['Biến'].tolist())}
                                """)
                    else:
                        st.error(f"Không thể tính toán Cronbach's Alpha: {reliability_results.get('error', 'Lỗi không xác định')}")
                else:
                    st.info("Vui lòng chọn ít nhất 2 biến để tính toán Cronbach's Alpha.")
            else:
                st.warning("Cần ít nhất 2 biến số để thực hiện phân tích độ tin cậy.")
        
        # 2. Exploratory Factor Analysis (EFA) Tab
        with adv_tab2:
            st.subheader("Phân tích nhân tố khám phá (EFA)")
            st.write("""
            Phân tích nhân tố khám phá (EFA) giúp xác định cấu trúc tiềm ẩn giữa các biến và nhóm chúng thành các nhân tố.
            """)
            
            if len(numeric_questions) >= 3:
                # Tùy chọn sử dụng nhóm biến đã lưu
                use_saved_group = False
                if st.session_state.variable_groups:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        use_saved_group = st.checkbox("Sử dụng nhóm biến đã lưu", key="use_saved_group_efa")
                    
                    if use_saved_group:
                        with col2:
                            selected_group = st.selectbox(
                                "Chọn nhóm biến",
                                options=list(st.session_state.variable_groups.keys()),
                                key="selected_group_efa"
                            )
                            selected_efa_qs = st.session_state.variable_groups.get(selected_group, [])
                            
                            # Hiển thị danh sách biến trong nhóm đã chọn
                            if selected_efa_qs:
                                with st.expander(f"Các biến trong nhóm '{selected_group}'"):
                                    for var in selected_efa_qs:
                                        var_text = next((q["text"] for q in numeric_questions if q["column"] == var), var)
                                        st.write(f"- {var_text}")
                    else:
                        # Chọn biến thủ công nếu không sử dụng nhóm biến đã lưu
                        selected_efa_qs = st.multiselect(
                            "Chọn các biến để phân tích nhân tố",
                            options=[q["column"] for q in numeric_questions],
                            format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                            default=[q["column"] for q in numeric_questions[:min(5, len(numeric_questions))]]
                        )
                        
                        # Tùy chọn lưu nhóm biến đã chọn
                        save_group = st.checkbox("Lưu nhóm biến này để tái sử dụng", key="save_group_efa")
                        if save_group:
                            group_name = st.text_input("Nhập tên nhóm biến", key="group_name_efa")
                            if st.button("Lưu lại", key="save_btn_efa"):
                                if group_name and selected_efa_qs:
                                    st.session_state.variable_groups[group_name] = selected_efa_qs
                                    st.success(f"Đã lưu nhóm biến '{group_name}' với {len(selected_efa_qs)} biến")
                                else:
                                    st.warning("Vui lòng nhập tên nhóm và chọn ít nhất một biến")
                else:
                    # Không có nhóm biến nào đã lưu
                    selected_efa_qs = st.multiselect(
                        "Chọn các biến để phân tích nhân tố",
                        options=[q["column"] for q in numeric_questions],
                        format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                        default=[q["column"] for q in numeric_questions[:min(5, len(numeric_questions))]]
                    )
                    
                    # Tùy chọn lưu nhóm biến đã chọn
                    save_group = st.checkbox("Lưu nhóm biến này để tái sử dụng", key="save_group_efa")
                    if save_group:
                        group_name = st.text_input("Nhập tên nhóm biến", key="group_name_efa")
                        if st.button("Lưu lại", key="save_btn_efa"):
                            if group_name and selected_efa_qs:
                                st.session_state.variable_groups[group_name] = selected_efa_qs
                                st.success(f"Đã lưu nhóm biến '{group_name}' với {len(selected_efa_qs)} biến")
                            else:
                                st.warning("Vui lòng nhập tên nhóm và chọn ít nhất một biến")
                
                if selected_efa_qs and len(selected_efa_qs) >= 3:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        rotation_method = st.selectbox(
                            "Phương pháp xoay nhân tố",
                            options=["varimax", "promax", "oblimin", "quartimax"],
                            index=0
                        )
                    
                    with col2:
                        n_factors = st.number_input(
                            "Số lượng nhân tố (để trống để tự động xác định)",
                            min_value=0,
                            max_value=len(selected_efa_qs)-1,
                            value=0
                        )
                    
                    # Run EFA
                    n_factors_param = None if n_factors == 0 else n_factors
                    efa_results = perform_efa(
                        numeric_df, 
                        selected_efa_qs, 
                        n_factors=n_factors_param, 
                        rotation=rotation_method
                    )
                    
                    if efa_results.get("success", False):
                        # Display warnings if any
                        if efa_results.get("warning"):
                            st.warning(efa_results["warning"])
                        
                        # Show results
                        st.subheader("Kết quả phân tích nhân tố")
                        
                        # Display KMO and Bartlett's test
                        col1, col2 = st.columns(2)
                        with col1:
                            kmo = efa_results.get("kmo", 0)
                            kmo_color = "green" if kmo >= 0.7 else "orange" if kmo >= 0.5 else "red"
                            st.markdown(f"**Chỉ số KMO**: <span style='color:{kmo_color}'>{kmo:.3f}</span>", unsafe_allow_html=True)
                        
                        with col2:
                            p_value = efa_results.get("bartlett_p_value", 1)
                            p_color = "green" if p_value < 0.05 else "red"
                            st.markdown(f"**Bartlett's Test p-value**: <span style='color:{p_color}'>{p_value:.4f}</span>", unsafe_allow_html=True)
                        
                        # Display eigenvalues
                        eigenvalues = efa_results.get("eigenvalues", [])
                        if eigenvalues:
                            fig = px.line(
                                x=list(range(1, len(eigenvalues)+1)),
                                y=eigenvalues,
                                markers=True,
                                title="Scree Plot",
                                labels={"x": "Số nhân tố", "y": "Eigenvalue"}
                            )
                            fig.add_hline(y=1.0, line_dash="dash", line_color="red")
                            st.plotly_chart(fig, use_container_width=True, key="scree_plot")
                        
                        # Show variance explained
                        n_factors_found = efa_results.get("n_factors", 0)
                        explained_var = efa_results.get("explained_variance", [])
                        cumulative_var = efa_results.get("cumulative_variance", [])
                        
                        if explained_var and n_factors_found > 0:
                            var_df = pd.DataFrame({
                                "Nhân tố": [f"Nhân tố {i+1}" for i in range(n_factors_found)],
                                "Phương sai giải thích (%)": [v*100 for v in explained_var[:n_factors_found]],
                                "Phương sai tích lũy (%)": [v*100 for v in cumulative_var[:n_factors_found]]
                            })
                            
                            st.dataframe(var_df)
                            
                            last_cumulative = cumulative_var[n_factors_found-1] * 100
                            st.info(f"Các nhân tố đã trích xuất giải thích được **{last_cumulative:.1f}%** tổng phương sai của dữ liệu.")
                        
                        # Display factor loadings
                        st.subheader("Hệ số tải nhân tố")
                        
                        # Convert loadings dictionary to DataFrame
                        loadings = efa_results.get("loadings", {})
                        if loadings:
                            # Create a loading matrix dataframe
                            loadings_df = pd.DataFrame(loadings)
                            
                            # Map row indices (variable names) to question texts
                            loadings_df.index = [
                                next((q["text"] for q in numeric_questions if q["column"] == idx), idx)
                                for idx in loadings_df.index
                            ]
                            
                            # Format the dataframe with conditional formatting
                            def highlight_max(s):
                                is_max = s == s.abs().max()
                                return ['font-weight: bold' if v else '' for v in is_max]
                            
                            st.dataframe(loadings_df.style.format("{:.3f}").apply(highlight_max, axis=1))
                        
                        # Display factor groups
                        st.subheader("Phân nhóm biến theo nhân tố")
                        factor_groups = efa_results.get("factor_groups", {})
                        
                        for factor, variables in factor_groups.items():
                            with st.expander(f"{factor}"):
                                group_df = pd.DataFrame(variables)
                                # Map variable names to question texts
                                group_df["variable"] = group_df["variable"].apply(
                                    lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col)
                                )
                                group_df.columns = ["Biến", "Hệ số tải"]
                                st.dataframe(group_df.style.format({"Hệ số tải": "{:.3f}"}))
                    else:
                        st.error(f"Không thể thực hiện phân tích nhân tố: {efa_results.get('error', 'Lỗi không xác định')}")
                else:
                    st.info("Vui lòng chọn ít nhất 3 biến để thực hiện phân tích nhân tố.")
            else:
                st.warning("Cần ít nhất 3 biến số để thực hiện phân tích nhân tố.")
        
        # 3. Regression Analysis Tab
        with adv_tab3:
            st.subheader("Phân tích hồi quy đa biến")
            st.write("""
            Phân tích hồi quy giúp xác định mối quan hệ giữa một biến phụ thuộc và nhiều biến độc lập.
            """)
            
            if len(numeric_questions) >= 2:
                # Biến phụ thuộc (Y)
                dependent_var = st.selectbox(
                    "Chọn biến phụ thuộc (Y)",
                    options=[q["column"] for q in numeric_questions],
                    format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col)
                )
                
                # Biến độc lập (X) - cho phép sử dụng nhóm biến đã lưu
                st.subheader("Biến độc lập (X)")
                
                use_saved_group = False
                if st.session_state.variable_groups:
                    use_saved_group = st.checkbox("Sử dụng nhóm biến đã lưu làm biến độc lập", key="use_saved_group_reg")
                    
                    if use_saved_group:
                        selected_group = st.selectbox(
                            "Chọn nhóm biến",
                            options=list(st.session_state.variable_groups.keys()),
                            key="selected_group_reg"
                        )
                        # Lọc biến phụ thuộc ra khỏi các biến độc lập
                        independent_vars = [var for var in st.session_state.variable_groups.get(selected_group, []) 
                                         if var != dependent_var]
                        
                        # Hiển thị danh sách biến trong nhóm đã chọn
                        if independent_vars:
                            with st.expander(f"Các biến độc lập từ nhóm '{selected_group}'"):
                                for var in independent_vars:
                                    var_text = next((q["text"] for q in numeric_questions if q["column"] == var), var)
                                    st.write(f"- {var_text}")
                        else:
                            st.warning("Không có biến nào trong nhóm này có thể làm biến độc lập (loại trừ biến phụ thuộc)")
                    else:
                        # Chọn biến thủ công nếu không sử dụng nhóm biến đã lưu
                        independent_vars = st.multiselect(
                            "Chọn các biến độc lập (X)",
                            options=[q["column"] for q in numeric_questions if q["column"] != dependent_var],
                            format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                            default=[q["column"] for q in numeric_questions if q["column"] != dependent_var][:min(3, len(numeric_questions)-1)]
                        )
                        
                        # Tùy chọn lưu nhóm biến độc lập đã chọn
                        save_group = st.checkbox("Lưu nhóm biến này để tái sử dụng", key="save_group_reg")
                        if save_group:
                            group_name = st.text_input("Nhập tên nhóm biến", key="group_name_reg")
                            if st.button("Lưu lại", key="save_btn_reg"):
                                if group_name and independent_vars:
                                    st.session_state.variable_groups[group_name] = independent_vars
                                    st.success(f"Đã lưu nhóm biến '{group_name}' với {len(independent_vars)} biến")
                                else:
                                    st.warning("Vui lòng nhập tên nhóm và chọn ít nhất một biến")
                else:
                    # Không có nhóm biến nào đã lưu
                    independent_vars = st.multiselect(
                        "Chọn các biến độc lập (X)",
                        options=[q["column"] for q in numeric_questions if q["column"] != dependent_var],
                        format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                        default=[q["column"] for q in numeric_questions if q["column"] != dependent_var][:min(3, len(numeric_questions)-1)]
                    )
                    
                    # Tùy chọn lưu nhóm biến đã chọn
                    save_group = st.checkbox("Lưu nhóm biến này để tái sử dụng", key="save_group_reg")
                    if save_group:
                        group_name = st.text_input("Nhập tên nhóm biến", key="group_name_reg")
                        if st.button("Lưu lại", key="save_btn_reg"):
                            if group_name and independent_vars:
                                st.session_state.variable_groups[group_name] = independent_vars
                                st.success(f"Đã lưu nhóm biến '{group_name}' với {len(independent_vars)} biến")
                            else:
                                st.warning("Vui lòng nhập tên nhóm và chọn ít nhất một biến")
                
                if dependent_var and independent_vars:
                    # Run regression analysis
                    reg_results = perform_regression(numeric_df, dependent_var, independent_vars)
                    
                    if reg_results.get("success", False):
                        # Display model summary
                        st.subheader("Tóm tắt mô hình")
                        model_summary = reg_results["model_summary"]
                        
                        # Display R-squared and Adjusted R-squared
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            r2_color = "green" if model_summary["r_squared"] > 0.5 else "orange" if model_summary["r_squared"] > 0.3 else "red"
                            st.markdown(f"**R²**: <span style='color:{r2_color}'>{model_summary['r_squared']:.3f}</span>", unsafe_allow_html=True)
                        
                        with col2:
                            adj_r2_color = "green" if model_summary["adj_r_squared"] > 0.5 else "orange" if model_summary["adj_r_squared"] > 0.3 else "red"
                            st.markdown(f"**Adjusted R²**: <span style='color:{adj_r2_color}'>{model_summary['adj_r_squared']:.3f}</span>", unsafe_allow_html=True)
                        
                        with col3:
                            f_color = "green" if model_summary["f_pvalue"] < 0.05 else "red"
                            st.markdown(f"**F-statistic p-value**: <span style='color:{f_color}'>{model_summary['f_pvalue']:.4f}</span>", unsafe_allow_html=True)
                        
                        # Display regression equation
                        st.subheader("Phương trình hồi quy")
                        st.markdown(f"**{model_summary['equation']}**")
                        
                        # Display coefficients
                        st.subheader("Hệ số hồi quy")
                        variables = reg_results["variables"]
                        var_df = pd.DataFrame(variables)
                        
                        # Map variable names to question texts for display
                        var_df["variable"] = var_df["variable"].apply(
                            lambda v: v if v == "Hằng số" else next(
                                (q["text"] for q in numeric_questions if q["column"] == v), v
                            )
                        )
                        
                        # Rename columns for display
                        var_df.columns = [
                            "Biến", "Hệ số", "Độ lệch chuẩn", "t-value", "p-value", 
                            "Có ý nghĩa thống kê", "VIF" if "vif" in var_df.columns else None
                        ]
                        
                        # Filter out None columns
                        var_df = var_df.loc[:, var_df.columns.notnull()]
                        
                        # Add significance markers
                        var_df["Có ý nghĩa thống kê"] = var_df["p-value"].apply(
                            lambda p: "✓" if p < 0.05 else "✗"
                        )
                        
                        st.dataframe(var_df.style.format({
                            "Hệ số": "{:.3f}",
                            "Độ lệch chuẩn": "{:.3f}",
                            "t-value": "{:.3f}",
                            "p-value": "{:.4f}",
                            "VIF": "{:.2f}" if "VIF" in var_df.columns else None
                        }))
                        
                        # Display assumption tests
                        if "assumptions" in reg_results:
                            st.subheader("Kiểm định giả định")
                            assumptions = reg_results["assumptions"]
                            
                            # Multicollinearity
                            if "multicollinearity" in assumptions:
                                multicollinearity = assumptions["multicollinearity"]
                                multi_color = "red" if multicollinearity else "green"
                                st.markdown(f"**Đa cộng tuyến**: <span style='color:{multi_color}'>{'Có vấn đề (VIF > 10)' if multicollinearity else 'Không có vấn đề'}</span>", unsafe_allow_html=True)
                            
                            # Durbin-Watson test
                            if "durbin_watson" in assumptions:
                                dw = assumptions["durbin_watson"]
                                dw_color = "green" if 1.5 < dw < 2.5 else "orange" if (1 < dw <= 1.5) or (2.5 <= dw < 3) else "red"
                                st.markdown(f"**Durbin-Watson**: <span style='color:{dw_color}'>{dw:.3f}</span> (lý tưởng: 2.0)", unsafe_allow_html=True)
                    else:
                        st.error(f"Không thể thực hiện phân tích hồi quy: {reg_results.get('error', 'Lỗi không xác định')}")
                else:
                    st.info("Vui lòng chọn biến phụ thuộc và ít nhất một biến độc lập.")
            else:
                st.warning("Cần ít nhất 2 biến số để thực hiện phân tích hồi quy.")
        
        # 4. Confirmatory Factor Analysis (CFA) Tab
        with adv_tab4:
            st.subheader("Phân tích nhân tố khẳng định (CFA)")
            st.write("""
            Phân tích nhân tố khẳng định (CFA) kiểm định các mô hình lý thuyết về mối quan hệ giữa các biến quan sát và các nhân tố tiềm ẩn.
            """)
            
            st.info("""
            **Phân tích nhân tố khẳng định đơn giản**
            
            Chức năng này cung cấp đánh giá cơ bản cho mô hình CFA được xác định trước. Để phân tích CFA đầy đủ,
            bạn nên sử dụng phần mềm chuyên dụng như AMOS, Mplus, hoặc lavaan (R).
            """)
            
            if len(numeric_questions) >= 3:
                # Let users define factor structure
                st.subheader("Xác định cấu trúc nhân tố")
                
                # Allow users to add factors
                if "cfa_factors" not in st.session_state:
                    st.session_state.cfa_factors = {"Factor 1": []}
                
                # Display current factor structure
                factors_to_remove = []
                for factor in st.session_state.cfa_factors:
                    with st.expander(f"Nhân tố: {factor}", expanded=True):
                        # Allow renaming the factor
                        new_name = st.text_input(f"Tên nhân tố", value=factor, key=f"name_{factor}")
                        
                        # Select variables for this factor
                        selected_vars = st.multiselect(
                            "Chọn các biến quan sát",
                            options=[q["column"] for q in numeric_questions],
                            format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                            default=st.session_state.cfa_factors[factor],
                            key=f"vars_{factor}"
                        )
                        
                        # Update session state
                        if new_name != factor:
                            st.session_state.cfa_factors[new_name] = selected_vars
                            factors_to_remove.append(factor)
                        else:
                            st.session_state.cfa_factors[factor] = selected_vars
                        
                        # Option to remove factor
                        if st.button("Xóa nhân tố này", key=f"remove_{factor}"):
                            factors_to_remove.append(factor)
                
                # Remove factors marked for removal
                for factor in factors_to_remove:
                    if factor in st.session_state.cfa_factors:
                        del st.session_state.cfa_factors[factor]
                
                # Add new factor button
                if st.button("Thêm nhân tố mới"):
                    # Find next available factor number
                    factor_nums = [int(f.split()[-1]) for f in st.session_state.cfa_factors.keys() if f.startswith("Factor ")]
                    next_num = max(factor_nums) + 1 if factor_nums else 1
                    st.session_state.cfa_factors[f"Factor {next_num}"] = []
                    st.rerun()
                
                # Run CFA analysis button
                if st.button("Thực hiện phân tích CFA"):
                    # Clean empty factors
                    factor_structure = {k: v for k, v in st.session_state.cfa_factors.items() if v}
                    
                    if factor_structure and all(len(vars) >= 2 for vars in factor_structure.values()):
                        # Run CFA analysis
                        cfa_results = simple_cfa_evaluation(numeric_df, factor_structure)
                        
                        if cfa_results.get("success", False):
                            st.subheader("Kết quả đánh giá CFA")
                            
                            # Overall evaluation
                            st.markdown("### Đánh giá tổng thể mô hình")
                            overall = cfa_results.get("overall_evaluation", {})
                            
                            convergent = overall.get("convergent_validity", False)
                            discriminant = overall.get("discriminant_validity", False)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                conv_color = "green" if convergent else "red"
                                st.markdown(f"**Độ giá trị hội tụ**: <span style='color:{conv_color}'>{'Đạt' if convergent else 'Không đạt'}</span>", unsafe_allow_html=True)
                            
                            with col2:
                                disc_color = "green" if discriminant else "red"
                                st.markdown(f"**Độ giá trị phân biệt**: <span style='color:{disc_color}'>{'Đạt' if discriminant else 'Không đạt'}</span>", unsafe_allow_html=True)
                            
                            # Factor statistics
                            st.markdown("### Thống kê theo nhân tố")
                            factor_stats = cfa_results.get("factor_stats", {})
                            
                            for factor, stats in factor_stats.items():
                                with st.expander(f"Nhân tố: {factor}"):
                                    variables = stats.get("variables", [])
                                    var_texts = [next((q["text"] for q in numeric_questions if q["column"] == v), v) for v in variables]
                                    
                                    st.markdown(f"**Biến quan sát**: {', '.join(var_texts)}")
                                    
                                    # Display reliability
                                    reliability = stats.get("reliability")
                                    if reliability is not None:
                                        rel_color = "green" if reliability > 0.7 else "orange" if reliability > 0.6 else "red"
                                        st.markdown(f"**Độ tin cậy (Cronbach's Alpha)**: <span style='color:{rel_color}'>{reliability:.3f}</span>", unsafe_allow_html=True)
                                    
                                    # Display average correlation
                                    avg_corr = stats.get("avg_correlation")
                                    if avg_corr is not None:
                                        corr_color = "green" if avg_corr > 0.5 else "orange" if avg_corr > 0.3 else "red"
                                        st.markdown(f"**Tương quan trung bình**: <span style='color:{corr_color}'>{avg_corr:.3f}</span>", unsafe_allow_html=True)
                                    
                                    # Display cross-loadings
                                    cross_loadings = stats.get("cross_loadings", {})
                                    if cross_loadings:
                                        st.markdown("**Tương quan với các nhân tố khác**:")
                                        for other_factor, cross_loading in cross_loadings.items():
                                            if cross_loading is not None:
                                                cross_color = "red" if cross_loading > 0.3 else "green"
                                                st.markdown(f"- {other_factor}: <span style='color:{cross_color}'>{cross_loading:.3f}</span>", unsafe_allow_html=True)
                        else:
                            st.error(f"Không thể thực hiện phân tích CFA: {cfa_results.get('error', 'Lỗi không xác định')}")
                    else:
                        st.warning("Mỗi nhân tố cần ít nhất 2 biến quan sát để thực hiện phân tích CFA.")
            else:
                st.warning("Cần ít nhất 3 biến số để thực hiện phân tích CFA.")
        
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
            
        # 5. Structural Equation Modeling (SEM) Tab
        with adv_tab5:
            st.subheader("Mô hình cấu trúc (SEM)")
            st.write("""
            Mô hình phương trình cấu trúc (SEM) cho phép kiểm tra mối quan hệ phức tạp giữa các biến quan sát và các biến tiềm ẩn.
            """)
            
            st.info("""
            **Lưu ý về mô hình SEM**
            
            Phân tích SEM đầy đủ đòi hỏi phần mềm chuyên dụng như AMOS, Mplus, hoặc lavaan (R).
            Chức năng này hỗ trợ quản lý cấu trúc mô hình và các biến trong phân tích SEM.
            """)
            
            # Tạo giao diện định nghĩa mô hình SEM
            st.subheader("Định nghĩa mô hình SEM")
            
            # Khởi tạo mô hình SEM nếu chưa có
            if "sem_model" not in st.session_state:
                st.session_state.sem_model = {
                    "latent_variables": {},
                    "paths": []
                }
            
            # Định nghĩa biến tiềm ẩn (latent variables) từ các nhóm biến
            with st.expander("Định nghĩa biến tiềm ẩn (Latent Variables)", expanded=True):
                st.write("Các biến tiềm ẩn được tạo từ nhiều biến quan sát.")
                
                # Tùy chọn sử dụng nhóm biến hoặc nhập mới
                if st.session_state.variable_groups:
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        latent_name = st.text_input("Tên biến tiềm ẩn", key="latent_name")
                    
                    with col2:
                        use_saved_group = st.checkbox("Sử dụng nhóm biến đã lưu", key="use_saved_group_sem")
                        
                        if use_saved_group:
                            selected_group = st.selectbox(
                                "Chọn nhóm biến",
                                options=list(st.session_state.variable_groups.keys()),
                                key="selected_group_sem"
                            )
                            manifest_vars = st.session_state.variable_groups.get(selected_group, [])
                        else:
                            # Chọn biến thủ công
                            manifest_vars = st.multiselect(
                                "Chọn các biến quan sát",
                                options=[q["column"] for q in numeric_questions],
                                format_func=lambda col: next((q["text"] for q in numeric_questions if q["column"] == col), col),
                                key="manifest_vars_sem"
                            )
                    
                    # Nút để thêm biến tiềm ẩn mới
                    if st.button("Thêm biến tiềm ẩn", key="add_latent_btn"):
                        if latent_name and manifest_vars:
                            st.session_state.sem_model["latent_variables"][latent_name] = manifest_vars
                            st.success(f"Đã thêm biến tiềm ẩn '{latent_name}' với {len(manifest_vars)} biến quan sát")
                            # Reset fields
                            st.session_state.latent_name = ""
                            if not use_saved_group:
                                st.session_state.manifest_vars_sem = []
                        else:
                            st.warning("Vui lòng nhập tên biến tiềm ẩn và chọn ít nhất một biến quan sát")
                    
                    # Hiển thị các biến tiềm ẩn đã định nghĩa
                    if st.session_state.sem_model["latent_variables"]:
                        st.subheader("Biến tiềm ẩn đã định nghĩa")
                        
                        latent_to_remove = None
                        for latent, vars in st.session_state.sem_model["latent_variables"].items():
                            with st.expander(f"{latent} ({len(vars)} biến)"):
                                # Hiển thị danh sách biến
                                for var in vars:
                                    var_text = next((q["text"] for q in numeric_questions if q["column"] == var), var)
                                    st.write(f"- {var_text}")
                                
                                # Nút xóa biến tiềm ẩn
                                if st.button("Xóa biến tiềm ẩn này", key=f"remove_{latent}"):
                                    latent_to_remove = latent
                        
                        # Xóa biến tiềm ẩn nếu được yêu cầu
                        if latent_to_remove:
                            del st.session_state.sem_model["latent_variables"][latent_to_remove]
                            # Cũng xóa các đường dẫn liên quan
                            st.session_state.sem_model["paths"] = [
                                path for path in st.session_state.sem_model["paths"] 
                                if path["from"] != latent_to_remove and path["to"] != latent_to_remove
                            ]
                            st.rerun()
                        
                        # Định nghĩa đường dẫn (paths) giữa các biến
                        st.subheader("Định nghĩa mối quan hệ (Paths)")
                        
                        col1, col2, col3 = st.columns([2, 1, 2])
                        
                        with col1:
                            from_var = st.selectbox(
                                "Từ",
                                options=list(st.session_state.sem_model["latent_variables"].keys()),
                                key="from_var"
                            )
                        
                        with col2:
                            relationship = st.selectbox(
                                "Quan hệ",
                                options=["→", "↔"],
                                key="relationship"
                            )
                        
                        with col3:
                            to_var = st.selectbox(
                                "Đến",
                                options=list(st.session_state.sem_model["latent_variables"].keys()),
                                key="to_var"
                            )
                        
                        # Nút thêm đường dẫn
                        if st.button("Thêm mối quan hệ", key="add_path_btn"):
                            if from_var != to_var or relationship == "↔":
                                # Kiểm tra trùng lặp
                                path_exists = any(
                                    (p["from"] == from_var and p["to"] == to_var and p["type"] == relationship) or
                                    (relationship == "↔" and p["from"] == to_var and p["to"] == from_var and p["type"] == "↔")
                                    for p in st.session_state.sem_model["paths"]
                                )
                                
                                if not path_exists:
                                    st.session_state.sem_model["paths"].append({
                                        "from": from_var,
                                        "to": to_var,
                                        "type": relationship
                                    })
                                    st.success(f"Đã thêm mối quan hệ: {from_var} {relationship} {to_var}")
                                else:
                                    st.warning("Mối quan hệ này đã tồn tại")
                            else:
                                st.warning("Không thể tạo mối quan hệ một chiều từ biến đến chính nó")
                        
                        # Hiển thị các đường dẫn đã định nghĩa
                        if st.session_state.sem_model["paths"]:
                            st.subheader("Mối quan hệ đã định nghĩa")
                            
                            for i, path in enumerate(st.session_state.sem_model["paths"]):
                                st.write(f"{i+1}. {path['from']} {path['type']} {path['to']}")
                            
                            # Nút xóa tất cả đường dẫn
                            if st.button("Xóa tất cả mối quan hệ", key="clear_paths"):
                                st.session_state.sem_model["paths"] = []
                                st.rerun()
                        
                        # Hiển thị mô hình dưới dạng mã lập trình (cho lavaan)
                        st.subheader("Mã mô hình SEM (định dạng lavaan)")
                        
                        # Tạo mã cho mô hình đo lường (measurement model)
                        measurement_code = []
                        for latent, vars in st.session_state.sem_model["latent_variables"].items():
                            var_names = " + ".join(vars)
                            measurement_code.append(f"{latent} =~ {var_names}")
                        
                        # Tạo mã cho mô hình cấu trúc (structural model)
                        structural_code = []
                        for path in st.session_state.sem_model["paths"]:
                            if path["type"] == "→":
                                structural_code.append(f"{path['to']} ~ {path['from']}")
                            else:  # "↔"
                                structural_code.append(f"{path['from']} ~~ {path['to']}")
                        
                        # Gộp tất cả mã lại
                        model_code = "\n".join(measurement_code + structural_code)
                        
                        # Hiển thị mã
                        st.code(model_code, language="r")
                        
                        # Tùy chọn xuất mô hình
                        st.download_button(
                            label="Tải xuống mã mô hình",
                            data=model_code,
                            file_name="sem_model.txt",
                            mime="text/plain"
                        )
                else:
                    st.warning("Hãy tạo ít nhất một nhóm biến trước để định nghĩa biến tiềm ẩn.")
