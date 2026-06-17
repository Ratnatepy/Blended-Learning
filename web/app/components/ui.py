"""Reusable Streamlit UI components."""

from __future__ import annotations

from typing import Any
import html

import plotly.graph_objects as go
import streamlit as st

from core.config import ThemeSettings

from core.recommendations import (
    clean_recommendation_text,
    get_nested_recommendation_tags,
    get_recommendation_report,
    parse_tags_to_list,
)


def show_api_error(error_type: str, error_message: str = "") -> None:
    if error_type == "connection_error":
        st.error("Could not connect to FastAPI backend.")
    elif error_type == "timeout_error":
        st.warning(
            "FastAPI received the request, but the frontend waited too long for the response. "
            "Because OpenRouter LLM generation can be slow, the recommendation may already be saved. "
            "Please search the student ID before clicking Generate again."
        )
    elif error_type == "request_error":
        st.error("A request error occurred while contacting FastAPI.")
        if error_message:
            st.code(error_message)
    else:
        st.error("An unknown frontend/API error occurred.")
        if error_message:
            st.code(error_message)


def render_metric_card(label: Any, value: Any, subtext: Any = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(str(label))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-small">{html.escape(str(subtext))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tags(tags: Any) -> None:
    cleaned_tags = parse_tags_to_list(tags)
    if not cleaned_tags:
        st.info("No recommendation tags available.")
        return

    html_tags = "".join(f'<span class="tag-pill">{html.escape(tag)}</span>' for tag in cleaned_tags)
    st.markdown(html_tags, unsafe_allow_html=True)


def style_plotly(fig: go.Figure, theme: ThemeSettings | None = None) -> go.Figure:
    """Apply frontend theme colors to Plotly charts."""

    text_color = theme.color("text", "#f8fafc") if theme else "#f8fafc"
    plotly_cfg = theme.plotly if theme else {}
    template = plotly_cfg.get("template", "plotly_dark")
    paper_bgcolor = plotly_cfg.get("paper_bgcolor", "rgba(0,0,0,0)")
    plot_bgcolor = plotly_cfg.get("plot_bgcolor", "rgba(0,0,0,0)")
    gridcolor = plotly_cfg.get("gridcolor", "rgba(148,163,184,0.15)")
    linecolor = plotly_cfg.get("linecolor", "rgba(148,163,184,0.25)")

    fig.update_layout(
        template=template,
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        font=dict(color=text_color),
        title_font=dict(size=18, color=text_color),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=text_color)),
    )
    fig.update_xaxes(gridcolor=gridcolor, linecolor=linecolor)
    fig.update_yaxes(gridcolor=gridcolor, linecolor=linecolor)
    return fig


def render_recommendation_report(report: Any) -> None:
    cleaned_report = clean_recommendation_text(report)
    if cleaned_report:
        st.markdown(cleaned_report, unsafe_allow_html=True)


def render_generated_recommendation_result(data: dict[str, Any], final_student_id: str, respondent_type: str) -> None:
    """Render recommendation generation result from flat or nested API response."""
    if not isinstance(data, dict):
        st.error("FastAPI returned an invalid response format.")
        st.code(str(data))
        return

    already_exists = data.get("already_exists", False)

    if already_exists:
        st.warning("This ID already exists. Showing the saved recommendation instead of creating a duplicate.")
    else:
        st.success("Recommendation generated and saved successfully.")

    if respondent_type == "Non-ITC / External Respondent":
        st.info(
            f"Generated internal external respondent ID: `{final_student_id}`. "
            "This ID is stored for database tracking and future model tuning, "
            "but the public lookup page is limited to ITC student IDs."
        )

    student_id_value = data.get("student_id", final_student_id)
    segment_value = data.get("student_segment_label") or data.get("segment_label") or data.get("segment") or "-"
    generation_source = data.get("llm_generation_source")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Assigned Learner Segment")
        st.markdown(
            f"""
            <div class="info-card">
                <b>ID:</b> {html.escape(str(student_id_value))}<br><br>
                <b>Segment:</b> {html.escape(str(segment_value))}<br><br>
                <b>Generation Source:</b> {html.escape(str(generation_source or "-"))}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("### Recommendation Tags")
        render_tags(get_nested_recommendation_tags(data))

    st.markdown("### Generated Recommendation Report")

    if generation_source == "openrouter_llm":
        st.success("Generated using OpenRouter LLM.")
    elif generation_source:
        st.warning(
            "Generated using the safe rule-based fallback "
            f"because LLM generation was unavailable: `{generation_source}`."
        )

    generated_report = get_recommendation_report(data)
    if generated_report:
        render_recommendation_report(generated_report)
    else:
        st.info(
            "The backend returned NLP extraction and recommendation tags, "
            "but no final recommendation report field was found."
        )
        with st.expander("Show raw FastAPI response"):
            st.json(data)
