import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def create_chart(df, column_name, question_type, question=None, title=None):
    """
    Create an appropriate chart for a survey question based on its type.
    
    Args:
        df (DataFrame): DataFrame containing response data
        column_name (str): Column name in the DataFrame
        question_type (str): Type of question (text, number, multiple_choice, etc.)
        question (dict, optional): Question configuration
        title (str, optional): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Skip if column doesn't exist
    if column_name not in df.columns:
        return None
    
    chart_title = title if title else f"Responses for {column_name}"
    
    # Create appropriate chart based on question type
    if question_type in ["multiple_choice", "dropdown"]:
        # Bar chart for categorical data
        value_counts = df[column_name].value_counts().reset_index()
        value_counts.columns = ["option", "count"]
        
        fig = px.bar(
            value_counts,
            x="option",
            y="count",
            title=chart_title,
            labels={"option": "Option", "count": "Count"}
        )
        
        return fig
    
    elif question_type == "checkbox":
        # For checkbox (multiple selection)
        if isinstance(df[column_name].iloc[0], list):
            # Explode the lists
            exploded = df[column_name].explode()
            
            # Get value counts
            value_counts = exploded.value_counts().reset_index()
            value_counts.columns = ["option", "count"]
            
            fig = px.bar(
                value_counts,
                x="option",
                y="count",
                title=chart_title,
                labels={"option": "Option", "count": "Count"}
            )
            
            return fig
    
    elif question_type == "likert_scale":
        # For Likert scale questions
        if df[column_name].dtype in [np.int64, np.float64]:
            value_counts = df[column_name].value_counts().sort_index().reset_index()
            value_counts.columns = ["rating", "count"]
            
            # Get scale information from the question
            if question:
                scale_min = question.get("scale_min", 1)
                scale_max = question.get("scale_max", 5)
                scale_labels = question.get("scale_labels", [])
                
                # Map numeric values to labels if available
                if len(scale_labels) == (scale_max - scale_min + 1):
                    label_map = {i: f"{i} - {label}" for i, label in 
                                zip(range(scale_min, scale_max + 1), scale_labels)}
                    value_counts["label"] = value_counts["rating"].map(label_map)
                    
                    # Create horizontal bar chart with labels
                    fig = px.bar(
                        value_counts,
                        y="label",
                        x="count",
                        title=chart_title,
                        labels={"count": "Count", "label": "Rating"},
                        orientation='h'
                    )
                    
                    return fig
            
            # Create horizontal bar chart without labels
            fig = px.bar(
                value_counts,
                y="rating",
                x="count",
                title=chart_title,
                labels={"count": "Count", "rating": "Rating"},
                orientation='h'
            )
            
            return fig
    
    elif question_type == "number":
        # For numeric questions
        if df[column_name].dtype in [np.int64, np.float64]:
            # Create histogram
            fig = px.histogram(
                df,
                x=column_name,
                nbins=10,
                title=chart_title
            )
            
            return fig
    
    elif question_type == "date":
        # For date questions
        try:
            date_series = pd.to_datetime(df[column_name])
            
            # Create date histogram
            fig = px.histogram(
                date_series,
                nbins=20,
                title=chart_title
            )
            
            return fig
        except:
            pass
    
    # Return None if no chart could be created
    return None

def create_comparison_chart(df, column1, column2, question_type1, question_type2, title=None):
    """
    Create a chart comparing two survey questions.
    
    Args:
        df (DataFrame): DataFrame containing response data
        column1 (str): First column name
        column2 (str): Second column name
        question_type1 (str): Type of first question
        question_type2 (str): Type of second question
        title (str, optional): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Skip if columns don't exist
    if column1 not in df.columns or column2 not in df.columns:
        return None
    
    chart_title = title if title else f"Comparison: {column1} vs {column2}"
    
    # Determine chart type based on question types
    
    # Two categorical questions
    if question_type1 in ["multiple_choice", "dropdown"] and question_type2 in ["multiple_choice", "dropdown"]:
        # Create a contingency table
        contingency = pd.crosstab(
            df[column1],
            df[column2],
            normalize='index',
            margins=True
        ) * 100
        
        # Create heatmap
        fig = px.imshow(
            contingency.iloc[:-1, :-1],  # Remove the 'All' row and column
            labels=dict(x=column2, y=column1, color="Percentage"),
            x=contingency.columns[:-1],  # Remove the 'All' column
            y=contingency.index[:-1],    # Remove the 'All' row
            text_auto='.1f',
            color_continuous_scale="Blues",
            aspect="auto",
            title=chart_title
        )
        
        return fig
    
    # Two numeric questions
    elif (question_type1 in ["likert_scale", "number"] and 
          question_type2 in ["likert_scale", "number"] and
          df[column1].dtype in [np.int64, np.float64] and
          df[column2].dtype in [np.int64, np.float64]):
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x=column1,
            y=column2,
            trendline="ols",
            title=chart_title
        )
        
        return fig
    
    # Numeric vs categorical
    elif (question_type1 in ["likert_scale", "number"] and
          question_type2 in ["multiple_choice", "dropdown"] and
          df[column1].dtype in [np.int64, np.float64]):
        
        # Create box plot
        fig = px.box(
            df,
            x=column2,
            y=column1,
            title=chart_title
        )
        
        return fig
    
    # Categorical vs numeric
    elif (question_type1 in ["multiple_choice", "dropdown"] and
          question_type2 in ["likert_scale", "number"] and
          df[column2].dtype in [np.int64, np.float64]):
        
        # Create box plot
        fig = px.box(
            df,
            x=column1,
            y=column2,
            title=chart_title
        )
        
        return fig
    
    # Return None if no chart could be created
    return None
