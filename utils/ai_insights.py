"""
AI Insights Engine — HHD-HY Survey App

Phân tích dữ liệu khảo sát và tạo ra insights ngôn ngữ tự nhiên
mà KHÔNG cần API AI bên ngoài (rule-based NLG).

Market gap addressed:
  - IBM Cognos Analytics:  Watson AI auto-insights  → tốn kém, phức tạp
  - Tableau:               "Explain Data" feature   → enterprise only
  - Apache Superset:       Thiếu NL insights        → chỉ có charts
  - RapidMiner:            No-code ML               → không có NL output
  This module: Vietnamese/English NL insights, free, zero-API-cost.

Key features:
  1. generate_survey_insights()  — NL insight cards from survey stats
  2. detect_knowledge_gaps()     — Find weak-scoring questions
  3. get_radar_data()            — Spider/radar chart data (Likert only)
  4. build_recommendations()     — Actionable improvement suggestions
  5. generate_text_report()      — Full text report (exportable)

Reference:
  - Papers With Code: survey analytics patterns
  - System Design Primer: stateless computation
  - GeeksforGeeks: statistical measures (mean, stdev, percentile)
"""

from __future__ import annotations
import math
import statistics
from typing import Any


# ─── Private helpers ──────────────────────────────────────────────────────────

def _pct_str(n: int | float, total: int | float, decimals: int = 1) -> str:
    if total == 0:
        return "0%"
    return f"{n / total * 100:.{decimals}f}%"


def _scale_pct(value: float, scale_min: float, scale_max: float) -> float:
    """Normalize value to 0-100% of scale range."""
    rng = scale_max - scale_min
    if rng == 0:
        return 0.0
    return max(0.0, min(100.0, (value - scale_min) / rng * 100))


def _level_vi(pct: float) -> str:
    if pct >= 80: return "rất cao"
    if pct >= 65: return "khá cao"
    if pct >= 50: return "trung bình"
    if pct >= 35: return "thấp"
    return "rất thấp"


def _level_en(pct: float) -> str:
    if pct >= 80: return "very high"
    if pct >= 65: return "high"
    if pct >= 50: return "moderate"
    if pct >= 35: return "low"
    return "very low"


def _severity_color(severity: str) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")


def _extract_likert_scores(survey: dict, responses: list[dict]) -> dict[str, dict]:
    """
    Extract Likert question statistics from responses.
    Returns: {q_id: {q, mean, stdev, n, scale_min, scale_max, scale_pct}}
    """
    questions = survey.get("questions", [])
    result = {}

    for q in questions:
        if q.get("type") != "likert_scale":
            continue
        q_id = q.get("id", "")
        scale_min = float(q.get("scale_min", 1))
        scale_max = float(q.get("scale_max", 5))

        vals: list[float] = []
        for r in responses:
            v = r.get("response_data", {}).get(q_id)
            if v is not None:
                try:
                    vals.append(float(v))
                except (ValueError, TypeError):
                    pass

        if not vals:
            continue

        mean = statistics.mean(vals)
        stdev = statistics.stdev(vals) if len(vals) > 1 else 0.0
        pct = _scale_pct(mean, scale_min, scale_max)

        result[q_id] = {
            "q": q,
            "mean": round(mean, 3),
            "stdev": round(stdev, 3),
            "n": len(vals),
            "scale_min": scale_min,
            "scale_max": scale_max,
            "scale_pct": round(pct, 1),
        }

    return result


# ─── Public API ───────────────────────────────────────────────────────────────

def generate_survey_insights(
    survey: dict,
    responses: list[dict],
    lang: str = "vi",
) -> list[dict]:
    """
    Generate natural language insight cards from survey response data.

    Returns a list of card dicts:
        {type: "info"|"warning"|"success"|"error",
         icon: str, title: str, body: str}
    """
    cards: list[dict] = []
    n = len(responses)
    questions = survey.get("questions", [])
    n_q = len(questions)

    # ── Card 0: No data ────────────────────────────────────────────────────────
    if n == 0:
        cards.append({
            "type": "info", "icon": "ℹ️",
            "title": "Chưa có dữ liệu" if lang == "vi" else "No Data",
            "body": (
                "Chưa có phản hồi nào để phân tích. Thu thập thêm dữ liệu trước."
                if lang == "vi" else
                "No responses yet to analyze. Collect more data first."
            ),
        })
        return cards

    # ── Card 1: Response volume ────────────────────────────────────────────────
    if lang == "vi":
        good = n >= 30
        vol_body = (
            f"Khảo sát đã nhận được **{n} phản hồi**. "
            + ("Đủ dữ liệu để phân tích thống kê có ý nghĩa." if good
               else "Nên thu thập thêm để đạt độ tin cậy thống kê (khuyến nghị ≥ 30 mẫu).")
        )
    else:
        good = n >= 30
        vol_body = (
            f"Survey received **{n} response(s)**. "
            + ("Sufficient for meaningful statistical analysis." if good
               else "Collect more for statistical reliability (≥ 30 recommended).")
        )
    cards.append({
        "type": "success" if good else "warning",
        "icon": "📊",
        "title": "Số lượng phản hồi" if lang == "vi" else "Response Volume",
        "body": vol_body,
    })

    # ── Card 2: Completeness ───────────────────────────────────────────────────
    if n_q > 0:
        filled = 0
        for r in responses:
            rdata = r.get("response_data", {})
            for q in questions:
                v = rdata.get(q.get("id", ""), None)
                if v not in [None, "", []]:
                    filled += 1
        total_cells = n * n_q
        comp_pct = filled / total_cells * 100 if total_cells else 0

        if lang == "vi":
            body = (
                f"Tỷ lệ hoàn thành câu hỏi: **{comp_pct:.1f}%** ({filled}/{total_cells} ô). "
                + ("Mức tham gia xuất sắc." if comp_pct >= 90
                   else "Tốt." if comp_pct >= 75
                   else "Nhiều câu hỏi bị bỏ qua — xem xét giảm số câu bắt buộc.")
            )
        else:
            body = (
                f"Question completion rate: **{comp_pct:.1f}%** ({filled}/{total_cells} cells). "
                + ("Excellent engagement." if comp_pct >= 90
                   else "Good." if comp_pct >= 75
                   else "Many questions skipped — consider reducing mandatory questions.")
            )
        cards.append({
            "type": "success" if comp_pct >= 75 else "warning",
            "icon": "✅",
            "title": "Tỷ lệ hoàn thành" if lang == "vi" else "Completion Rate",
            "body": body,
        })

    # ── Card 3: Likert analysis ────────────────────────────────────────────────
    likert_scores = _extract_likert_scores(survey, responses)
    if likert_scores:
        best_id = max(likert_scores, key=lambda k: likert_scores[k]["scale_pct"])
        worst_id = min(likert_scores, key=lambda k: likert_scores[k]["scale_pct"])
        best = likert_scores[best_id]
        worst = likert_scores[worst_id]
        best_text = best["q"].get("question_text", "")[:55]
        worst_text = worst["q"].get("question_text", "")[:55]

        if lang == "vi":
            body = (
                f"Phân tích **{len(likert_scores)} câu Likert**:\n\n"
                f"- 🏆 **Cao nhất**: \"{best_text}\" — TB: **{best['mean']:.2f}** "
                f"({_level_vi(best['scale_pct'])} — {best['scale_pct']:.0f}%)\n"
                f"- ⚠️ **Thấp nhất**: \"{worst_text}\" — TB: **{worst['mean']:.2f}** "
                f"({_level_vi(worst['scale_pct'])} — {worst['scale_pct']:.0f}%)"
            )
        else:
            body = (
                f"Analysis of **{len(likert_scores)} Likert questions**:\n\n"
                f"- 🏆 **Highest**: \"{best_text}\" — mean: **{best['mean']:.2f}** "
                f"({_level_en(best['scale_pct'])} — {best['scale_pct']:.0f}%)\n"
                f"- ⚠️ **Lowest**: \"{worst_text}\" — mean: **{worst['mean']:.2f}** "
                f"({_level_en(worst['scale_pct'])} — {worst['scale_pct']:.0f}%)"
            )
        cards.append({
            "type": "info", "icon": "🎯",
            "title": "Điểm Likert nổi bật" if lang == "vi" else "Likert Score Highlights",
            "body": body,
        })

        # High variance = polarized opinions
        polarized = [k for k, v in likert_scores.items() if v["stdev"] > 1.2]
        if polarized:
            p_texts = [likert_scores[k]["q"]["question_text"][:45] for k in polarized[:3]]
            if lang == "vi":
                body2 = (
                    f"**{len(polarized)} câu hỏi** có độ lệch chuẩn cao (SD > 1.2), "
                    "cho thấy quan điểm phân cực trong nhóm khảo sát:\n\n"
                    + "".join(f"- \"{t}\"\n" for t in p_texts)
                )
            else:
                body2 = (
                    f"**{len(polarized)} question(s)** show high std deviation (SD > 1.2), "
                    "indicating polarized opinions among respondents:\n\n"
                    + "".join(f"- \"{t}\"\n" for t in p_texts)
                )
            cards.append({
                "type": "warning", "icon": "🔀",
                "title": "Quan điểm phân cực" if lang == "vi" else "Polarized Opinions",
                "body": body2,
            })

    # ── Card 4: Open-ended response engagement ─────────────────────────────────
    text_qs = [q for q in questions if q.get("type") in ["text", "paragraph"]]
    if text_qs:
        filled_t = sum(
            1 for r in responses for q in text_qs
            if str(r.get("response_data", {}).get(q.get("id", ""), "") or "").strip()
        )
        total_t = n * len(text_qs)
        t_pct = filled_t / total_t * 100 if total_t else 0
        if lang == "vi":
            body = (
                f"**{len(text_qs)} câu hỏi mở** — tỷ lệ trả lời: **{t_pct:.1f}%**.\n\n"
                + ("Người dùng rất tích cực chia sẻ ý kiến." if t_pct >= 70
                   else "Tỷ lệ trả lời câu mở chấp nhận được." if t_pct >= 40
                   else "Ít người trả lời câu hỏi mở — xem xét rút gọn hoặc đặt gợi ý rõ hơn.")
            )
        else:
            body = (
                f"**{len(text_qs)} open-ended question(s)** — response rate: **{t_pct:.1f}%**.\n\n"
                + ("Users are very actively sharing opinions." if t_pct >= 70
                   else "Acceptable open-ended response rate." if t_pct >= 40
                   else "Low open-ended response — consider shortening or adding clearer prompts.")
            )
        cards.append({
            "type": "success" if t_pct >= 50 else "info",
            "icon": "💬",
            "title": "Câu hỏi mở" if lang == "vi" else "Open-ended Questions",
            "body": body,
        })

    # ── Card 5: Overall assessment ─────────────────────────────────────────────
    avg_all_pct: float | None = None
    if likert_scores:
        avg_all_pct = statistics.mean(v["scale_pct"] for v in likert_scores.values())
        if lang == "vi":
            overall_body = (
                f"Điểm trung bình tổng thể toàn bộ câu Likert: "
                f"**{avg_all_pct:.1f}%** ({_level_vi(avg_all_pct)}). "
                + (
                    "Kết quả rất tích cực — duy trì và phát huy." if avg_all_pct >= 80
                    else "Kết quả khả quan — tiếp tục cải thiện các điểm yếu." if avg_all_pct >= 60
                    else "Cần chú trọng cải thiện — nhiều lĩnh vực còn yếu."
                )
            )
        else:
            overall_body = (
                f"Overall average score across all Likert questions: "
                f"**{avg_all_pct:.1f}%** ({_level_en(avg_all_pct)}). "
                + (
                    "Very positive results — keep up the good work." if avg_all_pct >= 80
                    else "Good results — continue improving weak areas." if avg_all_pct >= 60
                    else "Needs attention — several areas require significant improvement."
                )
            )
        cards.append({
            "type": "success" if avg_all_pct >= 60 else "warning",
            "icon": "📈",
            "title": "Đánh giá tổng thể" if lang == "vi" else "Overall Assessment",
            "body": overall_body,
        })

    return cards


def detect_knowledge_gaps(
    survey: dict,
    responses: list[dict],
    threshold_pct: float = 60.0,
) -> list[dict]:
    """
    Identify Likert questions where the average score is below
    `threshold_pct`% of the scale range.

    Returns list sorted by scale_pct ascending (worst gaps first):
        [{question_text, mean, scale_pct, gap_severity, scale_min, scale_max}]

    gap_severity: "high" (<40%), "medium" (40-50%), "low" (50-threshold%)
    """
    gaps = []
    likert_scores = _extract_likert_scores(survey, responses)

    for q_id, info in likert_scores.items():
        if info["scale_pct"] < threshold_pct:
            if info["scale_pct"] < 40:
                severity = "high"
            elif info["scale_pct"] < 50:
                severity = "medium"
            else:
                severity = "low"
            gaps.append({
                "question_text": info["q"].get("question_text", ""),
                "mean": info["mean"],
                "stdev": info["stdev"],
                "n": info["n"],
                "scale_pct": info["scale_pct"],
                "gap_severity": severity,
                "scale_min": info["scale_min"],
                "scale_max": info["scale_max"],
            })

    gaps.sort(key=lambda x: x["scale_pct"])
    return gaps


def get_radar_data(survey: dict, responses: list[dict]) -> dict:
    """
    Build Plotly-ready data for a radar / spider chart.
    Shows normalized 0-100% score per Likert question.

    Returns:
        {categories: [str], values: [float], avg_value: float}
    """
    likert_scores = _extract_likert_scores(survey, responses)
    if not likert_scores:
        return {"categories": [], "values": [], "avg_value": 0.0}

    categories = []
    values = []

    for _, info in likert_scores.items():
        # Short label for radar display
        label = info["q"].get("question_text", "")
        label = label[:32] + "…" if len(label) > 32 else label
        categories.append(label)
        values.append(info["scale_pct"])

    avg_value = statistics.mean(values) if values else 0.0
    return {
        "categories": categories,
        "values": values,
        "avg_value": round(avg_value, 1),
    }


def build_recommendations(
    survey: dict,
    responses: list[dict],
    lang: str = "vi",
) -> list[dict]:
    """
    Build actionable recommendations based on insights and gaps.

    Returns list of recommendation dicts:
        {priority: "high"|"medium"|"low", icon: str, title: str, action: str}
    """
    recs: list[dict] = []
    n = len(responses)
    questions = survey.get("questions", [])

    # Low sample size
    if n < 30:
        recs.append({
            "priority": "high",
            "icon": "📢",
            "title": "Tăng cỡ mẫu" if lang == "vi" else "Increase Sample Size",
            "action": (
                f"Hiện có {n} phản hồi. Cần ít nhất 30 để đảm bảo độ tin cậy thống kê. "
                "Chia sẻ link/QR code đến nhiều đối tượng hơn."
                if lang == "vi" else
                f"Current {n} responses. Minimum 30 needed for statistical reliability. "
                "Share the survey link/QR code to a broader audience."
            ),
        })

    # Knowledge gaps
    gaps = detect_knowledge_gaps(survey, responses, threshold_pct=60.0)
    for gap in gaps[:3]:  # top 3 worst gaps
        severity = gap["gap_severity"]
        priority = {"high": "high", "medium": "medium", "low": "low"}.get(severity, "low")
        q_text = gap["question_text"][:50]
        color = _severity_color(severity)
        if lang == "vi":
            action = (
                f"{color} \"{q_text}\" đạt {gap['scale_pct']:.0f}% thang điểm. "
                "Xem xét bổ sung nội dung đào tạo cho lĩnh vực này."
            )
        else:
            action = (
                f"{color} \"{q_text}\" scored {gap['scale_pct']:.0f}% of scale. "
                "Consider adding training content for this area."
            )
        recs.append({
            "priority": priority,
            "icon": "🎯",
            "title": f"Cải thiện: {q_text[:35]}" if lang == "vi" else f"Improve: {q_text[:35]}",
            "action": action,
        })

    # High variance / polarized questions → qualitative follow-up
    likert_scores = _extract_likert_scores(survey, responses)
    polarized = [(k, v) for k, v in likert_scores.items() if v["stdev"] > 1.3]
    if polarized:
        q_text = polarized[0][1]["q"].get("question_text", "")[:45]
        if lang == "vi":
            action = (
                f"\"{q_text}\" có ý kiến phân cực (SD={polarized[0][1]['stdev']:.2f}). "
                "Tổ chức thảo luận nhóm hoặc phỏng vấn sâu để hiểu nguyên nhân."
            )
        else:
            action = (
                f"\"{q_text}\" has polarized responses (SD={polarized[0][1]['stdev']:.2f}). "
                "Conduct focus groups or deep interviews to understand root causes."
            )
        recs.append({
            "priority": "medium",
            "icon": "🔀",
            "title": "Làm rõ quan điểm phân cực" if lang == "vi" else "Clarify Polarized Views",
            "action": action,
        })

    # Open-ended questions underused
    text_qs = [q for q in questions if q.get("type") in ["text", "paragraph"]]
    if not text_qs and len(questions) > 3:
        if lang == "vi":
            recs.append({
                "priority": "low",
                "icon": "💬",
                "title": "Thêm câu hỏi mở",
                "action": (
                    "Khảo sát chưa có câu hỏi mở. Thêm 1-2 câu hỏi mở sẽ giúp "
                    "thu thập ý kiến định tính sâu hơn, tăng giá trị phân tích."
                ),
            })
        else:
            recs.append({
                "priority": "low",
                "icon": "💬",
                "title": "Add Open-ended Questions",
                "action": (
                    "No open-ended questions found. Adding 1-2 open questions will "
                    "gather richer qualitative insights and increase analysis value."
                ),
            })

    # All Likert — suggest distribution channel diversification
    if n > 0 and n < 100:
        if lang == "vi":
            recs.append({
                "priority": "low",
                "icon": "🔗",
                "title": "Mở rộng kênh phân phối",
                "action": (
                    "Sử dụng QR Code (in tờ rơi), gửi email hàng loạt, hoặc tích hợp "
                    "link vào hệ thống LMS/nội bộ để tăng số phản hồi."
                ),
            })
        else:
            recs.append({
                "priority": "low",
                "icon": "🔗",
                "title": "Diversify Distribution Channels",
                "action": (
                    "Use QR Code (print flyers), mass email, or embed in LMS/intranet "
                    "to increase response count."
                ),
            })

    # Sort: high → medium → low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda x: priority_order.get(x["priority"], 3))
    return recs


def generate_text_report(
    survey: dict,
    responses: list[dict],
    lang: str = "vi",
) -> str:
    """
    Generate a full plain-text AI analysis report for download.
    """
    from datetime import datetime
    lines = []
    n = len(responses)
    sep = "=" * 65

    if lang == "vi":
        lines += [
            sep,
            f"  BÁO CÁO PHÂN TÍCH AI — HHD-HY SURVEY SYSTEM",
            sep,
            f"  Khảo sát : {survey.get('title', 'N/A')}",
            f"  Ngày tạo : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"  Tổng phản hồi : {n}",
            f"  Số câu hỏi   : {len(survey.get('questions', []))}",
            sep, "",
            "I. INSIGHTS TỰ ĐỘNG", "-" * 45,
        ]
    else:
        lines += [
            sep,
            f"  AI ANALYSIS REPORT — HHD-HY SURVEY SYSTEM",
            sep,
            f"  Survey  : {survey.get('title', 'N/A')}",
            f"  Date    : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"  Responses : {n}",
            f"  Questions : {len(survey.get('questions', []))}",
            sep, "",
            "I. AUTOMATED INSIGHTS", "-" * 45,
        ]

    for card in generate_survey_insights(survey, responses, lang):
        lines.append(f"{card['icon']} {card['title'].upper()}")
        lines.append(card["body"])
        lines.append("")

    if lang == "vi":
        lines += ["II. KHOẢNG CÁCH KIẾN THỨC", "-" * 45]
    else:
        lines += ["II. KNOWLEDGE GAPS", "-" * 45]

    gaps = detect_knowledge_gaps(survey, responses)
    if gaps:
        for g in gaps:
            sev = _severity_color(g["gap_severity"])
            lines.append(
                f"{sev} {g['question_text'][:60]}\n"
                f"   Score: {g['mean']:.2f} ({g['scale_pct']:.1f}% of scale)"
            )
    else:
        no_gap = "Không phát hiện khoảng cách kiến thức đáng lo ngại." if lang == "vi" \
            else "No significant knowledge gaps detected."
        lines.append(no_gap)

    lines.append("")

    if lang == "vi":
        lines += ["III. KHUYẾN NGHỊ", "-" * 45]
    else:
        lines += ["III. RECOMMENDATIONS", "-" * 45]

    for i, rec in enumerate(build_recommendations(survey, responses, lang), 1):
        priority_label = {"high": "ƯU TIÊN CAO", "medium": "TRUNG BÌNH", "low": "THẤP"} \
            if lang == "vi" else {"high": "HIGH PRIORITY", "medium": "MEDIUM", "low": "LOW"}
        p_lbl = priority_label.get(rec["priority"], rec["priority"].upper())
        lines.append(f"{i}. [{p_lbl}] {rec['icon']} {rec['title']}")
        lines.append(f"   → {rec['action']}")
        lines.append("")

    lines += [sep, f"© Bản quyền HHD-HY — Đỗ Hữu Hải", sep]
    return "\n".join(lines)
