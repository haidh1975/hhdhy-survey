import streamlit as st
import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
from utils.data_analysis import calculate_statistics
from utils.visualization import create_chart
from utils.advanced_analysis import (
    calculate_cronbach_alpha, perform_efa, perform_regression, simple_cfa_evaluation,
    calculate_correlation_matrix, calculate_descriptive_stats,
    perform_group_comparison, check_response_quality,
)
from utils.auth import require_auth, get_current_user
from utils.pdf_generator import generate_survey_report
from utils.db_utils import get_surveys_db
from utils.i18n import render_language_selector, t, get_lang

st.set_page_config(
    page_title="HHD-HY — Phân Tích Dữ Liệu / Data Analysis",
    page_icon="📈",
    layout="wide",
)

# Require authentication to access this page
require_auth()

render_language_selector()

# Load surveys from database
@st.cache_data(ttl=30)
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

# Load responses from database  
@st.cache_data(ttl=30)
def load_responses_from_db():
    """Load all responses from database"""
    from utils.db_utils import get_responses_db
    responses = {}
    surveys = get_surveys_db()
    
    for survey in surveys:
        survey_responses = get_responses_db(survey['uuid'])
        # Convert to format compatible with existing code
        responses[survey['uuid']] = [r['response_data'] for r in survey_responses]
    
    return responses

st.session_state.responses = load_responses_from_db()

_title_vi = "📈 Phân Tích Dữ Liệu Khảo Sát"
_title_en = "📈 Survey Data Analysis"
st.title(_title_vi if get_lang() == "vi" else _title_en)

_no_survey_vi = "Chưa có khảo sát nào. Hãy vào trang **Tạo Khảo Sát** để bắt đầu."
_no_survey_en = "No surveys yet. Go to **Create Survey** to get started."
if not st.session_state.surveys:
    st.info(_no_survey_vi if get_lang() == "vi" else _no_survey_en)
else:
    # Survey selection
    _sel_vi = "Chọn khảo sát để phân tích"
    _sel_en = "Select a survey to analyze"
    selected_survey_id = st.selectbox(
        _sel_vi if get_lang() == "vi" else _sel_en,
        options=list(st.session_state.surveys.keys()),
        format_func=lambda x: st.session_state.surveys[x]["title"]
    )

    selected_survey = st.session_state.surveys[selected_survey_id]
    survey_responses = st.session_state.responses.get(selected_survey_id, [])

    _for_vi = f"Phân tích: {selected_survey['title']}"
    _for_en = f"Analysis for: {selected_survey['title']}"
    st.subheader(_for_vi if get_lang() == "vi" else _for_en)

    _no_resp_vi = "Chưa có phản hồi nào cho khảo sát này."
    _no_resp_en = "No responses received for this survey yet."
    if not survey_responses:
        st.info(_no_resp_vi if get_lang() == "vi" else _no_resp_en)
    else:
        # Convert responses to DataFrame
        df = pd.DataFrame(survey_responses)

        # Overview metrics
        _overview_vi = "Tổng quan"
        _overview_en = "Overview"
        st.subheader(_overview_vi if get_lang() == "vi" else _overview_en)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            _tot_vi = "Tổng phản hồi"
            _tot_en = "Total Responses"
            st.metric(_tot_vi if get_lang() == "vi" else _tot_en, len(survey_responses))

        with col2:
            # Numeric questions count
            numeric_q_count = sum(
                1 for q in selected_survey.get("questions", [])
                if q["type"] in ["likert_scale", "number"]
            )
            _nq_vi = "Câu hỏi số"
            _nq_en = "Numeric Questions"
            st.metric(_nq_vi if get_lang() == "vi" else _nq_en, numeric_q_count)

        with col3:
            # Response completeness
            resp_cols = [c for c in df.columns if c != "timestamp"]
            if resp_cols:
                completeness = round(df[resp_cols].notna().values.mean() * 100, 1)
            else:
                completeness = 100.0
            _comp_vi = "Độ đầy đủ dữ liệu"
            _comp_en = "Data Completeness"
            st.metric(_comp_vi if get_lang() == "vi" else _comp_en, f"{completeness}%")
        
        # PDF Report Download Button
        with col4:
            st.markdown("### 📄 Xuất báo cáo")
            if st.button("📊 Tải báo cáo PDF", use_container_width=True):
                with st.spinner("Đang tạo báo cáo PDF..."):
                    try:
                        pdf_content = generate_survey_report(selected_survey_id)
                        if pdf_content:
                            # Create download button
                            st.download_button(
                                label="📥 Tải xuống báo cáo",
                                data=pdf_content,
                                file_name=f"bao_cao_khao_sat_{selected_survey_id[:8]}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("Báo cáo PDF đã được tạo thành công!")
                        else:
                            st.error("Không thể tạo báo cáo PDF. Vui lòng thử lại sau.")
                    except Exception as e:
                        st.error(f"Lỗi tạo báo cáo PDF: {str(e)}")
                        
            # Quick export options
            if st.button("📊 Xuất dữ liệu Excel", use_container_width=True):
                # Convert responses to Excel format
                try:
                    df_export = pd.DataFrame(survey_responses)
                    # Convert to Excel bytes
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df_export.to_excel(writer, sheet_name='Survey_Responses', index=False)
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Tải xuống Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"du_lieu_khao_sat_{selected_survey_id[:8]}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.success("File Excel đã sẵn sàng tải xuống!")
                except Exception as e:
                    st.error(f"Lỗi xuất Excel: {str(e)}")
        
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
        _qa_vi = "📊 Phân tích câu hỏi"
        _qa_en = "📊 Question Analysis"
        st.subheader(_qa_vi if get_lang() == "vi" else _qa_en)

        # Create tabs for different visualization methods
        _tab_labels = (
            ["📊 Biểu đồ", "📋 Thống kê", "🔀 So sánh", "📑 Bảng tóm tắt", "🔢 Phân tích chi tiết",
             "🔗 Ma trận tương quan", "🧪 Kiểm định nhóm"]
            if get_lang() == "vi" else
            ["📊 Charts", "📋 Statistics", "🔀 Comparisons", "📑 Summary Table", "🔢 Response Breakdown",
             "🔗 Correlation Matrix", "🧪 Group Tests"]
        )
        tab1, tab2, tab3, tab4, tab5, tab_corr, tab_group = st.tabs(_tab_labels)
        
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

            _sel_q_vi = "Chọn câu hỏi cần biểu đồ hoá"
            _sel_q_en = "Select questions to visualize"
            selected_questions = st.multiselect(
                _sel_q_vi if get_lang() == "vi" else _sel_q_en,
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
                            if len(df[column_name]) > 0 and isinstance(df[column_name].iloc[0], list):
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
                            value_counts["label"] = value_counts["rating"].map(label_map).fillna(value_counts["rating"])
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
                                mode_values = df[column_name].mode()
                                if len(mode_values) > 0:
                                    st.metric("Most Common", f"{mode_values.iloc[0]}")
                                else:
                                    st.metric("Most Common", "N/A")
                    
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
                                text_auto=True
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
                                if pd.notna(correlation):
                                    st.metric("Correlation Coefficient", f"{correlation:.2f}")
                                else:
                                    st.metric("Correlation Coefficient", "N/A")
                                
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
                        if pd.isna(numeric_values).all():  # If all values are NaN after conversion
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
                    if not pd.isna(numeric_values).all():  # If not all values are NaN
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
        _adv_labels = (
            ["📊 Thống kê mô tả", "🔑 Cronbach's Alpha",
             "🧩 Phân tích nhân tố (EFA)", "📈 Hồi quy đa biến",
             "✅ CFA", "🔗 Mô hình SEM"]
            if get_lang() == "vi" else
            ["📊 Descriptive Stats", "🔑 Cronbach's Alpha",
             "🧩 EFA", "📈 Regression",
             "✅ CFA", "🔗 SEM"]
        )
        adv_tab_desc, adv_tab1, adv_tab2, adv_tab3, adv_tab4, adv_tab5 = st.tabs(_adv_labels)
        
        # 0. Descriptive Statistics Tab
        with adv_tab_desc:
            _desc_title = "📊 Thống kê mô tả nâng cao" if get_lang() == "vi" else "📊 Advanced Descriptive Statistics"
            st.subheader(_desc_title)

            _desc_info = (
                "Bao gồm: mean, median, std, skewness, kurtosis, IQR, số outlier, và kiểm định chuẩn Shapiro-Wilk."
                if get_lang() == "vi" else
                "Includes: mean, median, std, skewness, kurtosis, IQR, outlier count, and Shapiro-Wilk normality test."
            )
            st.info(_desc_info)

            if numeric_questions:
                _desc_vars = "Chọn biến để mô tả" if get_lang() == "vi" else "Select variables to describe"
                desc_vars = st.multiselect(
                    _desc_vars,
                    options=[q["column"] for q in numeric_questions],
                    format_func=lambda c: next((q["text"] for q in numeric_questions if q["column"] == c), c),
                    default=[q["column"] for q in numeric_questions[:min(8, len(numeric_questions))]],
                    key="desc_vars_sel",
                )
                if desc_vars:
                    desc_result = calculate_descriptive_stats(numeric_df, desc_vars)
                    if desc_result.get("success"):
                        stats_list = desc_result["stats"]
                        label_map_d = {q["column"]: q["text"][:50] for q in numeric_questions}

                        if get_lang() == "vi":
                            col_labels = ["Biến", "N", "Mean", "Median", "Std", "Min", "Max",
                                          "Skewness", "Kurtosis", "Outliers", "Chuẩn? (p>0.05)"]
                        else:
                            col_labels = ["Variable", "N", "Mean", "Median", "Std", "Min", "Max",
                                          "Skewness", "Kurtosis", "Outliers", "Normal? (p>0.05)"]

                        rows = []
                        for s in stats_list:
                            rows.append([
                                label_map_d.get(s["column"], s["column"]),
                                s["n"],
                                round(s["mean"], 3),
                                round(s["median"], 3),
                                round(s["std"], 3),
                                round(s["min"], 3),
                                round(s["max"], 3),
                                round(s["skewness"], 3),
                                round(s["kurtosis"], 3),
                                s["n_outliers"],
                                "✅" if s["is_normal"] else "❌",
                            ])

                        desc_df = pd.DataFrame(rows, columns=col_labels)
                        st.dataframe(desc_df, use_container_width=True)

                        # Highlight variables with outliers
                        outlier_vars = [r[0] for r in rows if r[9] > 0]
                        non_normal_vars = [r[0] for r in rows if r[10] == "❌"]

                        if outlier_vars:
                            _out_warn = f"⚠️ Biến có outlier (IQR rule): {', '.join(outlier_vars[:5])}" \
                                        if get_lang() == "vi" else \
                                        f"⚠️ Variables with outliers (IQR rule): {', '.join(outlier_vars[:5])}"
                            st.warning(_out_warn)

                        if non_normal_vars:
                            _nn_info = f"📌 Phân phối không chuẩn (Shapiro-Wilk p<0.05): {', '.join(non_normal_vars[:5])}" \
                                       if get_lang() == "vi" else \
                                       f"📌 Non-normal distribution (Shapiro-Wilk p<0.05): {', '.join(non_normal_vars[:5])}"
                            st.info(_nn_info)

                        # Distribution chart for selected variable
                        if len(desc_vars) >= 1:
                            _hist_sel = "Chọn biến để xem phân phối" if get_lang() == "vi" else "Select variable to view distribution"
                            hist_var = st.selectbox(
                                _hist_sel,
                                options=desc_vars,
                                format_func=lambda c: label_map_d.get(c, c),
                                key="hist_var_sel",
                            )
                            fig_hist = go.Figure()
                            fig_hist.add_trace(go.Histogram(
                                x=numeric_df[hist_var].dropna(),
                                nbinsx=15,
                                marker_color="#0066cc",
                                opacity=0.8,
                                name=label_map_d.get(hist_var, hist_var),
                            ))
                            # Overlay normal curve
                            from scipy.stats import norm as _norm
                            _mu = numeric_df[hist_var].mean()
                            _sigma = numeric_df[hist_var].std()
                            _x_range = np.linspace(
                                numeric_df[hist_var].min(), numeric_df[hist_var].max(), 100
                            )
                            _bin_width = max(
                                (numeric_df[hist_var].max() - numeric_df[hist_var].min()) / 15, 1e-9
                            )
                            _y_norm = _norm.pdf(_x_range, _mu, _sigma) * \
                                      len(numeric_df[hist_var].dropna()) * _bin_width
                            fig_hist.add_trace(go.Scatter(
                                x=_x_range, y=_y_norm,
                                mode="lines",
                                line=dict(color="red", width=2, dash="dash"),
                                name="Normal curve",
                            ))
                            fig_hist.update_layout(
                                title=label_map_d.get(hist_var, hist_var),
                                xaxis_title="Value",
                                yaxis_title="Frequency",
                                height=320,
                                margin=dict(t=40, b=30),
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)
                    else:
                        st.error(desc_result.get("error", "Error"))
                else:
                    _info_desc = "Chọn ít nhất 1 biến." if get_lang() == "vi" else "Select at least 1 variable."
                    st.info(_info_desc)
            else:
                st.warning("Cần ít nhất 1 biến số." if get_lang() == "vi" else "Need at least 1 numeric variable.")

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
                        def map_variable_name(v):
                            if v == "Hằng số":
                                return v
                            for q in numeric_questions:
                                if q["column"] == v:
                                    return q["text"]
                            return v
                        
                        var_df["variable"] = var_df["variable"].apply(map_variable_name)
                        
                        # Rename columns for display
                        var_df.columns = [
                            "Biến", "Hệ số", "Độ lệch chuẩn", "t-value", "p-value", 
                            "Có ý nghĩa thống kê", "VIF" if "vif" in var_df.columns else None
                        ]
                        
                        # Filter out None columns
                        var_df = var_df.loc[:, var_df.columns.notnull()]
                        
                        # Add significance markers
                        if "p-value" in var_df.columns:
                            var_df["Có ý nghĩa thống kê"] = var_df["p-value"].apply(
                                lambda p: "✓" if p < 0.05 else "✗"
                            )
                        
                        # Format the dataframe
                        format_dict = {
                            "Hệ số": "{:.3f}",
                            "Độ lệch chuẩn": "{:.3f}",
                            "t-value": "{:.3f}",
                            "p-value": "{:.4f}"
                        }
                        if "VIF" in var_df.columns:
                            format_dict["VIF"] = "{:.2f}"
                        
                        st.dataframe(var_df.style.format(format_dict))
                        
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
        
        # ── Tab: Correlation Matrix ─────────────────────────────────────────────
        with tab_corr:
            _corr_title_vi = "🔗 Ma Trận Tương Quan"
            _corr_title_en = "🔗 Correlation Matrix"
            st.subheader(_corr_title_vi if get_lang() == "vi" else _corr_title_en)

            _corr_info_vi = """
Ma trận tương quan cho thấy mức độ tương quan tuyến tính giữa các biến số.
- |r| ≥ 0.7 → Tương quan mạnh
- 0.3 ≤ |r| < 0.7 → Tương quan trung bình
- |r| < 0.3 → Tương quan yếu
*Dấu * (p < 0.05) và ** (p < 0.01) chỉ mức ý nghĩa thống kê.*
"""
            _corr_info_en = """
The correlation matrix shows linear relationships between numeric variables.
- |r| ≥ 0.7 → Strong
- 0.3 ≤ |r| < 0.7 → Moderate
- |r| < 0.3 → Weak
*Significance: * (p < 0.05), ** (p < 0.01)*
"""
            st.markdown(_corr_info_vi if get_lang() == "vi" else _corr_info_en)

            if len(numeric_questions) >= 2:
                _method_vi = "Phương pháp tương quan"
                _method_en = "Correlation method"
                corr_method = st.radio(
                    _method_vi if get_lang() == "vi" else _method_en,
                    ["pearson", "spearman"],
                    horizontal=True,
                )

                _sel_vars_vi = "Chọn các biến để tính tương quan"
                _sel_vars_en = "Select variables for correlation"
                corr_vars = st.multiselect(
                    _sel_vars_vi if get_lang() == "vi" else _sel_vars_en,
                    options=[q["column"] for q in numeric_questions],
                    format_func=lambda c: next((q["text"] for q in numeric_questions if q["column"] == c), c),
                    default=[q["column"] for q in numeric_questions[:min(8, len(numeric_questions))]],
                )

                if len(corr_vars) >= 2:
                    corr_result = calculate_correlation_matrix(numeric_df, corr_vars, method=corr_method)
                    if corr_result.get("success"):
                        corr_mat = corr_result["corr_matrix"]
                        pval_mat = corr_result["pvalue_matrix"]

                        # Map column names to question texts for display
                        label_map = {q["column"]: q["text"][:35] for q in numeric_questions}
                        display_corr = corr_mat.rename(index=label_map, columns=label_map)

                        # Heatmap using Plotly
                        fig_corr = go.Figure(data=go.Heatmap(
                            z=display_corr.values,
                            x=display_corr.columns.tolist(),
                            y=display_corr.index.tolist(),
                            colorscale="RdBu",
                            zmid=0,
                            zmin=-1, zmax=1,
                            text=np.round(display_corr.values, 2),
                            texttemplate="%{text}",
                            colorbar=dict(title="r"),
                        ))
                        fig_corr.update_layout(
                            title=f"Ma trận tương quan ({corr_method})" if get_lang() == "vi"
                                  else f"Correlation Matrix ({corr_method})",
                            xaxis=dict(tickangle=-45),
                            height=max(400, len(corr_vars) * 55),
                        )
                        st.plotly_chart(fig_corr, use_container_width=True)

                        # Show significant pairs
                        sig_pairs = []
                        for i_idx, r in enumerate(corr_vars):
                            for j_idx, c in enumerate(corr_vars):
                                if i_idx >= j_idx:
                                    continue
                                r_val = corr_mat.iloc[i_idx, j_idx]
                                p_val = pval_mat.iloc[i_idx, j_idx]
                                if p_val < 0.05:
                                    sig_pairs.append({
                                        "Biến 1" if get_lang() == "vi" else "Variable 1": label_map.get(r, r),
                                        "Biến 2" if get_lang() == "vi" else "Variable 2": label_map.get(c, c),
                                        "r": round(r_val, 3),
                                        "p-value": round(p_val, 4),
                                        "Mức ý nghĩa" if get_lang() == "vi" else "Sig.":
                                            "**" if p_val < 0.01 else "*",
                                    })

                        if sig_pairs:
                            _sig_vi = f"Các cặp tương quan có ý nghĩa thống kê (n={corr_result['n']})"
                            _sig_en = f"Statistically significant pairs (n={corr_result['n']})"
                            st.subheader(_sig_vi if get_lang() == "vi" else _sig_en)
                            st.dataframe(pd.DataFrame(sig_pairs), use_container_width=True)
                    else:
                        st.error(corr_result.get("error", "Lỗi không xác định"))
                else:
                    _info_vi = "Chọn ít nhất 2 biến để tính ma trận tương quan."
                    _info_en = "Select at least 2 variables to compute the correlation matrix."
                    st.info(_info_vi if get_lang() == "vi" else _info_en)
            else:
                _warn_vi = "Cần ít nhất 2 biến số để tính ma trận tương quan."
                _warn_en = "Need at least 2 numeric variables for correlation matrix."
                st.warning(_warn_vi if get_lang() == "vi" else _warn_en)

        # ── Tab: Group Tests ────────────────────────────────────────────────────
        with tab_group:
            _grp_title_vi = "🧪 Kiểm Định So Sánh Nhóm"
            _grp_title_en = "🧪 Group Comparison Tests"
            st.subheader(_grp_title_vi if get_lang() == "vi" else _grp_title_en)

            _grp_info_vi = """
So sánh giá trị trung bình giữa các nhóm:
- **2 nhóm** → Welch's t-test (không giả định phương sai bằng nhau)
- **≥ 3 nhóm** → One-way ANOVA + Tukey HSD post-hoc
"""
            _grp_info_en = """
Compare means across groups:
- **2 groups** → Welch's t-test (unequal variance)
- **≥ 3 groups** → One-way ANOVA + Tukey HSD post-hoc
"""
            st.markdown(_grp_info_vi if get_lang() == "vi" else _grp_info_en)

            # Find categorical questions (group variable)
            cat_questions = [
                q for q in selected_survey.get("questions", [])
                if q["type"] in ["multiple_choice", "dropdown"]
            ]

            if numeric_questions and cat_questions:
                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    _val_vi = "Biến giá trị (số)"
                    _val_en = "Value variable (numeric)"
                    value_col = st.selectbox(
                        _val_vi if get_lang() == "vi" else _val_en,
                        options=[q["column"] for q in numeric_questions],
                        format_func=lambda c: next((q["text"] for q in numeric_questions if q["column"] == c), c),
                        key="grp_value_col",
                    )

                with col_g2:
                    _grp_vi = "Biến nhóm (phân loại)"
                    _grp_en = "Group variable (categorical)"
                    grp_q = st.selectbox(
                        _grp_vi if get_lang() == "vi" else _grp_en,
                        options=cat_questions,
                        format_func=lambda q: q["question_text"],
                        key="grp_cat_q",
                    )
                    grp_col = grp_q.get("id", "")
                    if grp_col not in df.columns:
                        grp_col = ""

                if value_col and grp_col:
                    grp_result = perform_group_comparison(df, value_col, grp_col)
                    if grp_result.get("success"):
                        # Summary cards
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric(
                                "Kiểm định" if get_lang() == "vi" else "Test",
                                grp_result["test_type"]
                            )
                        with c2:
                            st.metric(
                                "Thống kê F/t" if get_lang() == "vi" else "Statistic",
                                f"{grp_result['statistic']:.3f}"
                            )
                        with c3:
                            pv = grp_result["p_value"]
                            sig_label = "✅ Có ý nghĩa (p<0.05)" if pv < 0.05 else "❌ Không ý nghĩa"
                            if get_lang() == "en":
                                sig_label = "✅ Significant (p<0.05)" if pv < 0.05 else "❌ Not significant"
                            st.metric("p-value", f"{pv:.4f}", delta=sig_label)

                        # Group stats chart
                        gs_df = pd.DataFrame(grp_result["group_stats"])
                        fig_grp = go.Figure()
                        fig_grp.add_trace(go.Bar(
                            x=gs_df["group"].astype(str),
                            y=gs_df["mean"],
                            error_y=dict(type="data", array=gs_df["std"].tolist(), visible=True),
                            marker_color="#0066cc",
                            name="Mean ± SD",
                        ))
                        x_label = next((q["text"] for q in cat_questions if q.get("id") == grp_col), grp_col)
                        y_label = next((q["text"] for q in numeric_questions if q["column"] == value_col), value_col)
                        fig_grp.update_layout(
                            xaxis_title=x_label,
                            yaxis_title=y_label,
                            title="Mean ± SD by group",
                            height=350,
                        )
                        st.plotly_chart(fig_grp, use_container_width=True)

                        # Post-hoc table if available
                        if "posthoc" in grp_result and grp_result["posthoc"]:
                            _ph_vi = "Kiểm định post-hoc Tukey HSD"
                            _ph_en = "Tukey HSD Post-hoc Tests"
                            st.subheader(_ph_vi if get_lang() == "vi" else _ph_en)
                            ph_df = pd.DataFrame(grp_result["posthoc"])
                            ph_df.columns = (
                                ["Nhóm 1", "Nhóm 2", "Chênh lệch TB", "p điều chỉnh", "Khác nhau?"]
                                if get_lang() == "vi" else
                                ["Group 1", "Group 2", "Mean Diff", "p-adj", "Significant?"]
                            )
                            ph_df["Khác nhau?" if get_lang() == "vi" else "Significant?"] = \
                                ph_df["Khác nhau?" if get_lang() == "vi" else "Significant?"].map(
                                    {True: "✅", False: "❌"}
                                )
                            st.dataframe(ph_df, use_container_width=True)
                    else:
                        st.error(grp_result.get("error", "Lỗi không xác định"))
                else:
                    _info_vi = "Chọn biến giá trị và biến nhóm hợp lệ."
                    _info_en = "Select a valid value variable and group variable."
                    st.info(_info_vi if get_lang() == "vi" else _info_en)
            else:
                _warn_vi = "Cần ít nhất 1 biến số và 1 biến phân loại để so sánh nhóm."
                _warn_en = "Need at least 1 numeric and 1 categorical variable for group comparison."
                st.warning(_warn_vi if get_lang() == "vi" else _warn_en)

        # ── OLD Cross-question analysis (below tabs) ────────────────────────────
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
                        text_auto=True,
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
                    if pd.notna(correlation):
                        st.metric("Correlation Coefficient", f"{correlation:.3f}")
                    else:
                        st.metric("Correlation Coefficient", "N/A")
                    
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
