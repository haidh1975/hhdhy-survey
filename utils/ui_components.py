"""
Custom UI Components and Styling for Survey Application
"""
import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling to improve UI/UX"""
    st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --accent-color: #F18F01;
        --success-color: #6A994E;
        --warning-color: #F77F00;
        --danger-color: #C73E1D;
        --light-bg: #F8F9FA;
        --dark-text: #212529;
    }
    
    /* Global styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Headers */
    .main h1 {
        color: var(--primary-color);
        border-bottom: 3px solid var(--accent-color);
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    .main h2 {
        color: var(--secondary-color);
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    .main h3 {
        color: var(--accent-color);
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background-color: var(--light-bg);
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    [data-testid="metric-container"] > div {
        width: fit-content;
        margin: auto;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 1.8rem;
        color: var(--primary-color);
        font-weight: bold;
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: var(--dark-text);
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 0.5rem;
        border: none;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(90deg, var(--success-color), #4CAF50);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(90deg, #4CAF50, var(--success-color));
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--light-bg);
    }
    
    .css-17eq0hr {
        background-color: white;
    }
    
    /* Cards and containers */
    .survey-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .admin-card {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 1rem;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #d4edda;
        border-color: var(--success-color);
        color: #155724;
    }
    
    /* Error messages */
    .stError {
        background-color: #f8d7da;
        border-color: var(--danger-color);
        color: #721c24;
    }
    
    /* Warning messages */
    .stWarning {
        background-color: #fff3cd;
        border-color: var(--warning-color);
        color: #856404;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #d1ecf1;
        border-color: var(--primary-color);
        color: #0c5460;
    }
    
    /* Tables */
    .dataframe {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    .dataframe thead th {
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 0.75rem;
        font-weight: 600;
    }
    
    .dataframe tbody td {
        padding: 0.75rem;
        border-bottom: 1px solid #dee2e6;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: var(--light-bg);
    }
    
    .dataframe tbody tr:hover {
        background-color: #e9ecef;
    }
    
    /* Form inputs */
    .stTextInput > div > div > input {
        border-radius: 0.5rem;
        border: 2px solid #dee2e6;
        padding: 0.5rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 0.2rem rgba(46, 134, 171, 0.25);
    }
    
    .stSelectbox > div > div > select {
        border-radius: 0.5rem;
        border: 2px solid #dee2e6;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 0.5rem;
        border: 2px solid #dee2e6;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: var(--light-bg);
        border-radius: 0.5rem 0.5rem 0 0;
        gap: 8px;
        padding-left: 20px;
        padding-right: 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: var(--light-bg);
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    
    /* Charts */
    .js-plotly-plot {
        border-radius: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--primary-color) !important;
    }
    
    /* Footer styling */
    .footer {
        margin-top: 3rem;
        padding: 2rem 0;
        background-color: var(--light-bg);
        border-top: 1px solid #dee2e6;
        text-align: center;
        color: #6c757d;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        [data-testid="metric-container"] {
            margin-bottom: 1rem;
        }
        
        .survey-card, .admin-card {
            margin-left: 0;
            margin-right: 0;
        }
    }
    
    /* Animation for loading states */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 1.5s infinite;
    }
    
    /* Custom classes for specific components */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-active {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-inactive {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
    }
    </style>
    """, unsafe_allow_html=True)

def create_metric_card(title: str, value: str, delta: str = None, help_text: str = None):
    """Create a custom metric card"""
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ''
    help_html = f'<div class="metric-help">{help_text}</div>' if help_text else ''
    
    card_html = f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
        {help_html}
    </div>
    """
    return st.markdown(card_html, unsafe_allow_html=True)

def create_status_badge(status: str):
    """Create a status badge"""
    status_class = f"status-{status.lower().replace(' ', '-')}"
    badge_html = f'<span class="status-badge {status_class}">{status}</span>'
    return st.markdown(badge_html, unsafe_allow_html=True)

def add_footer():
    """Add a footer to the page"""
    footer_html = """
    <div class="footer">
        <p><strong>Hệ thống Khảo sát Hưng Yên</strong> - Phiên bản 2.0</p>
        <p>© 2024 - Nghiên cứu Vốn xã hội và Vốn nhân lực</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

def show_loading_spinner(text: str = "Đang tải..."):
    """Show a loading spinner with custom text"""
    return st.spinner(text)

def create_info_box(title: str, content: str, icon: str = "ℹ️"):
    """Create an info box"""
    info_html = f"""
    <div class="survey-card">
        <h4>{icon} {title}</h4>
        <p>{content}</p>
    </div>
    """
    return st.markdown(info_html, unsafe_allow_html=True)

def create_admin_alert(title: str, content: str, alert_type: str = "info"):
    """Create an admin alert box"""
    alert_class = f"admin-alert-{alert_type}"
    alert_html = f"""
    <div class="admin-card {alert_class}">
        <h4>⚠️ {title}</h4>
        <p>{content}</p>
    </div>
    """
    return st.markdown(alert_html, unsafe_allow_html=True)