import streamlit as st
import pandas as pd
import json
import io
import base64
from utils.db_utils import get_surveys_db, get_responses_db
from utils.auth import require_auth
from utils.i18n import render_language_selector, t, get_lang

st.set_page_config(
    page_title="HHD-HY — Phân phối Khảo sát / Distribute Survey",
    page_icon="🔗",
    layout="wide",
)

render_language_selector()

require_auth()


@st.cache_data(ttl=30)
def load_surveys():
    surveys = get_surveys_db()
    return {s["uuid"]: s for s in surveys}


@st.cache_data(ttl=30)
def load_responses(survey_uuid: str):
    return get_responses_db(survey_uuid)


surveys = load_surveys()

st.title(t("distribute_page"))

if not surveys:
    no_survey_msg = "⚠️ Chưa có khảo sát nào. Hãy vào trang **Tạo Khảo Sát** để tạo khảo sát đầu tiên." \
                    if get_lang() == "vi" else "⚠️ No surveys found. Go to **Create Survey** to create your first one."
    st.info(no_survey_msg)
    create_btn = "➕ Tạo khảo sát mới" if get_lang() == "vi" else "➕ Create new survey"
    if st.button(create_btn):
        st.switch_page("pages/1_Create_Survey.py")
else:
    # Chọn khảo sát
    selected_id = st.selectbox(
        t("choose_to_distribute"),
        options=list(surveys.keys()),
        format_func=lambda x: surveys[x]["title"],
    )
    survey = surveys[selected_id]
    responses = load_responses(selected_id)

    st.markdown("---")
    col_info, col_stat = st.columns([3, 1])
    with col_info:
        st.subheader(f"📋 {survey['title']}")
        no_desc = "Không có mô tả" if get_lang() == "vi" else "No description"
        st.write(f"**{t('survey_description')}:** {survey.get('description') or no_desc}")
        st.write(f"**{t('num_questions')}:** {len(survey.get('questions', []))}")
    with col_stat:
        st.metric(t("total_responses"), len(responses))

    st.markdown("---")

    # ── Link chia sẻ ──────────────────────────────────────────────
    st.subheader(t("survey_link"))

    try:
        host = st.get_option("browser.serverAddress") or "localhost"
        port = st.get_option("server.port") or 5000
    except Exception:
        host, port = "localhost", 5000

    survey_url = f"http://{host}:{port}/5_Answer_Survey?survey={selected_id}"
    st.code(survey_url, language="text")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"#### {t('preview_survey')}")
        if st.button(t("preview_btn"), use_container_width=True):
            st.session_state.preview_survey_id = selected_id
            st.rerun()

    with col2:
        st.markdown(f"#### {t('open_form')}")
        if st.button(t("open_form_btn"), use_container_width=True):
            st.switch_page("pages/5_Answer_Survey.py")

    with col3:
        st.markdown(f"#### {t('qr_code')}")
        try:
            import qrcode
            from PIL import Image

            qr_img = qrcode.make(survey_url)
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            st.markdown(
                f'<img src="data:image/png;base64,{img_b64}" width="160" '
                f'style="border-radius:8px;border:1px solid #ddd;">',
                unsafe_allow_html=True,
            )
            st.caption(t("scan_qr"))

            st.download_button(
                label=t("download_qr"),
                data=buf.getvalue(),
                file_name=f"qr_{selected_id[:8]}.png",
                mime="image/png",
                use_container_width=True,
            )
        except ImportError:
            qr_warn = "Cần cài `qrcode[pil]` để tạo mã QR" if get_lang() == "vi" \
                      else "Install `qrcode[pil]` to generate QR codes"
            st.warning(qr_warn)

    # ── Xuất dữ liệu ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader(t("export_data"))

    if responses:
        response_data = [r["response_data"] for r in responses]
        df = pd.DataFrame(response_data)

        st.dataframe(df.head(10), use_container_width=True)
        if len(responses) > 10:
            show_caption = f"Hiển thị 10 / {len(responses)} phản hồi" if get_lang() == "vi" \
                           else f"Showing 10 / {len(responses)} responses"
            st.caption(show_caption)

        col_csv, col_json, col_excel = st.columns(3)

        with col_csv:
            csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label=t("export_csv"),
                data=csv_bytes,
                file_name=f"{survey['title'][:30]}_responses.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_json:
            json_bytes = json.dumps(response_data, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button(
                label=t("export_json"),
                data=json_bytes,
                file_name=f"{survey['title'][:30]}_responses.json",
                mime="application/json",
                use_container_width=True,
            )

        with col_excel:
            excel_buf = io.BytesIO()
            sheet_name = "Phản hồi" if get_lang() == "vi" else "Responses"
            with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            st.download_button(
                label=t("export_excel"),
                data=excel_buf.getvalue(),
                file_name=f"{survey['title'][:30]}_responses.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.info(t("no_responses_export"))

    # ── Xem trước khảo sát ────────────────────────────────────────
    if st.session_state.get("preview_survey_id") == selected_id:
        st.markdown("---")
        preview_header = "👁️ Xem trước khảo sát" if get_lang() == "vi" else "👁️ Survey Preview"
        st.subheader(preview_header)

        for i, q in enumerate(survey.get("questions", [])):
            req = f" **({t('required_mark')})**" if q.get("required") else ""
            st.markdown(f"**{i+1}. {q['question_text']}{req}**")
            q_type = q["type"]

            if q_type == "text":
                st.text_input("Câu trả lời", key=f"prev_{i}", disabled=True)
            elif q_type == "paragraph":
                st.text_area("Câu trả lời", key=f"prev_{i}", disabled=True)
            elif q_type == "number":
                st.number_input("Câu trả lời", key=f"prev_{i}", disabled=True)
            elif q_type in ["multiple_choice"]:
                st.radio("Chọn một", options=q.get("options", []), key=f"prev_{i}", disabled=True)
            elif q_type == "checkbox":
                st.multiselect("Chọn các đáp án", options=q.get("options", []), key=f"prev_{i}", disabled=True)
            elif q_type == "dropdown":
                st.selectbox("Chọn một", options=q.get("options", []), key=f"prev_{i}", disabled=True)
            elif q_type == "likert_scale":
                st.slider("Đánh giá", min_value=q.get("scale_min", 1), max_value=q.get("scale_max", 5),
                          value=q.get("scale_min", 1), key=f"prev_{i}", disabled=True)
            elif q_type == "date":
                st.date_input("Ngày", key=f"prev_{i}", disabled=True)
            elif q_type == "email":
                st.text_input("Email", key=f"prev_{i}", disabled=True, placeholder="ten@example.com")
            elif q_type == "phone":
                st.text_input("Số điện thoại", key=f"prev_{i}", disabled=True)
            st.markdown("---")

        st.button(t("submit_response"), disabled=True, use_container_width=True)
        if st.button(t("close_preview")):
            del st.session_state["preview_survey_id"]
            st.rerun()

# ── Hướng dẫn ────────────────────────────────────────────────────
st.markdown("---")
st.subheader(t("distribute_guide"))
if get_lang() == "vi":
    st.markdown("""
Chia sẻ khảo sát của bạn bằng các cách sau:

1. **📧 Email** — Gửi đường link trực tiếp đến người tham gia qua email
2. **📱 Mạng xã hội** — Chia sẻ link lên Facebook, Zalo, Telegram...
3. **📱 Mã QR** — In mã QR ra giấy hoặc chia sẻ ảnh cho người tham gia quét
4. **🌐 Website** — Nhúng link vào trang web hoặc cổng thông tin nội bộ

> 💡 Theo dõi phản hồi tại trang **Xem Phản Hồi** hoặc **Phân Tích Dữ Liệu**.
""")
else:
    st.markdown("""
Share your survey using one of the following methods:

1. **📧 Email** — Send the link directly to participants via email
2. **📱 Social Media** — Share the link on Facebook, Zalo, Telegram...
3. **📱 QR Code** — Print the QR code or share the image for participants to scan
4. **🌐 Website** — Embed the link in a website or internal portal

> 💡 Track responses in the **View Responses** or **Data Analysis** pages.
""")
