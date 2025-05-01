import pandas as pd
import numpy as np

def calculate_statistics(df, column_name, question_type, question=None):
    """
    Calculate statistics for a survey question based on its type.
    
    Args:
        df (DataFrame): DataFrame containing response data
        column_name (str): Column name in the DataFrame
        question_type (str): Type of question (text, number, multiple_choice, etc.)
        question (dict, optional): Question configuration
        
    Returns:
        dict: Dictionary of calculated statistics
    """
    # Skip if column doesn't exist
    if column_name not in df.columns:
        return None
    
    stats = {}
    
    # Calculate response rate
    total_responses = len(df)
    non_empty_responses = df[column_name].notna().sum()
    response_rate = (non_empty_responses / total_responses) * 100 if total_responses > 0 else 0
    stats["Response Rate (%)"] = round(response_rate, 1)
    
    # Type-specific statistics
    if question_type in ["multiple_choice", "dropdown"]:
        # Get value counts
        value_counts = df[column_name].value_counts()
        
        # Most common response
        if not value_counts.empty:
            stats["Most Common Response"] = str(value_counts.index[0])  # Chuyển đổi sang chuỗi
            stats["Most Common Count"] = int(value_counts.iloc[0])
            stats["Most Common (%)"] = round((value_counts.iloc[0] / non_empty_responses) * 100, 1)
        
        # Number of unique responses
        stats["Unique Responses"] = int(value_counts.count())
    
    elif question_type == "checkbox":
        # For checkbox (multiple selection)
        if isinstance(df[column_name].iloc[0], list):
            # Explode the lists
            exploded = df[column_name].explode()
            
            # Get value counts
            if not exploded.empty:
                value_counts = exploded.value_counts()
                
                # Most common response
                if not value_counts.empty:
                    stats["Most Common Response"] = str(value_counts.index[0])  # Chuyển đổi sang chuỗi
                    stats["Most Common Count"] = int(value_counts.iloc[0])
                    stats["Most Common (%)"] = round((value_counts.iloc[0] / non_empty_responses) * 100, 1)
                
                # Average selections per response
                non_empty_lists = [lst for lst in df[column_name] if isinstance(lst, list) and lst]
                avg_selections = sum(len(lst) for lst in non_empty_lists) / len(non_empty_lists) if non_empty_lists else 0
                stats["Avg Selections Per Response"] = round(avg_selections, 1)
    
    elif question_type == "likert_scale":
        # For Likert scale questions
        if df[column_name].dtype in [np.int64, np.float64]:
            # Basic statistics
            stats["Mean"] = round(df[column_name].mean(), 2)
            stats["Median"] = round(df[column_name].median(), 1)
            stats["Std Dev"] = round(df[column_name].std(), 2)
            
            # Value counts
            value_counts = df[column_name].value_counts().sort_index()
            
            # Most common response
            if not value_counts.empty:
                stats["Most Common Response"] = str(value_counts.index[0])  # Chuyển đổi sang chuỗi
                stats["Most Common Count"] = int(value_counts.iloc[0])
                stats["Most Common (%)"] = round((value_counts.iloc[0] / non_empty_responses) * 100, 1)
            
            # If question object has scale labels, use them
            if question and "scale_labels" in question:
                scale_min = question.get("scale_min", 1)
                scale_max = question.get("scale_max", 5)
                scale_labels = question.get("scale_labels", [])
                
                if len(scale_labels) == (scale_max - scale_min + 1):
                    # Add label for most common response
                    most_common = stats.get("Most Common Response")
                    if most_common is not None:
                        try:
                            # Xử lý trường hợp '1.0' hoặc '1' bằng cách chuyển về float trước
                            most_common_float = float(most_common)
                            label_index = int(most_common_float) - scale_min
                            if 0 <= label_index < len(scale_labels):
                                stats["Most Common Label"] = scale_labels[label_index]
                        except (ValueError, TypeError):
                            # Bỏ qua nếu không thể chuyển đổi được
                            pass
    
    elif question_type == "number":
        # For numeric questions
        if df[column_name].dtype in [np.int64, np.float64]:
            # Basic statistics
            stats["Mean"] = round(df[column_name].mean(), 2)
            stats["Median"] = round(df[column_name].median(), 2)
            stats["Std Dev"] = round(df[column_name].std(), 2)
            stats["Min"] = round(df[column_name].min(), 2)
            stats["Max"] = round(df[column_name].max(), 2)
            
            # Calculate percentiles
            stats["25th Percentile"] = round(df[column_name].quantile(0.25), 2)
            stats["75th Percentile"] = round(df[column_name].quantile(0.75), 2)
    
    elif question_type in ["text", "paragraph"]:
        # For text questions
        if non_empty_responses > 0:
            # Calculate average response length
            text_lengths = df[column_name].dropna().str.len()
            stats["Avg Response Length"] = round(text_lengths.mean(), 1)
            stats["Max Response Length"] = int(text_lengths.max())
            stats["Min Response Length"] = int(text_lengths.min())
    
    return stats
