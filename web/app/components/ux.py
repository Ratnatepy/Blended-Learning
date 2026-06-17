'''Higher-level UX components for the Streamlit frontend.'''
from __future__ import annotations

from collections.abc import Iterable
from typing import Any
import html

import streamlit as st


def _safe(value: Any) -> str:
    return html.escape(str(value))

def _render_html(markup: str) -> None:
    """Render compact HTML through Streamlit without Markdown code-block parsing.

    Streamlit's ``st.markdown`` still runs the text through Markdown before the
    HTML is rendered. If a multi-line HTML fragment contains indented lines,
    Markdown can interpret part of the fragment as an indented code block and
    show the raw ``<div>`` tags in the app. Keeping custom HTML compact avoids
    that issue while still allowing our scoped CSS classes to style the blocks.
    """
    st.markdown(markup.strip(), unsafe_allow_html=True)

def _render_badges(badges: Iterable[str] | None) -> str:
    if not badges:
        return ""
    return "".join(f'<span class="hero-badge">{_safe(badge)}</span>' for badge in badges)


def render_page_hero(title: str, subtitle: str, badges: Iterable[str] | None = None, eyebrow: str = "Personalized Blended Learning Prototype") -> None:
    _render_html(
        '<section class="hero-box ux-hero">'
        f'<div class="hero-eyebrow">{_safe(eyebrow)}</div>'
        f'<div class="hero-title">{_safe(title)}</div>'
        f'<div class="hero-subtitle">{_safe(subtitle)}</div>'
        f'<div class="hero-badge-row">{_render_badges(badges)}</div>'
        '</section>'
     )


def render_section_header(title: str, subtitle: str | None = None, eyebrow: str | None = None) -> None:
    eyebrow_html = f'<div class="section-eyebrow">{_safe(eyebrow)}</div>' if eyebrow else ""
    subtitle_html = f'<div class="section-subtitle">{_safe(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'''
        <div class="section-header">
            {eyebrow_html}
            <div class="section-title">{_safe(title)}</div>
            {subtitle_html}
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_info_panel(title: str, body: str, tone: str = "neutral") -> None:
    safe_tone = tone if tone in {"neutral", "success", "warning", "danger"} else "neutral"
    st.markdown(
        f'''
        <div class="ux-info-panel ux-info-panel-{safe_tone}">
            <div class="ux-info-title">{_safe(title)}</div>
            <div class="ux-info-body">{_safe(body)}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_process_steps(steps: Iterable[dict[str, Any] | str]) -> None:
    items: list[str] = []
    for index, step in enumerate(steps, start=1):
        if isinstance(step, dict):
            title = step.get("title", f"Step {index}")
            body = step.get("body", "")
        else:
            title = f"Step {index}"
            body = str(step)
        items.append(
            f'''
            <div class="ux-step-card">
                <div class="ux-step-number">{index:02d}</div>
                <div class="ux-step-title">{_safe(title)}</div>
                <div class="ux-step-body">{_safe(body)}</div>
            </div>
            '''
        )
    st.markdown(f'<div class="ux-step-grid">{"".join(items)}</div>', unsafe_allow_html=True)


def render_feature_group_intro(title: str, subtitle: str, count: int | None = None) -> None:
    count_html = f'<span class="feature-count">{int(count)} items</span>' if count is not None else ""
    st.markdown(
        f'''
        <div class="feature-group-intro">
            <div>
                <div class="feature-group-title">{_safe(title)}</div>
                <div class="feature-group-subtitle">{_safe(subtitle)}</div>
            </div>
            {count_html}
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, body: str, hint: str | None = None) -> None:
    hint_html = f'<div class="empty-state-hint">{_safe(hint)}</div>' if hint else ""
    st.markdown(
        f'''
        <div class="empty-state">
            <div class="empty-state-icon">⌕</div>
            <div class="empty-state-title">{_safe(title)}</div>
            <div class="empty-state-body">{_safe(body)}</div>
            {hint_html}
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_split_card(title: str, items: Iterable[str]) -> None:
    item_html = "".join(f'<li>{_safe(item)}</li>' for item in items)
    st.markdown(
        f'''
        <div class="ux-list-card">
            <div class="ux-list-title">{_safe(title)}</div>
            <ul>{item_html}</ul>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_inline_kpi(label: str, value: Any, caption: str = "") -> None:
    st.markdown(
        f'''
        <div class="inline-kpi">
            <div class="inline-kpi-label">{_safe(label)}</div>
            <div class="inline-kpi-value">{_safe(value)}</div>
            <div class="inline-kpi-caption">{_safe(caption)}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
