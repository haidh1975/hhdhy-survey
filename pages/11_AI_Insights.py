"""
AI Insights & Smart Analysis — HHD-HY Survey App

Market gap addressed vs Cognos / Tableau / Superset:
  ✅ Natural language insights (Cognos/Watson equivalent) — no API cost
  ✅ Knowledge Gap radar chart (educational analytics)
  ✅ Actionable recommendations (Tableau Story equivalent)
  ✅ One-click AI report export (PDF-ready text)
  ✅ Polarized opinion detection (novel feature)

Target users:
  - Giáo viên/Giảng viên xem kết quả đánh giá khóa học
  - HR Managers xem khảo sát nhân sự
  - Nhà nghiên cứu phân tích dữ liệu khảo sát HY
  - SME owners theo dõi văn hóa doanh nghiệp

AI approach: Rule-based NLG (no external API) — free, fast, offline-capable.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.db_utils import get_surveys_db, get_responses_db
from utils.auth import require_auth
from utils.i18n import render_language_selector, t, get_lang
from utils.ai_insights import (
    generate_survey_insights,
    detect_knowledge_gaps,
    get_radar_data,
    build_recommendations,
    generate_text_report,
)

st.set_page_config(
    page_title="HHD-HY — AI Insights",
    page_icon="🤖",
    layout="wide",
)

render_language_selector()
require_auth()

# ── Load data ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_surveys():
    return {s["uuid"]: s for s in get_surveys_db()}


@st.cache_data(ttl=20)
def load_responses(survey_uuid: str):
    return get_responses_db(survey_uuid)


surveys = load_surveys()

# ── Page header ────────────────────────────────────────────────────────────────

st.title(t("ai_insights_page"))
st.markdown(f"*{t('ai_insights_subtitle')}*")
st.markdown("---")

if not surveys:
    st.info(
        "⚠️ Chưa có khảo sát nào. Tạo khảo sát và thu thập phản hồi trước."
        if get_lang() == "vi" else
        "⚠️ No surveys found. Create a survey and collect responses first."
    )
    if st.button("➕ Tạo khảo sát mới" if get_lang() == "vi" else "➕ Create new survey"):
        st.switch_page("pages/1_Create_Survey.py")
    st.stop()

# ── Survey selector ────────────────────────────────────────────────────────────

selected_id = st.selectbox(
    t("select_survey_insights"),
    options=list(surveys.keys()),
    format_func=lambda x: surveys[x]["title"],
)

survey = surveys[selected_id]
responses = load_responses(selected_id)
lang = get_lang()

# ── Header metrics ─────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(t("total_responses"), len(responses))
with col2:
    st.metric(t("num_questions"), len(survey.get("questions", [])))
with col3:
    likert_count = sum(1 for q in survey.get("questions", []) if q.get("type") == "likert_scale")
    st.metric(
        "Câu Likert" if lang == "vi" else "Likert Qs",
        likert_count,
    )
with col4:
    n = len(responses)
    quality = (
        "Xuất sắc" if n >= 100 else
        "Tốt" if n >= 50 else
        "Đủ" if n >= 30 else
        "Cần thêm"
    ) if lang == "vi" else (
        "Excellent" if n >= 100 else
        "Good" if n >= 50 else
        "Adequate" if n >= 30 else
        "Need more"
    )
    st.metric("Chất lượng mẫu" if lang == "vi" else "Sample Quality", quality)

st.markdown("---")

# ── Main tabs ──────────────────────────────────────────────────────────────────

tab_auto, tab_gap, tab_radar, tab_rec = st.tabs([
    t("auto_insights_tab"),
    t("knowledge_gap_tab"),
    t("radar_tab"),
    t("recommendations_tab"),
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Auto Insights
# ══════════════════════════════════════════════════════════════════════════════

with tab_auto:
    _hdr = "💡 Insights tự động từ AI" if lang == "vi" else "💡 Automated AI Insights"
    st.subheader(_hdr)

    if not responses:
        st.info(t("no_insights"))
    else:
        cards = generate_survey_insights(survey, responses, lang)

        # Display insight cards with colored containers
        _type_color = {
            "success": "#d4edda",
            "warning": "#fff3cd",
            "info": "#d1ecf1",
            "error": "#f8d7da",
        }
        _type_border = {
            "success": "#28a745",
            "warning": "#ffc107",
            "info": "#17a2b8",
            "error": "#dc3545",
        }

        for card in cards:
            bg = _type_color.get(card["type"], "#f8f9fa")
            border = _type_border.get(card["type"], "#6c757d")
            st.markdown(
                f"""
                <div style="
                    background:{bg};
                    border-left: 5px solid {border};
                    border-radius: 8px;
                    padding: 14px 18px;
                    margin-bottom: 14px;
                ">
                    <strong style="font-size:1.05em">{card['icon']} {card['title']}</strong>
                    <div style="margin-top:6px; white-space:pre-line">{card['body']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Export AI report
        st.markdown("---")
        _export_btn = "📄 Tải báo cáo AI (.txt)" if lang == "vi" else "📄 Download AI Report (.txt)"
        report_text = generate_text_report(survey, responses, lang)
        st.download_button(
            label=_export_btn,
            data=report_text.encode("utf-8"),
            file_name=f"ai_report_{selected_id[:8]}.txt",
            mime="text/plain",
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Knowledge Gap Analysis
# ══════════════════════════════════════════════════════════════════════════════

with tab_gap:
    st.subheader(t("knowledge_gap_title"))
    st.caption(t("knowledge_gap_desc"))

    if not responses:
        st.info(t("no_insights"))
    else:
        col_thresh, _ = st.columns([1, 3])
        with col_thresh:
            threshold = st.slider(
                t("gap_threshold"),
                min_value=30, max_value=80, value=60, step=5,
                help="Câu hỏi có điểm dưới ngưỡng này được coi là khoảng cách"
                if lang == "vi" else
                "Questions scoring below this threshold are flagged as gaps",
            )

        gaps = detect_knowledge_gaps(survey, responses, threshold_pct=threshold)

        if not gaps:
            st.success(t("no_knowledge_gaps"))
        else:
            _gap_count = f"Phát hiện **{len(gaps)} khoảng cách**" if lang == "vi" \
                else f"Found **{len(gaps)} gap(s)**"
            st.warning(_gap_count)

            # Gap table
            gap_rows = []
            for g in gaps:
                sev_labels_vi = {"high": "🔴 Cao", "medium": "🟡 Trung bình", "low": "🟢 Thấp"}
                sev_labels_en = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
                sev_label = (sev_labels_vi if lang == "vi" else sev_labels_en).get(
                    g["gap_severity"], g["gap_severity"]
                )
                gap_rows.append({
                    ("Câu hỏi" if lang == "vi" else "Question"):
                        g["question_text"][:70],
                    ("Điểm TB" if lang == "vi" else "Mean"):
                        f"{g['mean']:.2f}",
                    ("% Thang điểm" if lang == "vi" else "% of Scale"):
                        f"{g['scale_pct']:.1f}%",
                    ("Độ lệch chuẩn" if lang == "vi" else "Std Dev"):
                        f"{g['stdev']:.2f}",
                    ("Mức độ" if lang == "vi" else "Severity"):
                        sev_label,
                })
            st.dataframe(pd.DataFrame(gap_rows), use_container_width=True, height=300)

            # Bar chart of gap questions (sorted by score ascending)
            gap_df = pd.DataFrame({
                "q": [g["question_text"][:40] for g in gaps],
                "pct": [g["scale_pct"] for g in gaps],
                "sev": [g["gap_severity"] for g in gaps],
            })
            color_map = {"high": "#dc3545", "medium": "#ffc107", "low": "#fd7e14"}
            fig_gap = px.bar(
                gap_df,
                x="pct", y="q",
                orientation="h",
                color="sev",
                color_discrete_map=color_map,
                text="pct",
                labels={
                    "pct": ("% Thang điểm" if lang == "vi" else "% of Scale"),
                    "q": ("Câu hỏi" if lang == "vi" else "Question"),
                    "sev": ("Mức độ" if lang == "vi" else "Severity"),
                },
            )
            fig_gap.add_vline(x=threshold, line_dash="dash", line_color="navy",
                              annotation_text=f"Ngưỡng {threshold}%" if lang == "vi"
                              else f"Threshold {threshold}%")
            fig_gap.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_gap.update_layout(
                height=max(280, len(gaps) * 50),
                yaxis={"categoryorder": "total ascending"},
                showlegend=True,
                margin=dict(t=20, b=20),
            )
            st.plotly_chart(fig_gap, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Radar Chart
# ══════════════════════════════════════════════════════════════════════════════

with tab_radar:
    st.subheader(t("radar_title"))

    if not responses:
        st.info(t("no_insights"))
    else:
        radar = get_radar_data(survey, responses)

        if len(radar["categories"]) < 3:
            st.info(t("radar_no_likert"))
        else:
            # Close the radar polygon
            cats = radar["categories"] + [radar["categories"][0]]
            vals = radar["values"] + [radar["values"][0]]

            fig_radar = go.Figure()

            # Average reference line
            avg_val = radar["avg_value"]
            avg_vals = [avg_val] * len(cats)

            fig_radar.add_trace(go.Scatterpolar(
                r=avg_vals,
                theta=cats,
                fill=None,
                mode="lines",
                line=dict(color="gray", dash="dash", width=1.5),
                name=f"{'Trung bình' if lang == 'vi' else 'Average'} {avg_val:.1f}%",
            ))

            # Actual values
            fig_radar.add_trace(go.Scatterpolar(
                r=vals,
                theta=cats,
                fill="toself",
                fillcolor="rgba(0, 100, 200, 0.15)",
                line=dict(color="#0066cc", width=2.5),
                mode="lines+markers",
                marker=dict(size=7, color="#0066cc"),
                name=survey["title"][:30],
            ))

            # Mark gaps (below 60%)
            gap_cats = [c for c, v in zip(radar["categories"], radar["values"]) if v < 60]
            gap_vals_r = [v for v in radar["values"] if v < 60]
            if gap_cats:
                fig_radar.add_trace(go.Scatterpolar(
                    r=gap_vals_r,
                    theta=gap_cats,
                    mode="markers",
                    marker=dict(size=12, color="#dc3545", symbol="x"),
                    name="Gap (<60%)",
                ))

            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickvals=[20, 40, 60, 80, 100],
                        ticktext=["20%", "40%", "60%", "80%", "100%"],
                        gridcolor="lightgray",
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=10),
                    ),
                ),
                showlegend=True,
                height=520,
                title=dict(
                    text=(
                        f"Bản đồ điểm số — {survey['title'][:40]}"
                        if lang == "vi" else
                        f"Score Map — {survey['title'][:40]}"
                    ),
                    font=dict(size=14),
                ),
                margin=dict(t=50, b=30),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            # Score table below radar
            with st.expander(
                "📋 Bảng điểm chi tiết" if lang == "vi" else "📋 Detailed Score Table"
            ):
                score_rows = []
                for cat, val in zip(radar["categories"], radar["values"]):
                    bar_fill = "█" * int(val / 5) + "░" * (20 - int(val / 5))
                    score_rows.append({
                        ("Câu hỏi" if lang == "vi" else "Question"): cat,
                        ("Điểm %" if lang == "vi" else "Score %"): f"{val:.1f}%",
                        ("Biểu đồ" if lang == "vi" else "Bar"): bar_fill[:20],
                    })
                st.dataframe(pd.DataFrame(score_rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Recommendations
# ══════════════════════════════════════════════════════════════════════════════

with tab_rec:
    st.subheader(t("ai_recommend_title"))

    if not responses:
        st.info(t("no_insights"))
    else:
        recs = build_recommendations(survey, responses, lang)

        if not recs:
            st.success(
                "✅ Không có khuyến nghị đặc biệt — Khảo sát đang hoạt động tốt!"
                if lang == "vi" else
                "✅ No specific recommendations — Survey is performing well!"
            )
        else:
            _p_colors = {
                "high": ("#f8d7da", "#dc3545"),
                "medium": ("#fff3cd", "#ffc107"),
                "low": ("#d4edda", "#28a745"),
            }
            _p_labels_vi = {"high": "ƯU TIÊN CAO", "medium": "TRUNG BÌNH", "low": "THẤP"}
            _p_labels_en = {"high": "HIGH PRIORITY", "medium": "MEDIUM", "low": "LOW"}
            p_labels = _p_labels_vi if lang == "vi" else _p_labels_en

            for i, rec in enumerate(recs, 1):
                bg, border = _p_colors.get(rec["priority"], ("#f8f9fa", "#6c757d"))
                p_lbl = p_labels.get(rec["priority"], rec["priority"].upper())
                st.markdown(
                    f"""
                    <div style="
                        background:{bg};
                        border-left:5px solid {border};
                        border-radius:8px;
                        padding:14px 18px;
                        margin-bottom:12px;
                    ">
                        <div style="font-size:0.78em;font-weight:bold;color:{border};
                                    margin-bottom:4px">
                            [{p_lbl}]
                        </div>
                        <strong>{i}. {rec['icon']} {rec['title']}</strong>
                        <div style="margin-top:6px;color:#333">{rec['action']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Download full report
        st.markdown("---")
        report_text = generate_text_report(survey, responses, lang)
        _dl_lbl = "📥 Tải toàn bộ báo cáo AI (.txt)" if lang == "vi" \
            else "📥 Download Full AI Report (.txt)"
        st.download_button(
            label=_dl_lbl,
            data=report_text.encode("utf-8"),
            file_name=f"ai_report_{selected_id[:8]}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"🤖 **{t('footer_system')}** — {t('footer_copy')}")
