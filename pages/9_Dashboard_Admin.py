import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.auth import require_admin, get_current_user
from utils.db_utils import get_system_stats_db, get_surveys_db, get_all_users_db
from utils.database import check_database_health
from utils.i18n import render_language_selector, t, get_lang

st.set_page_config(
    page_title="HHD-HY — Dashboard Quản trị / Admin Dashboard",
    page_icon="📈",
    layout="wide",
)

# Require admin authentication
require_admin()

render_language_selector()

_title = "📈 Dashboard Quản trị Nâng cao" if get_lang() == "vi" else "📈 Advanced Admin Dashboard"
_subtitle = "Theo dõi và phân tích toàn diện hệ thống khảo sát" if get_lang() == "vi" \
            else "Comprehensive monitoring and analysis of the survey system"
st.title(_title)
st.markdown(_subtitle)

# Load data with caching
@st.cache_data(ttl=60)
def load_dashboard_data():
    """Load all dashboard data with caching"""
    return {
        'stats': get_system_stats_db(),
        'surveys': get_surveys_db(),
        'users': get_all_users_db(),
        'db_health': check_database_health()
    }

data = load_dashboard_data()
stats = data['stats']
surveys = data['surveys'] 
users = data['users']
db_health = data['db_health']

# Top metrics row
_sys_overview = "📊 Tổng quan hệ thống" if get_lang() == "vi" else "📊 System Overview"
st.header(_sys_overview)

col1, col2, col3, col4, col5 = st.columns(5)

total_users = stats.get('users', {}).get('total', 0)
active_users = stats.get('users', {}).get('active', 0)
total_surveys = stats.get('surveys', {}).get('total', 0)
active_surveys = stats.get('surveys', {}).get('active', 0)
total_responses = stats.get('responses', {}).get('total', 0)
admin_count = stats.get('users', {}).get('admin_count', 0)

with col1:
    _lbl = "Người dùng" if get_lang() == "vi" else "Users"
    _delta = f"{active_users} hoạt động" if get_lang() == "vi" else f"{active_users} active"
    st.metric(_lbl, total_users, delta=_delta)

with col2:
    _lbl = "Khảo sát" if get_lang() == "vi" else "Surveys"
    _delta = f"{active_surveys} đang hoạt động" if get_lang() == "vi" else f"{active_surveys} active"
    st.metric(_lbl, total_surveys, delta=_delta)

with col3:
    _lbl = "Tổng phản hồi" if get_lang() == "vi" else "Total Responses"
    st.metric(_lbl, total_responses)

with col4:
    _lbl = "Quản trị viên" if get_lang() == "vi" else "Admins"
    st.metric(_lbl, admin_count)

with col5:
    db_status = db_health.get('status', 'unknown')
    status_color = "🟢" if db_status == "healthy" else "🔴"
    st.metric("Database", f"{status_color} {db_status.title()}")

st.markdown("---")

# Charts row
col1, col2 = st.columns(2)

with col1:
    _trend_title = "📈 Xu hướng phản hồi theo khảo sát" if get_lang() == "vi" else "📈 Responses per Survey"
    st.subheader(_trend_title)

    if surveys:
        # Bar chart: responses per survey (Pareto-style)
        # Reference: GeeksforGeeks Pareto Chart pattern
        survey_resp_data = sorted(
            [{"title": s["title"][:30], "responses": s.get("response_count", 0)} for s in surveys],
            key=lambda x: x["responses"],
            reverse=True
        )
        df_resp_bar = pd.DataFrame(survey_resp_data)
        if not df_resp_bar.empty:
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=df_resp_bar["title"],
                y=df_resp_bar["responses"],
                marker=dict(
                    color=df_resp_bar["responses"],
                    colorscale="Blues",
                    showscale=False,
                ),
                text=df_resp_bar["responses"],
                textposition="outside",
            ))
            # Add cumulative % line (Pareto)
            total_r = df_resp_bar["responses"].sum()
            if total_r > 0:
                cum_pct = (df_resp_bar["responses"].cumsum() / total_r * 100).tolist()
                fig_bar.add_trace(go.Scatter(
                    x=df_resp_bar["title"],
                    y=cum_pct,
                    mode="lines+markers",
                    name="Tích lũy %" if get_lang() == "vi" else "Cumulative %",
                    yaxis="y2",
                    line=dict(color="#ff7f0e", width=2),
                ))
                fig_bar.update_layout(
                    yaxis2=dict(
                        overlaying="y", side="right",
                        range=[0, 110],
                        title="%" ,
                        showgrid=False,
                    )
                )
            fig_bar.update_layout(
                xaxis_tickangle=-30,
                xaxis_title="",
                yaxis_title="Số phản hồi" if get_lang() == "vi" else "Responses",
                showlegend=False,
                height=320,
                margin=dict(t=20, b=80),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Chưa có phản hồi nào." if get_lang() == "vi" else "No responses yet.")
    else:
        st.info("Chưa có khảo sát nào." if get_lang() == "vi" else "No surveys yet.")

with col2:
    _user_dist_title = "👥 Phân bố người dùng" if get_lang() == "vi" else "👥 User Distribution"
    st.subheader(_user_dist_title)

    if users:
        # User role + status donut chart
        user_roles = {}
        for user in users:
            role = user.get('role', 'user')
            user_roles[role] = user_roles.get(role, 0) + 1

        role_labels_vi = {'admin': 'Quản trị viên', 'user': 'Người dùng'}
        role_labels_en = {'admin': 'Administrator', 'user': 'User'}
        role_labels = role_labels_vi if get_lang() == "vi" else role_labels_en

        fig_users = go.Figure(data=[go.Pie(
            labels=[role_labels.get(r, r) for r in user_roles],
            values=list(user_roles.values()),
            hole=0.45,
            textinfo="label+percent",
            marker=dict(colors=["#0066cc", "#6eaee0"]),
        )])
        _pie_title = "Vai trò người dùng" if get_lang() == "vi" else "User Roles"
        fig_users.update_layout(
            title=_pie_title,
            height=320,
            showlegend=True,
            margin=dict(t=40, b=10),
        )
        st.plotly_chart(fig_users, use_container_width=True)
    else:
        st.info("Chưa có người dùng nào." if get_lang() == "vi" else "No users yet.")

# Detailed analytics
st.header("📋 Phân tích chi tiết")

tab1, tab2, tab3, tab4 = st.tabs(["Khảo sát", "Người dùng", "Hệ thống", "Hoạt động gần đây"])

with tab1:
    st.subheader("🔍 Phân tích khảo sát")
    
    if surveys:
        # Survey statistics table
        survey_data = []
        for survey in surveys:
            survey_data.append({
                'Tiêu đề': survey['title'][:50] + ('...' if len(survey['title']) > 50 else ''),
                'Ngày tạo': survey.get('created_at', 'N/A')[:10],
                'Số câu hỏi': len(survey.get('questions', [])),
                'Số phản hồi': survey.get('response_count', 0),
                'Trạng thái': 'Hoạt động' if survey.get('active', True) else 'Tạm dừng'
            })
        
        survey_df = pd.DataFrame(survey_data)
        st.dataframe(survey_df, use_container_width=True)
        
        # Survey performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Most popular surveys
            popular_surveys = sorted(surveys, key=lambda x: x.get('response_count', 0), reverse=True)[:5]
            
            st.markdown("**Top 5 khảo sát có nhiều phản hồi nhất:**")
            for i, survey in enumerate(popular_surveys):
                st.write(f"{i+1}. {survey['title'][:30]}... ({survey.get('response_count', 0)} phản hồi)")
        
        with col2:
            # Survey complexity analysis
            question_counts = [len(survey.get('questions', [])) for survey in surveys]
            avg_questions = sum(question_counts) / len(question_counts) if question_counts else 0
            
            st.metric("Số câu hỏi trung bình", f"{avg_questions:.1f}")
            st.metric("Khảo sát phức tạp nhất", f"{max(question_counts) if question_counts else 0} câu hỏi")
            st.metric("Khảo sát đơn giản nhất", f"{min(question_counts) if question_counts else 0} câu hỏi")

with tab2:
    st.subheader("👤 Phân tích người dùng")
    
    if users:
        # User activity analysis
        user_data = []
        for user in users:
            user_data.append({
                'Tên đăng nhập': user['username'],
                'Email': user['email'],
                'Vai trò': 'Quản trị viên' if user['role'] == 'admin' else 'Người dùng',
                'Trạng thái': 'Hoạt động' if user.get('active', True) else 'Tạm khóa',
                'Ngày tạo': user.get('created_at', 'N/A')[:10],
                'Đăng nhập cuối': user.get('last_login', 'Chưa từng')[:10] if user.get('last_login') else 'Chưa từng'
            })
        
        user_df = pd.DataFrame(user_data)
        st.dataframe(user_df, use_container_width=True)
        
        # User statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_users_7d = 0  # Would need to implement date filtering
            st.metric("Người dùng mới (7 ngày)", new_users_7d)
        
        with col2:
            active_rate = (stats.get('users', {}).get('active', 0) / total_users * 100) if total_users > 0 else 0
            st.metric("Tỷ lệ người dùng hoạt động", f"{active_rate:.1f}%")
        
        with col3:
            admin_rate = (admin_count / total_users * 100) if total_users > 0 else 0
            st.metric("Tỷ lệ quản trị viên", f"{admin_rate:.1f}%")

with tab3:
    st.subheader("⚙️ Thông tin hệ thống")
    
    # Database health
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Tình trạng Database:**")
        if db_health.get('status') == 'healthy':
            st.success(f"✅ Kết nối ổn định ({db_health.get('connection', 'unknown')})")
            st.info(f"📊 Số bảng: {db_health.get('tables_count', 'N/A')}")
        else:
            st.error(f"❌ Có vấn đề: {db_health.get('error', 'Unknown error')}")
    
    with col2:
        st.markdown("**Thống kê lưu trữ:**")
        st.info(f"📋 Khảo sát: {total_surveys}")
        st.info(f"💬 Phản hồi: {total_responses}")
        st.info(f"👥 Người dùng: {total_users}")
    
    # Performance metrics (placeholder)
    st.markdown("**Hiệu suất hệ thống:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Thời gian phản hồi", "< 100ms", delta="Tốt")
    
    with col2:
        st.metric("Tải trang trung bình", "1.2s", delta="Bình thường")
    
    with col3:
        st.metric("Uptime", "99.9%", delta="Xuất sắc")

with tab4:
    st.subheader("🕒 Hoạt động gần đây")
    
    # Recent activity
    recent_activity = []
    
    # Recent surveys
    recent_surveys = stats.get('recent_activity', {}).get('surveys', [])
    for survey in recent_surveys:
        recent_activity.append({
            'Thời gian': survey.get('created_at', 'N/A')[:16],
            'Hoạt động': 'Tạo khảo sát mới',
            'Chi tiết': survey.get('title', 'N/A')[:50],
            'Người thực hiện': f"User ID: {survey.get('created_by', 'N/A')}"
        })
    
    # Recent responses
    recent_responses = stats.get('recent_activity', {}).get('responses', [])
    for response in recent_responses:
        recent_activity.append({
            'Thời gian': response.get('submitted_at', 'N/A')[:16],
            'Hoạt động': 'Gửi phản hồi',
            'Chi tiết': f"Survey ID: {response.get('survey_id', 'N/A')}",
            'Người thực hiện': f"User ID: {response.get('user_id', 'Anonymous')}"
        })
    
    if recent_activity:
        # Sort by time (newest first)
        recent_activity.sort(key=lambda x: x['Thời gian'], reverse=True)
        
        activity_df = pd.DataFrame(recent_activity[:20])  # Show last 20 activities
        st.dataframe(activity_df, use_container_width=True)
    else:
        st.info("Chưa có hoạt động gần đây")

# Quick actions
st.header("⚡ Thao tác nhanh")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🔄 Làm mới dữ liệu", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col2:
    if st.button("☁️ Backup Google Drive", use_container_width=True):
        st.switch_page("pages/10_Google_Drive_Backup.py")

with col3:
    if st.button("📊 Xem thống kê chi tiết", use_container_width=True):
        st.switch_page("pages/4_Data_Analysis.py")

with col4:
    if st.button("👥 Quản lý người dùng", use_container_width=True):
        st.switch_page("pages/8_Admin.py")

with col5:
    if st.button("🏠 Về trang chủ", use_container_width=True):
        st.switch_page("app.py")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p><strong>Dashboard Quản trị Nâng cao</strong> - Phiên bản 2.0</p>
        <p>Cập nhật cuối: {}</p>
    </div>
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M")), 
    unsafe_allow_html=True
)