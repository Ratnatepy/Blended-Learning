"""Streamlit page configuration and CSS theme."""

from __future__ import annotations

import html

import streamlit as st

from core.config import ThemeSettings, WebSettings


def _c(theme: ThemeSettings, key: str, default: str) -> str:
    return theme.color(key, default)


def build_custom_css(theme: ThemeSettings) -> str:
    """Build scoped Streamlit CSS from config-driven theme values."""

    primary = _c(theme, "primary", "#ef4444")
    primary_hover = _c(theme, "primary_hover", "#dc2626")
    accent = _c(theme, "accent", "#f97316")
    background_start = _c(theme, "background_start", "#020617")
    background_mid = _c(theme, "background_mid", "#0f172a")
    background_end = _c(theme, "background_end", "#111827")
    sidebar_start = _c(theme, "sidebar_start", background_start)
    sidebar_end = _c(theme, "sidebar_end", background_end)
    card_background = _c(theme, "card_background", "rgba(15, 23, 42, 0.92)")
    card_background_soft = _c(theme, "card_background_soft", "rgba(15, 23, 42, 0.55)")
    input_background = _c(theme, "input_background", "#111827")
    text = _c(theme, "text", "#f8fafc")
    heading = _c(theme, "heading", "#ffffff")
    muted_text = _c(theme, "muted_text", "#cbd5e1")
    subtle_text = _c(theme, "subtle_text", "#94a3b8")
    border = _c(theme, "border", "rgba(255,255,255,0.09)")
    border_strong = _c(theme, "border_strong", "#334155")
    success = _c(theme, "success", "#22c55e")
    success_text = _c(theme, "success_text", "#bbf7d0")
    danger = _c(theme, "danger", "#ef4444")
    danger_text = _c(theme, "danger_text", "#fecaca")

    max_width = int(theme.layout_value("max_width_px", 1280))
    desktop_padding_top = float(theme.layout_value("desktop_padding_top_rem", 3.8))
    mobile_padding_top = float(theme.layout_value("mobile_padding_top_rem", 4.8))
    small_mobile_padding_top = float(theme.layout_value("small_mobile_padding_top_rem", 5.2))

    return f"""
    <style>
        :root {{
            --bl-primary: {primary};
            --bl-primary-hover: {primary_hover};
            --bl-accent: {accent};
            --bl-bg-start: {background_start};
            --bl-bg-mid: {background_mid};
            --bl-bg-end: {background_end};
            --bl-card-bg: {card_background};
            --bl-card-bg-soft: {card_background_soft};
            --bl-input-bg: {input_background};
            --bl-text: {text};
            --bl-heading: {heading};
            --bl-muted-text: {muted_text};
            --bl-subtle-text: {subtle_text};
            --bl-border: {border};
            --bl-border-strong: {border_strong};
            --bl-success: {success};
            --bl-success-text: {success_text};
            --bl-danger: {danger};
            --bl-danger-text: {danger_text};
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(239, 68, 68, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.10), transparent 28%),
                linear-gradient(135deg, var(--bl-bg-start) 0%, var(--bl-bg-mid) 55%, var(--bl-bg-end) 100%);
            color: var(--bl-text);
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
            height: 3.2rem;
        }}

        .block-container {{
            padding-top: {desktop_padding_top}rem !important;
            padding-bottom: 2rem;
            max-width: {max_width}px;
        }}

        @media (max-width: 768px) {{
            .block-container {{
                padding-top: {mobile_padding_top}rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }}

            .hero-box {{
                padding: 1.1rem 1.2rem !important;
                border-radius: 18px !important;
                margin-top: 0.5rem !important;
                margin-bottom: 1.2rem !important;
            }}

            .hero-title {{
                font-size: 1.45rem !important;
                line-height: 1.3 !important;
                word-break: break-word;
                white-space: normal;
            }}

            .hero-subtitle {{
                font-size: 0.86rem !important;
                line-height: 1.45 !important;
            }}

            .hero-badge {{
                font-size: 0.68rem !important;
                padding: 0.28rem 0.55rem !important;
                margin: 0.12rem 0.18rem 0.12rem 0;
            }}

            .section-title {{
                font-size: 1.25rem !important;
                line-height: 1.35 !important;
                margin-top: 0.6rem !important;
            }}
        }}

        @media (max-width: 420px) {{
            .block-container {{
                padding-top: {small_mobile_padding_top}rem !important;
            }}

            .hero-title {{ font-size: 1.3rem !important; }}
            .hero-box {{ padding: 1rem !important; }}
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {sidebar_start} 0%, {sidebar_end} 100%);
            border-right: 1px solid var(--bl-border);
        }}

        /* Keep theme scoped. Avoid global `div/span` overrides because they can make
           Streamlit selectbox/dropdown internals unreadable. */
        .stMarkdown, .stMarkdown p, .stMarkdown li,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p {{
            color: var(--bl-text);
        }}

        h1, h2, h3 {{
            color: var(--bl-heading);
            font-weight: 800;
            letter-spacing: -0.03em;
        }}

        .hero-box {{
            padding: 1.5rem 2rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(30,41,59,0.96));
            color: var(--bl-text);
            margin-bottom: 1.5rem;
            border: 1px solid var(--bl-border);
            box-shadow: 0 18px 45px rgba(0,0,0,0.30);
        }}

        .hero-title {{
            font-size: 2.15rem;
            line-height: 1.2;
            font-weight: 900;
            margin-bottom: 0.35rem;
            color: var(--bl-heading);
        }}

        .hero-subtitle {{
            color: var(--bl-muted-text);
            font-size: 1rem;
            margin-bottom: 0.9rem;
        }}

        .hero-badge {{
            display: inline-block;
            color: var(--bl-danger-text);
            background: rgba(239,68,68,0.12);
            border: 1px solid rgba(239,68,68,0.35);
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            margin: 0.15rem 0.35rem 0.15rem 0;
        }}

        .section-title {{
            font-size: 1.55rem;
            font-weight: 800;
            margin-top: 0.2rem;
            margin-bottom: 1rem;
            color: var(--bl-heading);
        }}

        .metric-card,
        .info-card,
        .footer-box,
        .sidebar-info-card,
        .sidebar-current-page {{
            background: var(--bl-card-bg);
            border: 1px solid var(--bl-border);
            box-shadow: 0 12px 32px rgba(0,0,0,0.28);
            backdrop-filter: blur(8px);
        }}

        .metric-card {{
            padding: 1.15rem 1.25rem;
            border-radius: 18px;
            margin-bottom: 1rem;
            min-height: 132px;
        }}

        .metric-label {{ font-size: 0.92rem; color: var(--bl-muted-text); margin-bottom: 0.45rem; }}
        .metric-value {{ font-size: 2rem; font-weight: 900; color: var(--bl-heading); line-height: 1.1; }}
        .metric-small {{ font-size: 0.84rem; color: var(--bl-subtle-text); margin-top: 0.55rem; }}

        .info-card {{
            padding: 1.2rem 1.35rem;
            border-radius: 18px;
            margin-bottom: 1rem;
            color: var(--bl-text);
        }}

        .question-card {{
            background: var(--bl-card-bg-soft);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
            padding: 0.75rem 0.85rem;
            margin-top: 0.85rem;
            margin-bottom: 0.35rem;
        }}

        .question-label {{ font-size: 0.95rem; color: var(--bl-heading); font-weight: 800; margin-bottom: 0.28rem; }}
        .question-text {{ font-size: 0.82rem; color: var(--bl-muted-text); line-height: 1.42; }}
        .scale-note {{ font-size: 0.78rem; color: var(--bl-subtle-text); margin-top: 0.25rem; }}

        .tag-pill {{
            display: inline-block;
            background: rgba(239,68,68,0.14);
            color: var(--bl-danger-text);
            border: 1px solid rgba(239,68,68,0.42);
            padding: 0.38rem 0.78rem;
            border-radius: 999px;
            margin: 0.2rem 0.35rem 0.2rem 0;
            font-size: 0.85rem;
            font-weight: 750;
        }}

        .status-pill-ok,
        .status-pill-bad {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.35rem 0.65rem;
            font-size: 0.82rem;
            font-weight: 800;
        }}

        .status-pill-ok {{
            color: var(--bl-success-text);
            background: rgba(34,197,94,0.13);
            border: 1px solid rgba(34,197,94,0.35);
        }}

        .status-pill-bad {{
            color: var(--bl-danger-text);
            background: rgba(239,68,68,0.13);
            border: 1px solid rgba(239,68,68,0.35);
        }}

        .footer-box {{
            margin-top: 2rem;
            padding: 1rem 1.2rem;
            border-radius: 16px;
            color: var(--bl-muted-text);
            font-size: 0.92rem;
        }}

        .stButton > button[kind="primary"],
        .stButton > button {{
            background: linear-gradient(135deg, var(--bl-primary), var(--bl-accent));
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.62rem 1.1rem;
            font-weight: 800;
            box-shadow: 0 8px 20px rgba(239,68,68,0.22);
        }}

        .stButton > button:hover {{
            background: linear-gradient(135deg, var(--bl-primary-hover), #ea580c);
            color: white;
            border: none;
            transform: translateY(-1px);
        }}

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {{
            background-color: var(--bl-input-bg);
            color: var(--bl-text);
            border: 1px solid var(--bl-border-strong);
            border-radius: 12px;
        }}

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {{
            border: 1px solid var(--bl-primary);
            box-shadow: 0 0 0 1px var(--bl-primary);
        }}

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            background-color: var(--bl-input-bg);
            color: var(--bl-text);
            border-radius: 12px;
        }}

        div[data-baseweb="popover"],
        div[data-baseweb="menu"] {{
            background-color: var(--bl-input-bg) !important;
            color: var(--bl-text) !important;
        }}

        div[data-baseweb="option"] {{
            color: var(--bl-text) !important;
        }}

        div[data-testid="stDataFrame"] {{
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--bl-border);
        }}

        div[data-testid="stPlotlyChart"] {{
            background: var(--bl-card-bg-soft);
            border-radius: 18px;
            padding: 0.5rem;
            border: 1px solid rgba(255,255,255,0.06);
        }}

        .inline-icon,
        .sidebar-brand-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: var(--bl-text);
        }}

        .inline-icon {{ width: 1.15em; height: 1.15em; margin-right: 0.45rem; vertical-align: -0.15em; }}
        .inline-icon svg,
        .sidebar-brand-icon svg {{ width: 100%; height: 100%; stroke: currentColor; }}

        .sidebar-brand {{
            display: flex;
            align-items: center;
            gap: 0.55rem;
            font-size: 1.08rem;
            font-weight: 900;
            color: var(--bl-text);
            margin-bottom: 1rem;
        }}

        .sidebar-logo {{
            width: 60px;
            height: 60px;
            object-fit: contain;
            background: transparent;
            padding: 0;
            border: none;
            border-radius: 0;
            box-shadow: none;
        }}

        .sidebar-info-card {{
            padding: 1rem;
            border-radius: 18px;
            margin-bottom: 1.2rem;
        }}

        .sidebar-info-title {{
            font-size: 1rem;
            font-weight: 900;
            color: var(--bl-heading);
            margin-bottom: 0.35rem;
        }}

        .sidebar-info-text {{
            font-size: 0.82rem;
            color: var(--bl-muted-text);
            line-height: 1.45;
        }}

        .sidebar-current-page {{
            padding: 0.85rem;
            border-radius: 14px;
            margin-bottom: 0.8rem;
        }}

        .sidebar-current-label {{
            font-size: 0.78rem;
            color: var(--bl-subtle-text);
            margin-bottom: 0.25rem;
        }}

        .sidebar-current-value {{
            font-size: 0.92rem;
            font-weight: 800;
            color: var(--bl-heading);
        }}


        /* UX polish layer */
        .ux-hero {{ position: relative; overflow: hidden; }}
        .ux-hero::after {{ content: ""; position: absolute; right: -90px; top: -90px; width: 240px; height: 240px; background: radial-gradient(circle, rgba(249,115,22,0.22), transparent 68%); pointer-events: none; }}
        .hero-eyebrow, .section-eyebrow {{ color: var(--bl-danger-text); text-transform: uppercase; letter-spacing: 0.13em; font-size: 0.72rem; font-weight: 900; margin-bottom: 0.45rem; }}
        .hero-badge-row {{ display: flex; flex-wrap: wrap; gap: 0.25rem; }}
        .section-header {{ margin: 0.35rem 0 1rem 0; }}
        .section-subtitle {{ color: var(--bl-muted-text); font-size: 0.96rem; line-height: 1.55; margin-top: -0.5rem; max-width: 900px; }}
        .ux-info-panel {{ border-radius: 18px; padding: 1rem 1.15rem; margin: 0.85rem 0 1rem; background: var(--bl-card-bg-soft); border: 1px solid var(--bl-border); }}
        .ux-info-title {{ color: var(--bl-heading); font-weight: 900; margin-bottom: 0.25rem; }}
        .ux-info-body {{ color: var(--bl-muted-text); font-size: 0.92rem; line-height: 1.5; }}
        .ux-info-panel-success {{ border-color: rgba(34,197,94,0.30); background: rgba(34,197,94,0.08); }}
        .ux-info-panel-warning {{ border-color: rgba(249,115,22,0.36); background: rgba(249,115,22,0.08); }}
        .ux-info-panel-danger {{ border-color: rgba(239,68,68,0.36); background: rgba(239,68,68,0.08); }}
        .ux-step-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.85rem; margin: 0.9rem 0 1.2rem; }}
        .ux-step-card, .ux-list-card, .inline-kpi, .empty-state, .feature-group-intro {{ background: var(--bl-card-bg-soft); border: 1px solid var(--bl-border); border-radius: 18px; box-shadow: 0 10px 26px rgba(0,0,0,0.18); }}
        .ux-step-card {{ padding: 1rem; min-height: 132px; }}
        .ux-step-number {{ width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white; background: linear-gradient(135deg, var(--bl-primary), var(--bl-accent)); margin-bottom: 0.75rem; }}
        .ux-step-title {{ color: var(--bl-heading); font-weight: 900; margin-bottom: 0.3rem; }}
        .ux-step-body {{ color: var(--bl-muted-text); font-size: 0.86rem; line-height: 1.48; }}
        .feature-group-intro {{ display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; padding: 0.95rem 1rem; margin: 0.35rem 0 1rem; }}
        .feature-group-title {{ color: var(--bl-heading); font-weight: 900; font-size: 1.02rem; }}
        .feature-group-subtitle {{ color: var(--bl-muted-text); font-size: 0.86rem; line-height: 1.45; margin-top: 0.15rem; }}
        .feature-count {{ white-space: nowrap; color: var(--bl-danger-text); border: 1px solid rgba(239,68,68,0.35); background: rgba(239,68,68,0.11); border-radius: 999px; padding: 0.28rem 0.6rem; font-size: 0.74rem; font-weight: 800; }}
        .empty-state {{ text-align: center; padding: 2rem 1.2rem; margin: 1rem 0; }}
        .empty-state-icon {{ width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; border-radius: 16px; color: white; background: linear-gradient(135deg, var(--bl-primary), var(--bl-accent)); font-size: 1.3rem; margin-bottom: 0.75rem; }}
        .empty-state-title {{ color: var(--bl-heading); font-weight: 900; font-size: 1.05rem; margin-bottom: 0.35rem; }}
        .empty-state-body, .empty-state-hint {{ color: var(--bl-muted-text); font-size: 0.9rem; line-height: 1.5; }}
        .empty-state-hint {{ color: var(--bl-subtle-text); margin-top: 0.5rem; }}
        .ux-list-card {{ padding: 1.15rem 1.25rem; min-height: 270px; }}
        .ux-list-title {{ color: var(--bl-heading); font-weight: 900; font-size: 1.08rem; margin-bottom: 0.75rem; }}
        .ux-list-card ul {{ margin: 0; padding-left: 1.2rem; color: var(--bl-muted-text); line-height: 1.65; font-size: 0.92rem; }}
        .inline-kpi {{ padding: 0.85rem 0.95rem; margin-bottom: 0.75rem; }}
        .inline-kpi-label {{ color: var(--bl-subtle-text); font-size: 0.78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; }}
        .inline-kpi-value {{ color: var(--bl-heading); font-size: 1.55rem; font-weight: 900; margin-top: 0.2rem; }}
        .inline-kpi-caption {{ color: var(--bl-muted-text); font-size: 0.82rem; margin-top: 0.25rem; }}
        div[data-testid="stForm"] {{ border: 1px solid var(--bl-border); border-radius: 22px; padding: 1.1rem 1.2rem; background: rgba(15,23,42,0.34); }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 0.35rem; }}
        .stTabs [data-baseweb="tab"] {{ border-radius: 999px; background: rgba(15,23,42,0.72); border: 1px solid var(--bl-border); color: var(--bl-muted-text); padding: 0.45rem 0.85rem; }}
        .stTabs [aria-selected="true"] {{ background: linear-gradient(135deg, rgba(239,68,68,0.28), rgba(249,115,22,0.20)); border-color: rgba(239,68,68,0.45); color: var(--bl-heading); font-weight: 900; }}
        @media (max-width: 900px) {{ .ux-step-grid {{ grid-template-columns: 1fr; }} .feature-group-intro {{ flex-direction: column; }} }}
    </style>
    """


def configure_page(settings: WebSettings) -> None:
    page_icon = str(settings.logo_path) if settings.logo_path.exists() else None
    st.set_page_config(
        page_title=settings.page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_custom_theme(settings: WebSettings) -> None:
    st.markdown(build_custom_css(settings.theme), unsafe_allow_html=True)


def html_escape(value: object) -> str:
    return html.escape(str(value))
