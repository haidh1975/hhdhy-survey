import streamlit as st
import datetime
from utils.db_utils import get_surveys_db, get_survey_by_uuid_db, save_response_db
from utils.i18n import t, get_lang, render_language_selector

st.set_page_config(
    page_title="HHD-HY — Trả lời Khảo sát / Answer Survey",
    page_icon="📋",
    layout="wide",
)

render_language_selector()


@st.cache_data(ttl=30)
def load_surveys_from_db():
    surveys = get_surveys_db()
    surveys_dict = {}
    for s in surveys:
        surveys_dict[s["uuid"]] = {
            "title": s["title"],
            "description": s["description"],
            "questions": s["questions"],
        }
    return surveys_dict


# Tải khảo sát từ database
surveys_data = load_surveys_from_db()
st.session_state.surveys = surveys_data

# Lấy survey_id từ query params nếu có (dùng khi chia sẻ link)
params = st.query_params

st.title(t("answer_survey_page"))
st.markdown("---")

# Xác định khảo sát cần hiển thị
if "survey" in params:
    survey_id = params.get("survey")
    if survey_id in surveys_data:
        st.session_state.active_survey_id = survey_id
    else:
        no_survey_msg = "Không tìm thấy khảo sát. Vui lòng chọn một khảo sát hợp lệ." \
                        if get_lang() == "vi" else "Survey not found. Please select a valid survey."
        st.error(no_survey_msg)
        st.session_state.active_survey_id = None
else:
    st.subheader(t("choose_survey_to_answer"))

    if not surveys_data:
        no_survey_info = "Chưa có khảo sát nào. Hãy liên hệ người tạo để nhận đường link." \
                         if get_lang() == "vi" else "No surveys available. Contact the survey creator for a link."
        st.info(no_survey_info)
    else:
        survey_options = list(surveys_data.keys())
        selected_survey = st.selectbox(
            t("choose_survey_to_answer"),
            options=survey_options,
            format_func=lambda x: surveys_data[x]["title"],
            index=0 if survey_options else None,
        )

        if selected_survey:
            st.session_state.active_survey_id = selected_survey

            # Hiển thị link chia sẻ
            try:
                base_url = st.get_option("browser.serverAddress") or "localhost"
                port = st.get_option("server.port") or 5000
                survey_url = f"http://{base_url}:{port}/5_Answer_Survey?survey={selected_survey}"
                share_label = "🔗 Chia sẻ khảo sát này" if get_lang() == "vi" else "🔗 Share this survey"
                st.subheader(share_label)
                st.code(survey_url, language="text")
            except Exception:
                pass

# Hiển thị form khảo sát
active_id = st.session_state.get("active_survey_id")

if active_id and active_id in surveys_data:
    survey = surveys_data[active_id]

    st.markdown("---")

    # Kiểm tra đã nộp chưa
    submitted_key = f"submitted_{active_id}"
    if st.session_state.get(submitted_key):
        st.success(t("thank_you"))
        st.balloons()
        if st.button(t("submit_another")):
            st.session_state[submitted_key] = False
            st.rerun()
    else:
        st.header(survey["title"])
        if survey.get("description"):
            st.write(survey["description"])
        st.markdown("---")

        with st.form(key=f"survey_form_{active_id}"):
            responses = {}

            for i, question in enumerate(survey["questions"]):
                q_id = question.get("id", str(i))
                required_mark = f" **{t('required_mark')}**" if question.get("required") else ""
                st.markdown(f"**{i + 1}. {question['question_text']}{required_mark}**")

                q_type = question["type"]

                if q_type == "text":
                    responses[q_id] = st.text_input(
                        t("your_answer"), key=f"q_{i}", placeholder=t("enter_answer")
                    )

                elif q_type == "paragraph":
                    responses[q_id] = st.text_area(
                        t("your_answer"), key=f"q_{i}", placeholder=t("enter_answer")
                    )

                elif q_type == "number":
                    responses[q_id] = st.number_input(t("your_answer"), key=f"q_{i}")

                elif q_type == "multiple_choice":
                    if question.get("options"):
                        responses[q_id] = st.radio(
                            t("select_one"), options=question["options"], key=f"q_{i}"
                        )
                    else:
                        no_opts = "Câu hỏi này chưa có đáp án." if get_lang() == "vi" else "This question has no options."
                        st.warning(no_opts)
                        responses[q_id] = ""

                elif q_type == "checkbox":
                    if question.get("options"):
                        responses[q_id] = st.multiselect(
                            t("select_all"), options=question["options"], key=f"q_{i}"
                        )
                    else:
                        no_opts = "Câu hỏi này chưa có đáp án." if get_lang() == "vi" else "This question has no options."
                        st.warning(no_opts)
                        responses[q_id] = []

                elif q_type == "dropdown":
                    if question.get("options"):
                        responses[q_id] = st.selectbox(
                            t("select_one"), options=question["options"], key=f"q_{i}"
                        )
                    else:
                        no_opts = "Câu hỏi này chưa có đáp án." if get_lang() == "vi" else "This question has no options."
                        st.warning(no_opts)
                        responses[q_id] = ""

                elif q_type == "likert_scale":
                    scale_min = question.get("scale_min", 1)
                    scale_max = question.get("scale_max", 5)
                    if scale_max <= scale_min:
                        scale_max = scale_min + 1

                    responses[q_id] = st.slider(
                        t("your_rating"),
                        min_value=scale_min,
                        max_value=scale_max,
                        value=scale_min,
                        key=f"q_{i}",
                    )

                    scale_labels = question.get("scale_labels", [])
                    if len(scale_labels) == (scale_max - scale_min + 1):
                        cols = st.columns(len(scale_labels))
                        for j, label in enumerate(scale_labels):
                            with cols[j]:
                                st.caption(f"{scale_min + j}: {label}")

                elif q_type == "date":
                    date_val = st.date_input(t("your_answer"), key=f"q_{i}")
                    responses[q_id] = str(date_val)

                elif q_type == "email":
                    email_label = "Email" if get_lang() == "en" else "Email của bạn"
                    responses[q_id] = st.text_input(
                        email_label, key=f"q_{i}", placeholder="ten@example.com"
                    )

                elif q_type == "phone":
                    phone_label = "Phone number" if get_lang() == "en" else "Số điện thoại của bạn"
                    phone_placeholder = "e.g. 0912345678" if get_lang() == "en" else "VD: 0912345678"
                    responses[q_id] = st.text_input(
                        phone_label, key=f"q_{i}", placeholder=phone_placeholder
                    )

                st.markdown("---")

            responses["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            submitted = st.form_submit_button(t("submit_response"), use_container_width=True)

            if submitted:
                # Kiểm tra các câu bắt buộc
                missing = []
                for i, question in enumerate(survey["questions"]):
                    q_id = question.get("id", str(i))
                    if question.get("required"):
                        val = responses.get(q_id)
                        if val is None or val == "" or val == []:
                            missing.append(f"{i + 1}. {question['question_text']}")

                if missing:
                    st.error(
                        t("required_missing") + "\n"
                        + "\n".join(f"- {q}" for q in missing)
                    )
                else:
                    success, message = save_response_db(active_id, responses)
                    if success:
                        st.session_state[submitted_key] = True
                        st.rerun()
                    else:
                        err_save = f"Lỗi khi lưu phản hồi: {message}" if get_lang() == "vi" \
                                   else f"Error saving response: {message}"
                        st.error(err_save)
