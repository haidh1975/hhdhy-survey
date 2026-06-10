"""
View Survey Responses — HHD-HY Survey App

Enhancements (round 2):
  - Full-text search across all responses (BM25-lite, utils/search_utils.py)
  - Pagination to handle large response sets (System Design Primer pattern)
  - NLP word-cloud for text/paragraph responses (utils/nlp_utils.py)
  - Sentiment summary (batch_sentiment)
  - Unified export buttons — Excel (styled), CSV, JSON, Markdown, TXT
  - Response completeness gauge per response
"""

import streamlit as st
import pandas as pd
import datetime
import io
import plotly.graph_objects as go
import plotly.express as px

from utils.db_utils import get_surveys_db, get_responses_db
from utils.auth import require_auth
from utils.i18n import render_language_selector, t, get_lang
from utils.search_utils import search_responses
from utils.nlp_utils import word_frequency, build_wordcloud_data, batch_sentiment
from utils.export_utils import download_buttons

st.set_page_config(
    page_title="HHD-HY — Xem Phản Hồi / View Responses",
    page_icon="📊",
    layout="wide",
)

render_language_selector()

require_auth()

# ── Caching ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_surveys():
    return {s["uuid"]: s for s in get_surveys_db()}


@st.cache_data(ttl=15)
def load_responses(survey_uuid: str):
    return get_responses_db(survey_uuid)


# ── Page header ───────────────────────────────────────────────────────────────

surveys = load_surveys()

st.title(t("view_responses_page"))

if not surveys:
    no_survey_msg = "⚠️ Chưa có khảo sát nào. Hãy vào trang **Tạo Khảo Sát** để tạo khảo sát đầu tiên." \
                    if get_lang() == "vi" else "⚠️ No surveys found. Go to **Create Survey** to create one."
    st.info(no_survey_msg)
    if st.button("➕ Tạo khảo sát mới" if get_lang() == "vi" else "➕ Create new survey"):
        st.switch_page("pages/1_Create_Survey.py")
    st.stop()

# ── Survey selector ────────────────────────────────────────────────────────────

selected_id = st.selectbox(
    t("choose_to_view"),
    options=list(surveys.keys()),
    format_func=lambda x: surveys[x]["title"],
)

survey = surveys[selected_id]
raw_responses = load_responses(selected_id)

st.markdown("---")

# ── Survey info + overview metrics ────────────────────────────────────────────

st.subheader(f"📋 {survey['title']}")
if survey.get("description"):
    st.write(f"**{t('survey_description')}:** {survey['description']}")

questions = survey.get("questions", [])
n_questions = len(questions)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(t("total_responses"), len(raw_responses))
with col2:
    if raw_responses:
        latest = max(
            (r.get("submitted_at", "") for r in raw_responses if r.get("submitted_at")),
            default="N/A",
        )
        st.metric(t("latest_response"), latest[:10] if latest != "N/A" else "N/A")
    else:
        st.metric(t("latest_response"), "N/A")
with col3:
    st.metric(t("num_questions"), n_questions)
with col4:
    # Data completeness %
    if raw_responses:
        total_cells = len(raw_responses) * n_questions
        filled = 0
        for r in raw_responses:
            rdata = r.get("response_data", {})
            for q in questions:
                v = rdata.get(q.get("id", ""), None)
                if v is not None and v != "" and v != []:
                    filled += 1
        pct = round(filled / total_cells * 100, 1) if total_cells else 0
        _lbl = "Độ đầy đủ" if get_lang() == "vi" else "Completeness"
        st.metric(_lbl, f"{pct}%")
    else:
        _lbl = "Độ đầy đủ" if get_lang() == "vi" else "Completeness"
        st.metric(_lbl, "—")

st.markdown("---")

if not raw_responses:
    st.info(t("no_responses_yet"))
    st.stop()

# ── Build DataFrame ────────────────────────────────────────────────────────────

response_rows = []
for r in raw_responses:
    row = dict(r.get("response_data", {}))
    row["_thoi_gian"] = (r.get("submitted_at") or "")[:19]
    row["_ip"] = r.get("ip_address") or ""
    response_rows.append(row)

df_full = pd.DataFrame(response_rows)

# Map question IDs → readable labels
q_map = {}
for i, q in enumerate(questions):
    q_id = q.get("id", str(i))
    q_map[q_id] = f"C{i+1}. {q['question_text'][:45]}"

df_full = df_full.rename(columns=q_map)

# ── Filters ───────────────────────────────────────────────────────────────────

filter_label = "🔎 Bộ lọc & Tìm kiếm" if get_lang() == "vi" else "🔎 Filters & Search"
st.subheader(filter_label)

col_date, col_search = st.columns([2, 3])
filtered_indices = list(range(len(raw_responses)))

with col_date:
    if "_thoi_gian" in df_full.columns:
        try:
            df_full["_thoi_gian"] = pd.to_datetime(df_full["_thoi_gian"], errors="coerce")
            valid_dates = df_full["_thoi_gian"].dropna()
            if not valid_dates.empty:
                min_date = valid_dates.min().date()
                max_date = valid_dates.max().date()
                date_range = st.date_input(
                    t("filter_date"),
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )
                if len(date_range) == 2:
                    s_date, e_date = date_range
                    mask = (df_full["_thoi_gian"].dt.date >= s_date) & \
                           (df_full["_thoi_gian"].dt.date <= e_date)
                    filtered_indices = [i for i in filtered_indices if mask.iloc[i]]
            df_full["_thoi_gian"] = df_full["_thoi_gian"].astype(str)
        except Exception:
            pass

with col_search:
    # Full-text search (BM25-lite — utils/search_utils.py)
    _search_ph = "🔍 Tìm kiếm trong phản hồi..." if get_lang() == "vi" else "🔍 Search within responses..."
    search_query = st.text_input(
        "Tìm kiếm" if get_lang() == "vi" else "Search",
        placeholder=_search_ph,
        key="resp_search",
    )
    if search_query.strip():
        # Filter responses by search on the subset already filtered by date
        resp_subset = [raw_responses[i] for i in filtered_indices]
        ranked_local = search_responses(resp_subset, search_query, top_k=len(resp_subset))
        filtered_indices = [filtered_indices[j] for j in ranked_local]

# Apply filter to both df and raw_responses
df = df_full.iloc[filtered_indices].reset_index(drop=True)
filtered_raw = [raw_responses[i] for i in filtered_indices]

show_caption = (
    f"Hiển thị {len(df)} / {len(raw_responses)} phản hồi"
    if get_lang() == "vi" else
    f"Showing {len(df)} / {len(raw_responses)} responses"
)
st.caption(show_caption)

# ── Data table ────────────────────────────────────────────────────────────────

st.subheader(t("data_table"))

# Show/hide metadata
col_opt1, col_opt2 = st.columns([2, 3])
with col_opt1:
    show_meta = st.checkbox(t("show_meta"), value=False)

display_df = df if show_meta else df.drop(
    columns=[c for c in ["_thoi_gian", "_ip"] if c in df.columns], errors="ignore"
)

# ── Pagination ────────────────────────────────────────────────────────────────
# Reference: System Design Primer — pagination for large datasets

PAGE_SIZES = [10, 25, 50, 100]
with col_opt2:
    _pg_label = "Số dòng mỗi trang" if get_lang() == "vi" else "Rows per page"
    page_size = st.selectbox(_pg_label, PAGE_SIZES, index=1, key="pg_size")

total_pages = max(1, (len(display_df) + page_size - 1) // page_size)

if total_pages > 1:
    col_pn, col_pi = st.columns([1, 4])
    with col_pn:
        _pg_txt = f"Trang (1 – {total_pages})" if get_lang() == "vi" else f"Page (1 – {total_pages})"
        page_num = st.number_input(_pg_txt, min_value=1, max_value=total_pages,
                                   value=1, step=1, key="pg_num")
    page_start = (page_num - 1) * page_size
    page_end = page_start + page_size
    page_df = display_df.iloc[page_start:page_end]
else:
    page_df = display_df

st.dataframe(page_df, use_container_width=True)

# ── Export buttons (all formats) ──────────────────────────────────────────────

st.markdown("---")
_export_title = "📤 Xuất dữ liệu" if get_lang() == "vi" else "📤 Export Data"
st.subheader(_export_title)
download_buttons(
    df=display_df,
    base_filename=f"phan_hoi_{selected_id[:8]}",
    survey=survey,
    responses=filtered_raw,
    lang=get_lang(),
)

# ── NLP Analysis of text responses ────────────────────────────────────────────

text_questions = [q for q in questions if q["type"] in ["text", "paragraph"]]
if text_questions:
    st.markdown("---")
    _nlp_title = "💬 Phân tích văn bản phản hồi" if get_lang() == "vi" else "💬 Text Response Analysis"
    st.subheader(_nlp_title)

    sel_txt_q = st.selectbox(
        "Chọn câu hỏi văn bản" if get_lang() == "vi" else "Select text question",
        options=text_questions,
        format_func=lambda q: q["question_text"],
        key="sel_txt_q",
    )
    q_id_txt = sel_txt_q.get("id", "")
    text_vals = [
        str(r.get("response_data", {}).get(q_id_txt, ""))
        for r in filtered_raw
        if r.get("response_data", {}).get(q_id_txt, "")
    ]

    if text_vals:
        col_wc, col_sent = st.columns(2)

        with col_wc:
            _wc_title = "☁️ Từ xuất hiện nhiều nhất" if get_lang() == "vi" else "☁️ Most Frequent Words"
            st.markdown(f"**{_wc_title}**")
            wc_data = build_wordcloud_data(text_vals, top_n=40)
            if wc_data:
                wc_df = pd.DataFrame(wc_data).sort_values("value", ascending=False)
                fig_wc = px.treemap(
                    wc_df,
                    path=["text"],
                    values="value",
                    color="value",
                    color_continuous_scale="Blues",
                )
                fig_wc.update_layout(height=320, margin=dict(t=10, b=10))
                st.plotly_chart(fig_wc, use_container_width=True)

        with col_sent:
            _sent_title = "😊 Phân tích cảm xúc" if get_lang() == "vi" else "😊 Sentiment Analysis"
            st.markdown(f"**{_sent_title}**")
            sent = batch_sentiment(text_vals)
            fig_sent = go.Figure(go.Pie(
                labels=(
                    ["Tích cực", "Tiêu cực", "Trung tính"]
                    if get_lang() == "vi" else
                    ["Positive", "Negative", "Neutral"]
                ),
                values=[sent["positive"], sent["negative"], sent["neutral"]],
                hole=0.4,
                marker=dict(colors=["#2ecc71", "#e74c3c", "#95a5a6"]),
            ))
            fig_sent.update_layout(height=320, margin=dict(t=10, b=10), showlegend=True)
            st.plotly_chart(fig_sent, use_container_width=True)

        # Word list table
        _top_words_title = "Danh sách từ thường gặp" if get_lang() == "vi" else "Top words"
        with st.expander(_top_words_title):
            freq_list = word_frequency(text_vals, top_n=30)
            freq_df = pd.DataFrame(
                freq_list,
                columns=["Từ" if get_lang() == "vi" else "Word",
                         "Tần suất" if get_lang() == "vi" else "Count"]
            )
            st.dataframe(freq_df, use_container_width=True, height=200)
    else:
        st.info("Chưa có câu trả lời văn bản nào." if get_lang() == "vi" else "No text responses yet.")

# ── Individual response expanders ────────────────────────────────────────────

st.markdown("---")
st.subheader(t("view_detail"))

q_id_to_text = {q.get("id", str(i)): q["question_text"] for i, q in enumerate(questions)}

# Only show the paginated slice for individual responses too
resp_page = filtered_raw[page_start:page_end] if total_pages > 1 else filtered_raw

for idx, r in enumerate(resp_page, start=(page_start if total_pages > 1 else 0) + 1):
    rdata = r.get("response_data", {})
    submitted = (r.get("submitted_at") or "")[:19]

    # Completeness badge for this response
    filled_q = sum(
        1 for q in questions
        if rdata.get(q.get("id", ""), None) not in [None, "", []]
    )
    completeness_str = f"  ✅ {filled_q}/{n_questions}" if n_questions else ""

    with st.expander(f"{t('response_num')} #{idx}  —  {submitted}{completeness_str}"):
        for q in questions:
            q_id = q.get("id", str(questions.index(q)))
            val = rdata.get(q_id, t("no_answer"))
            st.markdown(f"**{q['question_text']}**")
            if isinstance(val, list):
                for item in val:
                    st.markdown(f"- {item}")
            else:
                st.write(val)
            st.markdown("---")
