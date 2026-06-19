import html

import pandas as pd
import plotly.express as px
import streamlit as st

<<<<<<< HEAD
from components.assets import icon_title, image_to_base64
from components.auth import require_admin_login
from components.theme import apply_custom_theme, configure_page
from components.ui import (
    render_generated_recommendation_result,
    render_metric_card,
    render_recommendation_report,
    render_tags,
    show_api_error,
    style_plotly,
=======
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
APP_ICON_PATH = "assets/itc_logo.png"
APP_DIR = Path(__file__).resolve().parent          # web/app
WEB_DIR = APP_DIR.parent                           # web
ASSETS_DIR = WEB_DIR / "assets"                    # web/assets
ICONS_DIR = ASSETS_DIR / "icons"                   # web/assets/icons
APP_ICON_PATH = ASSETS_DIR / "itc_logo.png"

st.set_page_config(
    page_title="Blended Learning Recommendation System",
    page_icon=str(APP_ICON_PATH) if APP_ICON_PATH.exists() else None,
    layout="wide",
    initial_sidebar_state="expanded"
>>>>>>> c5241ef (deploy)
)
from components.ux import (
    render_feature_group_intro,
    render_info_panel,
    render_page_hero,
    render_process_steps,
    render_section_header,
    render_split_card,
)
<<<<<<< HEAD
from core.api_client import ApiClient
from core.config import load_web_settings
from core.recommendations import (
    get_nested_recommendation_tags,
    get_recommendation_report,
    parse_tags_to_list,
)
from core.segments import normalize_segment_label, ordered_segments
from core.student_ids import (
    generate_external_student_id,
    is_valid_itc_student_id,
    normalize_itc_student_id,
)
from core.survey_schema import load_survey_schema

settings = load_web_settings()
survey_schema = load_survey_schema(settings.shared_config)
api_client = ApiClient(
    base_url=settings.api_base_url,
    default_get_timeout=settings.default_get_timeout,
    default_post_timeout=settings.default_post_timeout,
)
api_get = api_client.get
api_post = api_client.post

configure_page(settings)
apply_custom_theme(settings)
=======


# -----------------------------
# Helper functions
# -----------------------------

def image_to_base64(image_path: str):
    path = Path(image_path)

    if not path.exists():
        return ""
    
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def icon_svg(svg_path: str, size: int = 18, color: str = "#f8fafc") -> str:
    """
    Return an SVG loaded from a file as an HTML string.
    Use with st.markdown(..., unsafe_allow_html=True).
    """

    path = Path(svg_path)

    if not path.exists():
        return ""

    svg = path.read_text(encoding="utf-8")

    # Set width and height
    if "width=" in svg:
        svg = svg.replace('width="24"', f'width="{size}"')
    else:
        svg = svg.replace("<svg", f'<svg width="{size}"', 1)

    if "height=" in svg:
        svg = svg.replace('height="24"', f'height="{size}"')
    else:
        svg = svg.replace("<svg", f'<svg height="{size}"', 1)

    # Set stroke color when the SVG uses common stroke values
    safe_color = html.escape(color)
    svg = svg.replace('stroke="currentColor"', f'stroke="{safe_color}"')
    svg = svg.replace('stroke="#f8fafc"', f'stroke="{safe_color}"')
    svg = svg.replace('stroke="black"', f'stroke="{safe_color}"')

    # Add inline style
    svg = svg.replace(
        "<svg",
        '<svg style="vertical-align:-3px; margin-right:6px;"',
        1,
    )

    return svg


def icon_span(name: str, text: str, size: int = 18, color: str = "#f8fafc") -> str:
    path = ICONS_DIR / f"{name}.svg"
    return f'{icon_svg(path, size=size, color=color)}<span>{html.escape(text)}</span>'


def icon_title(name: str, text: str, level: int = 3, color: str = "#f8fafc") -> str:
    level = max(1, min(level, 6))
    path = ICONS_DIR / f"{name}.svg"

    return f"""
    <h{level} style="display:flex; align-items:center; gap:0.35rem; color:{color};">
        {icon_svg(path, size=22, color=color)}
        <span>{html.escape(text)}</span>
    </h{level}>
    """

def api_get(endpoint: str, timeout: int = 20):
    """
    GET request helper.

    Returns:
        response, error_type, error_message
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=timeout
        )
        return response, None, None

    except requests.exceptions.ConnectionError as error:
        return None, "connection_error", str(error)

    except requests.exceptions.Timeout as error:
        return None, "timeout_error", str(error)

    except requests.exceptions.RequestException as error:
        return None, "request_error", str(error)


def api_post(endpoint: str, payload: dict, timeout: int = 300):
    """
    POST request helper.

    OpenRouter LLM generation can take time, so this separates real
    connection problems from timeout problems.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=timeout
        )
        return response, None, None

    except requests.exceptions.ConnectionError as error:
        return None, "connection_error", str(error)

    except requests.exceptions.Timeout as error:
        return None, "timeout_error", str(error)

    except requests.exceptions.RequestException as error:
        return None, "request_error", str(error)


def show_api_error(error_type: str, error_message: str = ""):
    """
    Show accurate API/frontend errors instead of always saying
    'Could not connect to FastAPI backend.'
    """
    if error_type == "connection_error":
        st.error(
            "Could not connect to FastAPI backend."
        )

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


def render_metric_card(label, value, subtext=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(str(label))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-small">{html.escape(str(subtext))}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_tags(tags):
    if not tags:
        st.info("No recommendation tags available.")
        return

    try:
        parsed = json.loads(tags) if isinstance(tags, str) else tags

        if isinstance(parsed, list):
            cleaned_tags = [str(tag).strip() for tag in parsed]
        else:
            cleaned_tags = [str(parsed)]

    except Exception:
        cleaned_tags = (
            str(tags)
            .replace("[", "")
            .replace("]", "")
            .replace('"', "")
            .replace("'", "")
            .split(",")
        )
        cleaned_tags = [tag.strip() for tag in cleaned_tags if tag.strip()]

    html_tags = "".join(
        [f'<span class="tag-pill">{html.escape(tag)}</span>' for tag in cleaned_tags]
    )

    st.markdown(html_tags, unsafe_allow_html=True)


def style_plotly(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f8fafc"),
        title_font=dict(size=18, color="#f8fafc"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc")
        )
    )

    fig.update_xaxes(
        gridcolor="rgba(148,163,184,0.15)",
        linecolor="rgba(148,163,184,0.25)"
    )

    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.15)",
        linecolor="rgba(148,163,184,0.25)"
    )

    return fig


def parse_tags_to_list(tags):
    if not tags:
        return []

    try:
        parsed = json.loads(tags) if isinstance(tags, str) else tags
        if isinstance(parsed, list):
            return [str(tag).strip() for tag in parsed if str(tag).strip()]
        return [str(parsed)]
    except Exception:
        return [
            tag.strip()
            for tag in str(tags)
            .replace("[", "")
            .replace("]", "")
            .replace('"', "")
            .replace("'", "")
            .split(",")
            if tag.strip()
        ]


def is_valid_itc_student_id(student_id: str) -> bool:
    """
    Validate official ITC student ID formats.

    Supported examples:
    - Undergraduate: e20123456
    - Master: M061211
    - PhD: e2012345NKH
    - International Program: p20123456
    - ITC Kep Campus: kpe20123456
    - ITC Tbong Khmum Campus: tk20123456
    """
    if not student_id:
        return False

    student_id = student_id.strip()

    patterns = [
        r"^e\d{8}$",
        r"^M\d{6}$",
        r"^e\d{7}[A-Za-z]{3}$",
        r"^p\d{8}$",
        r"^kpe\d{8}$",
        r"^tk\d{8}$",
    ]

    return any(re.match(pattern, student_id, re.IGNORECASE) for pattern in patterns)


def normalize_itc_student_id(student_id: str) -> str:
    """
    Normalize ITC student ID before database lookup.
    This helps match the stored ID format.
    """
    cleaned_id = student_id.strip()

    if cleaned_id.lower().startswith(("kpe", "tk")):
        return cleaned_id.lower()

    if cleaned_id.lower().startswith(("e", "p")):
        prefix = cleaned_id[0].lower()
        rest = cleaned_id[1:]
        digits = "".join([char for char in rest if char.isdigit()])
        letters = "".join([char for char in rest if char.isalpha()])
        return prefix + digits + letters.upper()

    if cleaned_id.lower().startswith("m"):
        return cleaned_id.upper()

    return cleaned_id

def get_nested_recommendation_tags(data: dict):
    """
    Read recommendation tags from either the old flat API response
    or the newer nested NLP extraction response.
    """
    if not isinstance(data, dict):
        return []

    direct_tags = data.get("final_recommendation_tags")
    if direct_tags:
        return direct_tags

    nlp_extraction = data.get("nlp_extraction", {})
    if isinstance(nlp_extraction, dict):
        nested_tags = nlp_extraction.get("final_recommendation_tags")
        if nested_tags:
            return nested_tags

        recommendation_tags = nlp_extraction.get("recommendation_tags")
        if recommendation_tags:
            return recommendation_tags

    return []


def get_recommendation_report(data: dict):
    """
    Read the recommendation report safely from different possible API response shapes.
    """
    if not isinstance(data, dict):
        return ""

    possible_keys = [
        "llm_recommendation_report",
        "recommendation_report",
        "report",
        "generated_report"
    ]

    for key in possible_keys:
        value = data.get(key)
        if value:
            return value

    return ""

def clean_recommendation_text(text):
    """
    Clean recommendation report text before showing it in Streamlit.

    This fixes cases where <br>• appears directly in the UI by allowing
    <br> to render as a real line break inside Markdown tables.
    """
    if not text:
        return ""

    cleaned = str(text)

    # Decode escaped HTML if backend/database saved it as text
    cleaned = cleaned.replace("&lt;br&gt;", "<br>")
    cleaned = cleaned.replace("&lt;br/&gt;", "<br>")
    cleaned = cleaned.replace("&lt;br /&gt;", "<br>")

    # Normalize all break formats
    cleaned = cleaned.replace("<br />", "<br>")
    cleaned = cleaned.replace("<br/>", "<br>")

    return cleaned.strip()


def render_recommendation_report(report):
    """
    Render the recommendation report correctly in Streamlit.
    """
    cleaned_report = clean_recommendation_text(report)

    if cleaned_report:
        st.markdown(cleaned_report, unsafe_allow_html=True)

def render_generated_recommendation_result(data: dict, final_student_id: str, respondent_type: str):
    """
    Render successful recommendation generation result.
    Works with both flat and nested API response formats.
    """
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

    segment_value = (
        data.get("student_segment_label")
        or data.get("segment_label")
        or data.get("segment")
        or "-"
    )

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
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("### Recommendation Tags")
        tags = get_nested_recommendation_tags(data)
        render_tags(tags)

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


# -----------------------------
# Simple Admin Authentication
# -----------------------------
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def require_admin_login():
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if st.session_state["admin_logged_in"]:
        st.sidebar.success("Admin logged in")
        if st.sidebar.button("Logout Admin"):
            st.session_state["admin_logged_in"] = False
            st.rerun()
        return True

    st.markdown(icon_title("lock", "Admin Login Required", level=3), unsafe_allow_html=True)
    st.info("Please log in to access the Admin dashboard.")

    with st.form("admin_login_form"):
        email = st.text_input("Admin Email")
        password = st.text_input("Admin Password", type="password")
        login_clicked = st.form_submit_button("Login")

    if login_clicked:
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            st.session_state["admin_logged_in"] = True
            st.success("Admin login successful.")
            st.rerun()
        else:
            st.error("Invalid admin email or password.")

    return False
>>>>>>> c5241ef (deploy)

# -----------------------------
# Sidebar Navigation
# -----------------------------
<<<<<<< HEAD
logo_path = settings.logo_path
logo_base64 = image_to_base64(logo_path)
=======
logo_base64 = image_to_base64(APP_ICON_PATH)
>>>>>>> c5241ef (deploy)
st.sidebar.markdown(
    f"""
    <div class="sidebar-brand">
        <img src="data:image/png;base64,{logo_base64}" class="sidebar-logo">
        <span>Blended Learning System</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    """
    <div class="sidebar-info-card">
        <div class="sidebar-info-title">Personalized Learning UX</div>
        <div class="sidebar-info-text">
            A cleaner student and admin experience for learner segmentation, recommendations, and thesis demonstration.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

menu_group = st.sidebar.selectbox(
    "Choose Area",
    [
        "Student Portal",
        "Admin",
        "System Information"
    ]
)

if menu_group == "Student Portal":
    page = st.sidebar.radio(
        "Student Pages",
        [
            "ITC Student Lookup",
            "Saved Record Lookup",
            "New Student Input"
        ]
    )

    st.sidebar.info(
        "Use this section for student lookup and new recommendation generation."
    )

elif menu_group == "Admin":
    page = st.sidebar.radio(
        "Admin Pages",
        [
            "Dashboard",
            "Student Records",
            "Survey Analytics"
        ]
    )

    st.sidebar.info(
        "Use this section to monitor records, view analytics, and explain the research process."
    )

else:
    page = "About Prototype"

    st.sidebar.info(
        "System overview, architecture, data flow, and thesis positioning."
    )

health_response, health_error_type, health_error_message = api_get("/")

st.sidebar.markdown("---")
st.sidebar.markdown(icon_title("settings", "Backend Status", level=3), unsafe_allow_html=True)

if health_response and health_response.status_code == 200:
    st.sidebar.markdown(
        '<span class="status-pill-ok">Backend connected</span>',
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        '<span class="status-pill-bad">Backend not connected</span>',
        unsafe_allow_html=True
    )

st.sidebar.markdown("---")

st.sidebar.markdown(
    f"""
    <div class="sidebar-current-page">
        <div class="sidebar-current-label">Current Page</div>
        <div class="sidebar-current-value">{html.escape(page)}</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.caption("Blended Learning Thesis Prototype")
st.sidebar.caption("Built with Streamlit, FastAPI, and PostgreSQL")


# -----------------------------
# Hero section
# -----------------------------
fallback_page_subtitles = {
    "ITC Student Lookup": "Search an official ITC student ID and view the learner recommendation report.",
    "Saved Record Lookup": "Search any stored recommendation record, including demo, external, and ITC IDs.",
    "New Student Input": "Submit blended learning survey responses and generate a new recommendation.",
    "Dashboard": "Monitor total records, learner segments, and recommendation system summary.",
    "Student Records": "Review stored student and respondent recommendation records.",
    "Survey Analytics": "Explore preprocessing, survey features, learner clusters, and recommendation tags.",
    "About Prototype": "Understand the system architecture, thesis positioning, and data flow."
}

page_subtitles = settings.page_subtitles or fallback_page_subtitles
ux_cfg = settings.ux or {}
page_eyebrows = ux_cfg.get("page_eyebrows", {}) if isinstance(ux_cfg, dict) else {}
hero_badges = ux_cfg.get(
    "hero_badges",
    ["Personalized UX", "FastAPI", "K-Modes", "LLM-ready"],
) if isinstance(ux_cfg, dict) else ["Personalized UX", "FastAPI", "K-Modes", "LLM-ready"]

render_page_hero(
    title=page,
    subtitle=page_subtitles.get(page, "Blended learning recommendation prototype."),
    badges=hero_badges,
    eyebrow=page_eyebrows.get(page, "Personalized Blended Learning Prototype"),
)

# Protect Admin pages
if menu_group == "Admin":
    if not require_admin_login(settings.admin_email, settings.admin_password):
        st.stop()


# -----------------------------
# Dashboard
# -----------------------------
if page == "Dashboard":
    render_section_header(
        "Dashboard Summary",
        "Monitor stored recommendation records, learner segments, and backend data summaries in one admin view.",
        eyebrow="Admin workspace",
    )

    response, error_type, error_message = api_get("/students/summary")

    if response is None:
        show_api_error(error_type, error_message)
        st.stop()

    elif response.status_code == 200:
        data = response.json()

        total_students = data.get("total_students", 0)
        total_segments = data.get("total_segments", 0)
        segment_distribution = data.get("segment_distribution", {})

        col1, col2, col3 = st.columns(3)

        with col1:
            render_metric_card(
                "Total Records",
                total_students,
                "ITC + external/demo records in PostgreSQL"
            )

        with col2:
            render_metric_card(
                "Total Segments",
                total_segments,
                "Detected learner profiles"
            )

        with col3:
            render_metric_card(
                "Recommendation Type",
                "Segment-based",
                "K-Modes + rule-based tags"
            )

        render_section_header("Student Segment Distribution", "Compare learner profile counts and proportions from the saved recommendation records.")

        if segment_distribution:
            segment_df = pd.DataFrame(
                list(segment_distribution.items()),
                columns=["Segment", "Count"]
            )

            segment_df["Segment"] = segment_df["Segment"].apply(normalize_segment_label)

            # Group again in case old labels and new labels both exist
            segment_df = (
                segment_df
                .groupby("Segment", as_index=False)["Count"]
                .sum()
            )

            final_segment_order = ordered_segments(
                segment_df["Segment"].dropna().unique().tolist(),
                settings.segment_order,
            )

            segment_df["Segment"] = pd.Categorical(
                segment_df["Segment"],
                categories=final_segment_order,
                ordered=True
            )

            segment_df = segment_df.sort_values("Segment")

            segment_color_map = settings.segment_color_map

            chart_df = segment_df.copy()

            # Do not show Cluster 1 / Cluster 2 anymore
            chart_df["Short Segment"] = chart_df["Segment"].astype(str)

            chart_col1, chart_col2 = st.columns([2.2, 1.1])

            with chart_col1:
                fig_bar = px.bar(
                    chart_df,
                    x="Short Segment",
                    y="Count",
                    title="Distribution of Student Segments",
                    text="Count",
                    color="Segment",
                    color_discrete_map=segment_color_map,
                    category_orders={
                        "Segment": final_segment_order,
                        "Short Segment": final_segment_order
                    }
                )

                fig_bar.update_traces(
                    textposition="outside",
                    marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>Students: %{y}<extra></extra>"
                )

                fig_bar.update_layout(
                    xaxis_title="Student Segment",
                    yaxis_title="Number of Records",
                    title_x=0.01,
                    showlegend=False,
                    height=430
                )

                st.plotly_chart(
                    style_plotly(fig_bar, settings.theme),
                    use_container_width=True
                )

            with chart_col2:
                fig_pie = px.pie(
                    chart_df,
                    names="Short Segment",
                    values="Count",
                    title="Segment Share",
                    hole=0.52,
                    color="Segment",
                    color_discrete_map=segment_color_map,
                    category_orders={
                        "Segment": final_segment_order,
                        "Short Segment": final_segment_order
                    }
                )

                fig_pie.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Records: %{value}<br>"
                        "Share: %{percent}<extra></extra>"
                    )
                )

                fig_pie.update_layout(
                    height=430,
                    title_x=0.15,
                    margin=dict(l=10, r=10, t=70, b=70),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=11)
                    )
                )

                st.plotly_chart(
                    style_plotly(fig_pie, settings.theme),
                    use_container_width=True
                )

            st.markdown("### Segment Data Table")
            st.dataframe(
                segment_df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.warning("No segment distribution data found.")

    else:
        try:
            st.error(response.json().get("detail", "Unable to load dashboard data."))
        except Exception:
            st.error("Unable to load dashboard data.")


# -----------------------------
# Student Records
# -----------------------------
elif page == "Student Records":
    st.markdown(
        icon_title("clipboard", "Student Records", level=3),
        unsafe_allow_html=True
    )

    st.info(
        "Admin view: review all saved student and respondent recommendation records."
    )

    st.write(
        "This page displays all stored recommendation records, including the original seeded students "
        "and any new student/respondent inputs saved to PostgreSQL."
    )

    response, error_type, error_message = api_get("/students/")

    if response is None:
        show_api_error(error_type, error_message)

    elif response.status_code == 200:
        students = response.json()

        if students:
            records_df = pd.DataFrame(students)

            st.markdown("### All Stored Records")

            col1, col2 = st.columns([1, 1])

            with col1:
                search_id = st.text_input(
                    "Search by Student ID",
                    placeholder="Example: e20210528"
                )

            with col2:
                segment_options = ["All"] + sorted(
                    records_df["student_segment_label"].dropna().unique().tolist()
                )
                selected_segment = st.selectbox(
                    "Filter by Segment",
                    segment_options
                )

            filtered_df = records_df.copy()

            if search_id.strip():
                filtered_df = filtered_df[
                    filtered_df["student_id"]
                    .astype(str)
                    .str.contains(search_id.strip(), case=False, na=False)
                ]

            if selected_segment != "All":
                filtered_df = filtered_df[
                    filtered_df["student_segment_label"] == selected_segment
                ]

            st.caption(
                f"Showing {len(filtered_df)} of {len(records_df)} stored records."
            )

            visible_columns = [
                "student_id",
                "student_segment_label",
                "final_recommendation_tags",
                "created_at"
            ]

            existing_columns = [
                column for column in visible_columns
                if column in filtered_df.columns
            ]

            st.dataframe(
                filtered_df[existing_columns],
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No student records found.")

    else:
        try:
            st.error(response.json().get("detail", "Unable to load student records."))
        except Exception:
            st.error("Unable to load student records.")


# -----------------------------
# Survey Analytics
# -----------------------------
elif page == "Survey Analytics":
    data_summary = settings.data_summary
    raw_responses = data_summary.get("raw_responses", "-")
    cleaned_responses = data_summary.get("cleaned_responses", "-")
    excluded_responses = data_summary.get("excluded_responses", "-")
    clustering_features = data_summary.get("clustering_features", 33)

    st.markdown(
        '<div class="section-title"> Survey Analytics</div>',
        unsafe_allow_html=True
    )

    st.info(
        "Admin view: explain preprocessing, cleaned survey data, clustering features, and segment interpretation."
    )

    st.write(
        "This page summarizes the survey preparation process and selected analytics that support "
        "the learner segmentation and recommendation prototype."
    )

    st.markdown("### Data Preparation Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            "Raw Responses",
            raw_responses,
            "Initial survey export rows"
        )

    with col2:
        render_metric_card(
            "Cleaned Responses",
            cleaned_responses,
            "Valid cleaned records"
        )

    with col3:
        render_metric_card(
            "Excluded Responses",
            excluded_responses,
            "Records removed during cleaning"
        )

    with col4:
        render_metric_card(
            "Clustering Features",
            clustering_features,
            "Survey features used by K-Modes"
        )

    st.markdown(
        f"""
The dataset was not used directly in raw form. The current project data lock contains **{raw_responses} raw export rows**.  
After automated cleaning and preprocessing, **{cleaned_responses} valid cleaned responses** remain for clustering and recommendation model development.
"""
    )

    st.markdown("### Automated Cleaning and Preprocessing Pipeline")

    pipeline_steps = pd.DataFrame(
        [
            {
                "Step": 1,
                "Stage": "Drop columns",
                "Description": "Remove unnecessary columns not used for analysis."
            },
            {
                "Step": 2,
                "Stage": "Rename columns",
                "Description": "Convert raw survey column names into standardized feature names."
            },
            {
                "Step": 3,
                "Stage": "Remove invalid responses",
                "Description": "Keep only valid survey submissions."
            },
            {
                "Step": 4,
                "Stage": "Compute response time",
                "Description": "Calculate completion time from survey start and end timestamps."
            },
            {
                "Step": 5,
                "Stage": "Standardize respondent IDs",
                "Description": "Keep valid ITC IDs and generate external IDs for non-ITC respondents."
            },
            {
                "Step": 6,
                "Stage": "Remove duplicates",
                "Description": "Remove duplicate ITC submissions to keep one record per student."
            },
            {
                "Step": 7,
                "Stage": "Clean categorical values",
                "Description": "Standardize text fields such as gender, province, major, and faculty."
            },
            {
                "Step": 8,
                "Stage": "Flag speeders",
                "Description": "Flag responses completed in under 3 minutes."
            },
            {
                "Step": 9,
                "Stage": "Encode Likert responses",
                "Description": "Convert ordinal survey answers into numeric values for clustering."
            },
        ]
    )

    st.dataframe(
        pipeline_steps,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Respondent Composition")

    respondent_df = pd.DataFrame(
        {
            "Respondent Group": ["ITC Students", "Non-ITC / External Respondents"],
            "Count": [557, 31]
        }
    )

    fig_respondents = px.pie(
        respondent_df,
        names="Respondent Group",
        values="Count",
        title="ITC vs Non-ITC Respondent Composition",
        hole=0.45
    )

    fig_respondents.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>"
    )

    fig_respondents.update_layout(
        height=420,
        title_x=0.05,
        margin=dict(l=20, r=20, t=70, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(
        style_plotly(fig_respondents, settings.theme),
        use_container_width=True
    )

   
    st.markdown("### Top Recommendation Tags")

    records_response, records_error_type, records_error_message = api_get("/students/")

    if records_response and records_response.status_code == 200:
        records = records_response.json()

        tag_counts = {}

        for record in records:
            tags = parse_tags_to_list(record.get("final_recommendation_tags"))
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if tag_counts:
            tag_df = pd.DataFrame(
                list(tag_counts.items()),
                columns=["Recommendation Tag", "Count"]
            ).sort_values("Count", ascending=False)

            fig_tags = px.bar(
                tag_df,
                x="Recommendation Tag",
                y="Count",
                text="Count",
                title="Most Common Recommendation Tags"
            )

            fig_tags.update_traces(
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"
            )

            fig_tags.update_layout(
                height=430,
                xaxis_title="Recommendation Tag",
                yaxis_title="Frequency",
                title_x=0.01,
                showlegend=False
            )

            st.plotly_chart(
                style_plotly(fig_tags, settings.theme),
                use_container_width=True
            )

            st.dataframe(
                tag_df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No recommendation tags available yet.")

    else:
        st.warning("Could not load recommendation tags from PostgreSQL records.")

    st.markdown("### Interpretation")

    st.markdown(
        f"""
The analytics page supports the research explanation behind the prototype. It shows that the system is based on a cleaned dataset, not raw survey responses directly. The current reduction from **{raw_responses} raw export rows** to **{cleaned_responses} valid cleaned responses** demonstrates that the automated cleaning and preprocessing pipeline was applied before clustering.

The preprocessing pipeline includes column selection, column renaming, invalid response removal, response-time calculation, respondent ID standardization, duplicate handling, categorical standardization, speeder flagging, and ordinal encoding. After these steps, the cleaned dataset was used to train the K-Modes learner segmentation model.

The feature-group and cluster-comparison charts summarize the behavioral patterns behind the learner segments. The highly engaged segment represents more active learners, while the moderately engaged segment represents more passive or moderate learners. The interpretation is based on the segment profile rather than the numeric cluster ID, because K-Modes cluster IDs can change across dataset versions.
"""
    )

# -----------------------------
# ITC Student Lookup
# -----------------------------
elif page == "ITC Student Lookup":
    render_section_header(
        "ITC Student Lookup",
        "Enter an official ITC student ID to retrieve the learner profile and recommendation report.",
        eyebrow="Student-facing lookup",
    )
    render_process_steps(ux_cfg.get("student_lookup_steps", []))
    render_info_panel(
        "Supported ID formats",
        "Undergraduate e20123456, Master M061211, PhD e2012345NKH, International Program p20123456, Kep Campus kpe20123456, Tbong Khmum tk20123456.",
    )

    student_id = st.text_input(
        "ITC Student ID",
        placeholder="Example: e20210528, M061211, p20123456, kpe20123456"
    )

    if st.button("Get Student Recommendation", type="primary", use_container_width=False):
        raw_id = student_id.strip()

        if not raw_id:
            st.warning("Please enter an ITC student ID.")

        elif not is_valid_itc_student_id(raw_id):
            st.warning(
                "This lookup is for official ITC student IDs only. "
                "Valid examples include e20123456, M061211, e2012345NKH, "
                "p20123456, kpe20123456, or tk20123456."
            )

        else:
            cleaned_id = normalize_itc_student_id(raw_id)

            response, error_type, error_message = api_get(f"/students/{cleaned_id}")
            if response is None:
                show_api_error(error_type, error_message)

            elif response.status_code == 200:
                data = response.json()

                st.success("ITC student record found.")

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("### Student Profile")

                    st.markdown(
                        f"""
                        <div class="info-card">
                            <b>ITC Student ID:</b> {html.escape(str(data.get("student_id", "-")))}<br><br>
                            <b>Assigned Segment:</b> {html.escape(str(data.get("student_segment_label", "-")))}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown("### Recommendation Tags")
                    render_tags(data.get("final_recommendation_tags"))

                st.markdown("### Recommendation Report")

                report = data.get("llm_recommendation_report")

                if report:
                    render_recommendation_report(report)
                else:
                    st.info("No recommendation report found.")

            elif response.status_code == 404:
                st.error(
                    f"ITC student ID '{cleaned_id}' was not found in the recommendation database."
                )

                st.info(
                    "Your ID may not be included in the current database yet. "
                    "You can generate a recommendation now through the New Student Input page, "
                    "or complete the official survey form if you have not submitted your responses."
                )

                survey_url = "https://ee.kobotoolbox.org/x/U9fjVLLS"

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown(
                        """
                        <div class="info-card">
                            <b>Option 1: Generate recommendation now</b><br><br>
                            Go to <b>Student Portal → New Student Input</b>, enter your ITC ID,
                            answer the survey-based questions, and submit the form.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(
                        """
                        <div class="info-card">
                            <b>Option 2: Complete the survey</b><br><br>
                            If you have not filled in the blended learning survey yet,
                            complete the official survey form first.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.link_button("Open Survey Form", survey_url)

            else:
                try:
                    st.error(response.json().get("detail", "Unable to retrieve student record."))
                except Exception:
                    st.error("Unable to retrieve student record.")


# -----------------------------
# Saved Record Lookup
# -----------------------------
elif page == "Saved Record Lookup":
    render_section_header(
        "Saved Record Lookup",
        "Search any saved recommendation record by ID, including ITC, demo/test, and external respondent records.",
        eyebrow="Record retrieval",
    )
    render_info_panel(
        "When to use this page",
        "Use this page for records such as testllm6, demo_001, ext_8f3a91c204, or official ITC IDs. The ITC Student Lookup page remains restricted to official ITC IDs only.",
    )

    record_id = st.text_input(
        "Saved Record ID",
        placeholder="Example: testllm6, demo_001, ext_8f3a91c204, e20210528"
    )

    if st.button("Search Saved Record", type="primary", use_container_width=False):
        cleaned_id = record_id.strip()

        if not cleaned_id:
            st.warning("Please enter a saved record ID.")

        else:
            response, error_type, error_message = api_get(f"/students/{cleaned_id}")

            if response is None:
                show_api_error(error_type, error_message)

            elif response.status_code == 200:
                data = response.json()

                st.success("Saved record found.")

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("### Saved Record Profile")

                    student_id_value = data.get("student_id", cleaned_id)

                    segment_value = (
                        data.get("student_segment_label")
                        or data.get("segment_label")
                        or data.get("segment")
                        or "-"
                    )

                    generation_source = data.get("llm_generation_source", "-")

                    st.markdown(
                        f"""
                        <div class="info-card">
                            <b>Saved ID:</b> {html.escape(str(student_id_value))}<br><br>
                            <b>Assigned Segment:</b> {html.escape(str(segment_value))}<br><br>
                            <b>Generation Source:</b> {html.escape(str(generation_source))}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown("### Recommendation Tags")
                    render_tags(get_nested_recommendation_tags(data))

                st.markdown("### Recommendation Report")

                report = get_recommendation_report(data)

                if report:
                    render_recommendation_report(report)
                else:
                    st.info("No recommendation report found.")

                    with st.expander("Show raw FastAPI response"):
                        st.json(data)

            elif response.status_code == 404:
                st.error(f"No saved record found for ID: `{cleaned_id}`")

                st.info(
                    "Check the ID spelling, or create a new record from the New Student Input page."
                )

            else:
                st.error(f"FastAPI returned status code: {response.status_code}")

                try:
                    st.json(response.json())
                except Exception:
                    st.code(response.text)




# -----------------------------
# New Student Input
# -----------------------------
elif page == "New Student Input":
    render_section_header(
        "New Student / Respondent Input",
        "A guided recommendation flow using the same 33 survey features as the thesis model.",
        eyebrow="Personalized input journey",
    )
    render_process_steps(ux_cfg.get("new_input_steps", []))
    render_info_panel(
        "ID rule",
        "ITC students can use their official ITC ID. Non-ITC or external respondents can leave the ID blank and the system will generate an internal external ID.",
        tone="warning",
    )

    feature_labels = survey_schema.feature_labels
    feature_questions = survey_schema.feature_questions
    feature_scales = survey_schema.scales
    ordinal_column_scales = survey_schema.ordinal_column_scales

    def get_scale_note(feature_key: str):
        scale_name = ordinal_column_scales.get(feature_key, "AGREE5")
        scale_map = feature_scales[scale_name]
        return " | ".join([f"{value} = {label}" for label, value in scale_map.items()])

    def render_scaled_feature_input(feature_key: str):
        scale_name = ordinal_column_scales.get(feature_key, "AGREE5")
        scale_map = feature_scales[scale_name]
        scale_options = list(scale_map.keys())

        st.markdown(
            f"""
            <div class="question-card">
                <div class="question-label">{html.escape(feature_labels[feature_key])}</div>
                <div class="question-text">{html.escape(feature_questions[feature_key])}</div>
                <div class="scale-note">{html.escape(get_scale_note(feature_key))}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        selected_label = st.selectbox(
            "Choose an answer",
            options=scale_options,
            index=2,
            key=f"single_select_{feature_key}",
            label_visibility="collapsed"
        )

        numeric_value = scale_map[selected_label]
        return numeric_value

    def render_feature_group(features):
        col1, col2 = st.columns(2)

        for index, feature in enumerate(features):
            with col1 if index % 2 == 0 else col2:
                responses[feature] = render_scaled_feature_input(feature)

    # IMPORTANT:
    # Keep respondent_type outside the form so the ID field updates immediately.
    respondent_type = st.radio(
        "Respondent Type",
        ["ITC Student", "Non-ITC / External Respondent", "Demo/Test User"],
        horizontal=True,
        key="respondent_type_selector"
    )

    if respondent_type == "ITC Student":
        id_label = "ITC Student ID"
        id_placeholder = "Example: e20210320"
        id_help = "Enter an official ITC student ID."

    elif respondent_type == "Non-ITC / External Respondent":
        id_label = "External Respondent ID"
        id_placeholder = "Optional. Leave blank to auto-generate an external ID."
        id_help = "External respondents may leave this blank. The system will generate an ID automatically."

    else:
        id_label = "Demo/Test ID"
        id_placeholder = "Example: TEST001 or demo_001"
        id_help = "Enter a demo or testing ID for prototype testing."

    with st.form("new_student_form"):
        student_id = st.text_input(
            id_label,
            placeholder=id_placeholder,
            help=id_help,
            key=f"student_id_input_{respondent_type}"
        )

        st.markdown("### Student Learning Profile Questions")
        st.caption(
            "Choose one answer for each question. The system automatically converts your answer into a numeric value for the model."
        )

        responses = {}

        tabs = st.tabs([
            "Content Use",
            "Interaction",
            "Lecturer Support",
            "Self-Regulation",
            "Benefits"
        ])

        feature_keys = survey_schema.feature_keys

        with tabs[0]:
            render_feature_group_intro(
                "Content and Digital Learning Resources",
                "How often the student uses digital learning materials.",
                count=len(feature_keys[0:6]),
            )
            render_feature_group(feature_keys[0:6])

        with tabs[1]:
            render_feature_group_intro(
                "Interaction and Learning Experience",
                "Participation, collaboration, comfort, community, and course integration.",
                count=len(feature_keys[6:12]),
            )
            render_feature_group(feature_keys[6:12])

        with tabs[2]:
            render_feature_group_intro(
                "Lecturer Support",
                "Perceived lecturer instructions, support, tools, feedback, and interaction.",
                count=len(feature_keys[12:17]),
            )
            render_feature_group(feature_keys[12:17])

        with tabs[3]:
            render_feature_group_intro(
                "Self-Regulation and Learning Readiness",
                "Study habits, readiness, technical issues, LMS usability, satisfaction, and career preparation.",
                count=len(feature_keys[17:27]),
            )
            render_feature_group(feature_keys[17:27])

        with tabs[4]:
            render_feature_group_intro(
                "Perceived Benefits of Blended Learning",
                "How beneficial students find different aspects of blended learning.",
                count=len(feature_keys[27:33]),
            )
            render_feature_group(feature_keys[27:33])

        st.markdown("### Open-ended Responses")

        strengths = st.text_area(
            "In your opinion, what are the biggest strengths or most positive aspects of the blended learning approach?",
            height=120,
            placeholder="Example: I like flexible learning and recorded lectures.",
            key="open_strengths",
        )

        challenges = st.text_area(
            "What are your biggest challenges with blended learning, and what specific suggestions do you have for the university and lecturers to improve it?",
            height=120,
            placeholder="Example: I need more interaction or clearer instructions.",
            key="open_challenges_suggestions",
        )

        submitted = st.form_submit_button(
            "Generate Personalized Recommendation",
            type="primary"
        )
    if submitted:
        raw_student_id = student_id.strip()

        if respondent_type == "ITC Student" and not raw_student_id:
            st.warning("Please enter the ITC student ID.")

        elif respondent_type == "ITC Student" and not is_valid_itc_student_id(raw_student_id):
            st.warning(
                "Please enter a valid official ITC student ID. "
                "Examples: e20123456, M061211, e2012345NKH, p20123456, kpe20123456, tk20123456."
            )

        elif respondent_type == "Demo/Test User" and not raw_student_id:
            st.warning("Please enter a demo/test ID.")

        else:
            if respondent_type == "ITC Student":
                final_student_id = normalize_itc_student_id(raw_student_id)

            elif respondent_type == "Non-ITC / External Respondent" and not raw_student_id:
                final_student_id = generate_external_student_id()

            else:
                final_student_id = raw_student_id

            payload = {
                "student_id": final_student_id,
                "responses": responses,
                "strengths_positive_aspects": strengths,
                "challenges_suggestions": challenges
            }

            with st.spinner("Analyzing the learner profile and generating a recommendation..."):
                response, error_type, error_message = api_post(
                    "/recommendations/generate",
                    payload,
                    timeout=300
                )

            if response is None:
                show_api_error(error_type, error_message)

                st.info(
                    "Important: if this was a timeout, the recommendation may still have been saved. "
                    "Before clicking Generate again, search this ID in ITC Student Lookup or Student Records:"
                )
                st.code(final_student_id)

            elif response.status_code in [200, 201]:
                data = response.json()

                render_generated_recommendation_result(
                    data=data,
                    final_student_id=final_student_id,
                    respondent_type=respondent_type
                )

            elif response.status_code == 409:
                st.warning(
                    "This student ID already exists in the database. "
                
                )

                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "")

                    if detail:
                        st.info(str(detail))

                except Exception:
                    pass

                st.info("Search this ID in Student Portal → Saved Record Lookup instead of clicking Generate again:")
                st.code(final_student_id)

            elif response.status_code == 422:
                st.error("FastAPI rejected the submitted data because the request format is invalid.")
                st.code(response.text)

            elif response.status_code >= 500:
                st.error(
                    "FastAPI backend returned a server error. "
                    "Check the uvicorn terminal for the full Python traceback."
                )
                st.code(response.text)

            else:
                st.error(f"FastAPI returned unexpected status code: {response.status_code}")

                try:
                    st.json(response.json())
                except Exception:
                    st.code(response.text)

# -----------------------------
# About Prototype
# -----------------------------
elif page == "About Prototype":
    data_summary = settings.data_summary
    raw_responses = data_summary.get("raw_responses", "the current raw export")
    cleaned_responses = data_summary.get("cleaned_responses", "the current cleaned dataset")
    clustering_features = data_summary.get("clustering_features", 33)

    render_section_header(
        "About the Prototype",
        "Purpose, architecture, data flow, and thesis positioning of the blended learning recommendation system.",
        eyebrow="System overview",
    )

    col1, col2 = st.columns(2)

    with col1:
        render_split_card(
            "System Architecture",
            ux_cfg.get("about_architecture", [])
        )

    with col2:
        render_split_card(
            "Prototype Capabilities",
            ux_cfg.get("about_capabilities", [])
        )

    st.markdown("---")

    st.markdown("### Thesis Positioning")
    st.markdown(
        f"""
The prototype demonstrates a **segment-based personalized recommendation system** for blended learning.  
A saved **K-Modes clustering model** assigns new submissions to the closest learned learner segment based on the same **{clustering_features} survey features** used during model training.

The current project data lock contains **{raw_responses} raw export rows**. After the automated preprocessing pipeline, **{cleaned_responses} valid cleaned responses** remain for clustering and recommendation model development. These values are read from the frontend configuration block, so the web text can be updated safely when the data lock changes.

Because the original data collection included both ITC students and non-ITC/external respondents, the prototype uses a unified internal `student_id` field. Official ITC IDs are preserved for student lookup, while non-ITC respondents may receive generated external IDs such as `ext_8f3a91c204` for backend storage and future analysis.

The public lookup function is limited to ITC students because they have official IDs that are known and stable. External respondent IDs are treated as internal database identifiers rather than user-facing lookup credentials.

The Admin section is included to separate system monitoring and research analytics from the student-facing portal. For the current thesis prototype, authentication is optional and can be added later if the system is expanded.

The system does **not automatically retrain** the clustering model during prediction. Instead, new inputs are stored in PostgreSQL and can be combined with the original survey dataset later for future model refinement or retraining.
"""
    )

    st.markdown("### Data Flow")
    st.markdown(
        f"""
**Original Dataset Preparation**  
→ Current raw export rows: {raw_responses}  
→ Automated preprocessing pipeline  
→ Current valid cleaned responses: {cleaned_responses}  
→ {clustering_features} clustering features  
→ K-Modes learner segmentation

**Student Portal Flow**  
→ ITC student lookup or new student/respondent input  
→ FastAPI backend  
→ PostgreSQL recommendation record  
→ Streamlit profile and recommendation display

**Admin Flow**  
→ Dashboard summary  
→ Student records monitoring  
→ Survey analytics  
→ Segment interpretation  
→ Recommendation tag review

**New Student / Respondent Input**  
→ ID type selection  
→ 33 survey responses  
→ FastAPI backend  
→ Saved K-Modes model  
→ Assigned learner segment  
→ Recommendation tags and report  
→ PostgreSQL storage  
→ Streamlit display

**ITC Student Lookup**  
→ Official ITC student ID  
→ FastAPI backend  
→ PostgreSQL recommendation record  
→ Streamlit profile and recommendation display
"""
    )


# -----------------------------
# Footer
# -----------------------------
st.markdown(
    """
    <div class="footer-box">
        <b>Prototype Note:</b> This system provides segment-based personalized recommendations for blended learning.
        It supports both ITC students and non-ITC/external respondents.
    </div>
    """,
    unsafe_allow_html=True
)