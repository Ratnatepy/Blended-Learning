import os
import re
import json
import html
import uuid
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Blended Learning Recommendation System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Custom Theme CSS
# -----------------------------
st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(239, 68, 68, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.10), transparent 28%),
                linear-gradient(135deg, #020617 0%, #0f172a 55%, #111827 100%);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #020617 0%, #111827 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: #f8fafc !important;
        }

        h1, h2, h3 {
            color: #f8fafc;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        p, label, span, div {
            color: #f8fafc;
        }

        .hero-box {
            padding: 1.5rem 2rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(30,41,59,0.96));
            color: white;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255,255,255,0.10);
            box-shadow: 0 18px 45px rgba(0,0,0,0.30);
        }

        .hero-title {
            font-size: 2.15rem;
            line-height: 1.2;
            font-weight: 900;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            color: #cbd5e1;
            font-size: 1rem;
            margin-bottom: 0.9rem;
        }

        .hero-badge {
            display: inline-block;
            color: #fecaca;
            background: rgba(239,68,68,0.12);
            border: 1px solid rgba(239,68,68,0.35);
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            margin: 0.15rem 0.35rem 0.15rem 0;
        }

        .section-title {
            font-size: 1.55rem;
            font-weight: 800;
            margin-top: 0.2rem;
            margin-bottom: 1rem;
            color: #ffffff;
        }

        .metric-card,
        .info-card,
        .footer-box {
            background: rgba(15, 23, 42, 0.92);
            border: 1px solid rgba(255,255,255,0.09);
            box-shadow: 0 12px 32px rgba(0,0,0,0.28);
            backdrop-filter: blur(8px);
        }

        .metric-card {
            padding: 1.15rem 1.25rem;
            border-radius: 18px;
            margin-bottom: 1rem;
            min-height: 132px;
        }

        .metric-label {
            font-size: 0.92rem;
            color: #cbd5e1;
            margin-bottom: 0.45rem;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 900;
            color: #ffffff;
            line-height: 1.1;
        }

        .metric-small {
            font-size: 0.84rem;
            color: #94a3b8;
            margin-top: 0.55rem;
        }

        .info-card {
            padding: 1.2rem 1.35rem;
            border-radius: 18px;
            margin-bottom: 1rem;
            color: #e5e7eb;
        }

        .tag-pill {
            display: inline-block;
            background: rgba(239,68,68,0.14);
            color: #fecaca;
            border: 1px solid rgba(239,68,68,0.42);
            padding: 0.38rem 0.78rem;
            border-radius: 999px;
            margin: 0.2rem 0.35rem 0.2rem 0;
            font-size: 0.85rem;
            font-weight: 750;
        }

        .status-pill-ok {
            display: inline-block;
            color: #bbf7d0;
            background: rgba(34,197,94,0.13);
            border: 1px solid rgba(34,197,94,0.35);
            border-radius: 999px;
            padding: 0.35rem 0.65rem;
            font-size: 0.82rem;
            font-weight: 800;
        }

        .status-pill-bad {
            display: inline-block;
            color: #fecaca;
            background: rgba(239,68,68,0.13);
            border: 1px solid rgba(239,68,68,0.35);
            border-radius: 999px;
            padding: 0.35rem 0.65rem;
            font-size: 0.82rem;
            font-weight: 800;
        }

        .footer-box {
            margin-top: 2rem;
            padding: 1rem 1.2rem;
            border-radius: 16px;
            color: #cbd5e1;
            font-size: 0.92rem;
        }

        .stButton > button {
            background: linear-gradient(135deg, #ef4444, #f97316);
            color: white;
            border: none;
            border-radius: 13px;
            padding: 0.62rem 1.25rem;
            font-weight: 800;
            box-shadow: 0 8px 22px rgba(239,68,68,0.28);
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #dc2626, #ea580c);
            color: white;
            border: none;
            transform: translateY(-1px);
        }

        .stTextInput input,
        .stTextArea textarea {
            background-color: #111827;
            color: #f8fafc;
            border: 1px solid #334155;
            border-radius: 12px;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border: 1px solid #ef4444;
            box-shadow: 0 0 0 1px #ef4444;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
        }

        div[data-testid="stPlotlyChart"] {
            background: rgba(15,23,42,0.55);
            border-radius: 18px;
            padding: 0.5rem;
            border: 1px solid rgba(255,255,255,0.06);
        }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Helper functions
# -----------------------------
def api_get(endpoint: str):
    try:
        return requests.get(f"{API_BASE_URL}{endpoint}", timeout=15)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return None


def api_post(endpoint: str, payload: dict):
    try:
        return requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=15)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return None


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
        r"^e\d{8}$",              # Undergraduate
        r"^M\d{6}$",              # Master
        r"^e\d{7}[A-Za-z]{3}$",   # PhD
        r"^p\d{8}$",              # International Program
        r"^kpe\d{8}$",            # ITC Kep Campus
        r"^tk\d{8}$",             # ITC Tbong Khmum Campus
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


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## 🧭 Navigation")

page = st.sidebar.radio(
    "",
    [
        "📊 Dashboard",
        "👥 Student Records",
        "📈 Survey Analytics",
        "🔍 ITC Student Lookup",
        "📝 New Student Input",
        "ℹ️ About Prototype"
    ]
)

health_response = api_get("/")

if health_response and health_response.status_code == 200:
    st.sidebar.markdown(
        '<span class="status-pill-ok">● Backend connected</span>',
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        '<span class="status-pill-bad">● Backend not connected</span>',
        unsafe_allow_html=True
    )

st.sidebar.markdown("---")
st.sidebar.caption("🎓 Blended Learning Thesis Prototype")
st.sidebar.caption("Streamlit + FastAPI + PostgreSQL")


# -----------------------------
# Hero section
# -----------------------------
st.markdown(
    """
    <div class="hero-box">
        <div class="hero-title">🎓 Blended Learning Student Recommendation System</div>
        <div class="hero-subtitle">
            Student segmentation and personalized recommendation prototype demo
        </div>
        <div>
            <span class="hero-badge">📊 Streamlit UI</span>
            <span class="hero-badge">⚙️ FastAPI Backend</span>
            <span class="hero-badge">🗄️ PostgreSQL Database</span>
            <span class="hero-badge">🧩 Segment-based Recommendation</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Dashboard
# -----------------------------
if page == "📊 Dashboard":
    st.markdown(
        '<div class="section-title">📊 Dashboard Summary</div>',
        unsafe_allow_html=True
    )

    response = api_get("/students/summary")

    if response is None:
        st.error("Could not connect to FastAPI backend.")
        st.stop()

    if response.status_code == 200:
        data = response.json()

        total_students = data.get("total_students", 0)
        total_segments = data.get("total_segments", 0)
        segment_distribution = data.get("segment_distribution", {})

        col1, col2, col3 = st.columns(3)

        with col1:
            render_metric_card(
                "👥 Total Records",
                total_students,
                "ITC + external/demo records in PostgreSQL"
            )

        with col2:
            render_metric_card(
                "🧩 Total Segments",
                total_segments,
                "Detected learner profiles"
            )

        with col3:
            render_metric_card(
                "🎯 Recommendation Type",
                "Segment-based",
                "K-Modes + rule-based tags"
            )

        st.markdown("### 📈 Student Segment Distribution")

        if segment_distribution:
            segment_df = pd.DataFrame(
                list(segment_distribution.items()),
                columns=["Segment", "Count"]
            ).sort_values("Count", ascending=False)

            segment_color_map = {
                "Cluster 2: Highly Engaged (Active) Learners": "#22c55e",
                "Cluster 1: Moderately Engaged (Passive) Learners": "#ef4444"
            }

            segment_label_map = {
                "Cluster 2: Highly Engaged (Active) Learners": "Cluster 2 (Active)",
                "Cluster 1: Moderately Engaged (Passive) Learners": "Cluster 1 (Passive)"
            }

            chart_df = segment_df.copy()
            chart_df["Short Segment"] = chart_df["Segment"].map(segment_label_map)
            chart_df["Short Segment"] = chart_df["Short Segment"].fillna(chart_df["Segment"])

            chart_col1, chart_col2 = st.columns([2.2, 1.1])

            with chart_col1:
                fig_bar = px.bar(
                    chart_df,
                    x="Short Segment",
                    y="Count",
                    title="Distribution of Student Segments",
                    text="Count",
                    color="Segment",
                    color_discrete_map=segment_color_map
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
                    style_plotly(fig_bar),
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
                    color_discrete_map=segment_color_map
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
                    style_plotly(fig_pie),
                    use_container_width=True
                )

            st.markdown("### 📋 Segment Data Table")
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
elif page == "👥 Student Records":
    st.markdown(
        '<div class="section-title">👥 Student Records</div>',
        unsafe_allow_html=True
    )

    st.write(
        "This page displays all stored recommendation records, including the original seeded students "
        "and any new student/respondent inputs saved to PostgreSQL."
    )

    response = api_get("/students/")

    if response is None:
        st.error("Could not connect to FastAPI backend.")

    elif response.status_code == 200:
        students = response.json()

        if students:
            records_df = pd.DataFrame(students)

            st.markdown("### 📋 All Stored Records")

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
elif page == "📈 Survey Analytics":
    st.markdown(
        '<div class="section-title">📈 Survey Analytics</div>',
        unsafe_allow_html=True
    )

    st.write(
        "This page summarizes the survey preparation process and selected analytics that support "
        "the learner segmentation and recommendation prototype."
    )

    st.markdown("### 🧹 Data Preparation Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            "Raw Responses",
            445,
            "Initial survey submissions"
        )

    with col2:
        render_metric_card(
            "Cleaned Responses",
            420,
            "Valid records used for modeling"
        )

    with col3:
        render_metric_card(
            "Excluded Responses",
            25,
            "Invalid or duplicate records removed"
        )

    with col4:
        render_metric_card(
            "Clustering Features",
            33,
            "Survey features used by K-Modes"
        )

    st.markdown(
        """
The dataset was not used directly in raw form. The original survey contained **445 responses**.  
After automated cleaning and preprocessing, **420 valid responses** remained for clustering and recommendation model development.
"""
    )

    st.markdown("### 🔄 Automated Cleaning and Preprocessing Pipeline")

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

    st.markdown("### 👥 Respondent Composition")

    respondent_df = pd.DataFrame(
        {
            "Respondent Group": ["ITC Students", "Non-ITC / External Respondents"],
            "Count": [390, 30]
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
        style_plotly(fig_respondents),
        use_container_width=True
    )

    st.markdown("### 📊 Average Score by Feature Group")

    feature_group_df = pd.DataFrame(
        {
            "Feature Group": [
                "Content Use",
                "Interaction",
                "Lecturer Support",
                "Self-Regulation",
                "Perceived Benefits"
            ],
            "Average Score": [
                3.85,
                3.42,
                3.76,
                3.58,
                3.91
            ]
        }
    )

    fig_feature_group = px.bar(
        feature_group_df,
        x="Feature Group",
        y="Average Score",
        text="Average Score",
        title="Average Survey Score by Feature Group"
    )

    fig_feature_group.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Average Score: %{y:.2f}<extra></extra>"
    )

    fig_feature_group.update_layout(
        height=430,
        yaxis_range=[0, 5],
        xaxis_title="Feature Group",
        yaxis_title="Average Likert Score",
        title_x=0.01
    )

    st.plotly_chart(
        style_plotly(fig_feature_group),
        use_container_width=True
    )

    st.markdown("### 🧩 Cluster Comparison by Feature Group")

    cluster_compare_df = pd.DataFrame(
        {
            "Feature Group": [
                "Content Use", "Interaction", "Lecturer Support", "Self-Regulation", "Perceived Benefits",
                "Content Use", "Interaction", "Lecturer Support", "Self-Regulation", "Perceived Benefits"
            ],
            "Cluster": [
                "Cluster 1 (Passive)", "Cluster 1 (Passive)", "Cluster 1 (Passive)", "Cluster 1 (Passive)", "Cluster 1 (Passive)",
                "Cluster 2 (Active)", "Cluster 2 (Active)", "Cluster 2 (Active)", "Cluster 2 (Active)", "Cluster 2 (Active)"
            ],
            "Average Score": [
                3.30, 3.05, 3.35, 3.22, 3.40,
                4.10, 3.85, 4.05, 3.92, 4.20
            ]
        }
    )

    cluster_color_map = {
        "Cluster 1 (Passive)": "#ef4444",
        "Cluster 2 (Active)": "#22c55e"
    }

    fig_cluster_compare = px.bar(
        cluster_compare_df,
        x="Feature Group",
        y="Average Score",
        color="Cluster",
        barmode="group",
        text="Average Score",
        title="Cluster 1 vs Cluster 2 Average Scores",
        color_discrete_map=cluster_color_map
    )

    fig_cluster_compare.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{fullData.name}<br>Average Score: %{y:.2f}<extra></extra>"
    )

    fig_cluster_compare.update_layout(
        height=450,
        yaxis_range=[0, 5],
        xaxis_title="Feature Group",
        yaxis_title="Average Likert Score",
        title_x=0.01
    )

    st.plotly_chart(
        style_plotly(fig_cluster_compare),
        use_container_width=True
    )

    st.markdown("### 🏷️ Top Recommendation Tags")

    records_response = api_get("/students/")

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
                style_plotly(fig_tags),
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

    st.markdown("### 📝 Interpretation")

    st.markdown(
        """
The analytics page supports the research explanation behind the prototype. It shows that the system is based on a cleaned dataset, not raw survey responses directly. The reduction from **445 raw responses** to **420 valid responses** demonstrates that the automated cleaning and preprocessing pipeline was applied before clustering.

The preprocessing pipeline includes column selection, column renaming, invalid response removal, response-time calculation, respondent ID standardization, duplicate handling, categorical standardization, speeder flagging, and ordinal encoding. After these steps, the cleaned dataset was used to train the K-Modes learner segmentation model.

The feature-group and cluster-comparison charts summarize the behavioral patterns behind the learner segments. Cluster 2 is interpreted as more active/highly engaged, while Cluster 1 is interpreted as more moderate/passive. These segment interpretations are then used by the recommendation logic.
"""
    )


# -----------------------------
# ITC Student Lookup
# -----------------------------
elif page == "🔍 ITC Student Lookup":
    st.markdown(
        '<div class="section-title">🔍 ITC Student Lookup</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Enter an official ITC student ID to retrieve the learner profile and recommendation report."
    )

    st.caption(
        "Supported formats: Undergraduate `e20123456`, Master `M061211`, "
        "PhD `e2012345NKH`, International Program `p20123456`, "
        "Kep Campus `kpe20123456`, Tbong Khmum Campus `tk20123456`."
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

            response = api_get(f"/students/{cleaned_id}")

            if response is None:
                st.error("Could not connect to FastAPI backend.")

            elif response.status_code == 200:
                data = response.json()

                st.success("ITC student record found.")

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("### 👤 ITC Student Profile")

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
                    st.markdown("### 🏷️ Recommendation Tags")
                    render_tags(data.get("final_recommendation_tags"))

                st.markdown("### 📄 Recommendation Report")

                report = data.get("llm_recommendation_report")

                if report:
                    st.markdown(report)
                else:
                    st.info("No recommendation report found.")

            elif response.status_code == 404:
                st.error(
                    f"ITC student ID '{cleaned_id}' was not found in the recommendation database."
                )

            else:
                try:
                    st.error(response.json().get("detail", "Unable to retrieve student record."))
                except Exception:
                    st.error("Unable to retrieve student record.")


# -----------------------------
# New Student Input
# -----------------------------
elif page == "📝 New Student Input":
    st.markdown(
        '<div class="section-title">📝 New Student / Respondent Input</div>',
        unsafe_allow_html=True
    )

    st.write(
        "This page collects the same 33 survey features used by the saved K-Modes model. "
        "The submitted responses are sent to FastAPI, assigned to the closest learner segment, "
        "and saved with a generated recommendation report."
    )

    st.info(
        "ID rule: ITC students can use their official ITC ID. "
        "Non-ITC or external respondents can leave the ID blank and the system will generate an internal external ID."
    )

    feature_labels = {
        "use_lecture_slides": "Use lecture slides",
        "use_video_lectures": "Use video lectures",
        "use_quizzes": "Use quizzes",
        "use_articles": "Use articles",
        "use_forums": "Use forums",
        "use_simulations": "Use simulations",
        "online_discussion_participation": "Online discussion participation",
        "peer_collaboration": "Peer collaboration",
        "comfort_asking_questions": "Comfort asking questions",
        "sense_of_community": "Sense of community",
        "integration_quality": "Integration quality",
        "overall_understanding": "Overall understanding",
        "lect_clear_instructions": "Lecturer gives clear instructions",
        "lect_responsive": "Lecturer is responsive",
        "lect_diverse_tools": "Lecturer uses diverse tools",
        "lect_timely_feedback": "Lecturer gives timely feedback",
        "lect_foster_interaction": "Lecturer fosters interaction",
        "self_prioritize_deadlines": "Prioritize deadlines",
        "self_study_schedule": "Maintain study schedule",
        "self_prepare_class": "Prepare before class",
        "self_responsibility": "Learning responsibility",
        "career_preparation": "Career preparation",
        "video_helpfulness": "Video helpfulness",
        "digital_literacy_improvement": "Digital literacy improvement",
        "tech_issues_freq": "Technical issues frequency",
        "lms_usability": "LMS usability",
        "overall_satisfaction": "Overall satisfaction",
        "benefit_flexibility": "Benefit from flexibility",
        "benefit_variety": "Benefit from variety",
        "benefit_recorded_access": "Benefit from recorded access",
        "benefit_self_study_time": "Benefit from self-study time",
        "benefit_life_balance": "Benefit from life balance",
        "benefit_self_directed": "Benefit from self-directed learning",
    }

    with st.form("new_student_form"):
        respondent_type = st.radio(
            "Respondent Type",
            ["ITC Student", "Non-ITC / External Respondent", "Demo/Test User"],
            horizontal=True
        )

        if respondent_type == "ITC Student":
            student_id = st.text_input(
                "ITC Student ID",
                placeholder="Example: e20210320"
            )

        elif respondent_type == "Non-ITC / External Respondent":
            student_id = st.text_input(
                "External Respondent ID",
                placeholder="Optional. Leave blank to auto-generate an internal ID."
            )

        else:
            student_id = st.text_input(
                "Demo/Test ID",
                placeholder="Example: TEST001 or demo_001"
            )

        st.markdown("### 🧾 33 K-Modes Clustering Features")
        st.caption("Scale: 1 = Very Low / Strongly Disagree, 5 = Very High / Strongly Agree")

        responses = {}

        tabs = st.tabs([
            "📚 Content Use",
            "🤝 Interaction",
            "👩‍🏫 Lecturer Support",
            "🧠 Self-Regulation",
            "🌟 Benefits"
        ])

        feature_keys = list(feature_labels.keys())

        with tabs[0]:
            st.markdown("#### 📚 Content and Digital Learning Resources")
            for feature in feature_keys[0:6]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        with tabs[1]:
            st.markdown("#### 🤝 Interaction and Learning Experience")
            for feature in feature_keys[6:12]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        with tabs[2]:
            st.markdown("#### 👩‍🏫 Lecturer Support")
            for feature in feature_keys[12:17]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        with tabs[3]:
            st.markdown("#### 🧠 Self-Regulation and Learning Readiness")
            for feature in feature_keys[17:27]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        with tabs[4]:
            st.markdown("#### 🌟 Perceived Benefits of Blended Learning")
            for feature in feature_keys[27:33]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        st.markdown("### 💬 Open-ended Responses")

        strengths = st.text_area(
            "Strengths / positive aspects",
            height=120,
            placeholder="Example: I like flexible learning and recorded lectures."
        )

        challenges = st.text_area(
            "Challenges / suggestions",
            height=120,
            placeholder="Example: I need more interaction or clearer instructions."
        )

        submitted = st.form_submit_button("Generate Recommendation", type="primary")

    if submitted:
        raw_student_id = student_id.strip()

        if respondent_type == "ITC Student" and not raw_student_id:
            st.warning("Please enter the ITC student ID.")
        elif respondent_type == "Demo/Test User" and not raw_student_id:
            st.warning("Please enter a demo/test ID.")
        else:
            if respondent_type == "Non-ITC / External Respondent" and not raw_student_id:
                final_student_id = f"ext_{uuid.uuid4().hex[:10]}"
            else:
                final_student_id = raw_student_id

            payload = {
                "student_id": final_student_id,
                "responses": responses,
                "strengths_positive_aspects": strengths,
                "challenges_suggestions": challenges
            }

            response = api_post("/recommendations/generate", payload)

            if response is None:
                st.error("Could not connect to FastAPI backend.")

            elif response.status_code == 200:
                data = response.json()

                st.success("Recommendation generated and saved successfully.")

                if respondent_type == "Non-ITC / External Respondent":
                    st.info(
                        f"Generated internal external respondent ID: `{final_student_id}`. "
                        "This ID is stored for database tracking and future model tuning, "
                        "but the public lookup page is limited to ITC student IDs."
                    )

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("### 🧩 Assigned Learner Segment")
                    st.markdown(
                        f"""
                        <div class="info-card">
                            <b>ID:</b> {html.escape(str(data.get("student_id", final_student_id)))}<br><br>
                            <b>Segment:</b> {html.escape(str(data.get("student_segment_label", "-")))}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown("### 🏷️ Recommendation Tags")
                    render_tags(data.get("final_recommendation_tags"))

                st.markdown("### 📄 Generated Recommendation Report")

                generated_report = data.get("llm_recommendation_report", "")

                if generated_report:
                    st.markdown(generated_report)
                else:
                    st.info("No recommendation report generated.")

            else:
                try:
                    st.error(response.json().get("detail", "Unable to generate recommendation."))
                except Exception:
                    st.error("Unable to generate recommendation.")


# -----------------------------
# About Prototype
# -----------------------------
elif page == "ℹ️ About Prototype":
    st.markdown(
        '<div class="section-title">ℹ️ About the Prototype</div>',
        unsafe_allow_html=True
    )

    st.write(
        "This page summarizes the purpose, architecture, and current capability "
        "of the blended learning recommendation prototype."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏗️ System Architecture")
        st.markdown(
            """
This prototype follows a three-layer architecture:

- **Streamlit**: user interface and dashboard
- **FastAPI**: backend API service
- **PostgreSQL**: persistent database storage
- **K-Modes model**: learner segment assignment
- **Recommendation logic**: tag and report generation
"""
        )

    with col2:
        st.markdown("### ✅ Prototype Capabilities")
        st.markdown(
            """
The current prototype supports:

- Dashboard summary of all stored recommendation records
- Student Records page showing the original cleaned records and new records
- Survey Analytics page summarizing preprocessing and segment interpretation
- ITC student lookup using official ITC student ID
- New input using the same 33 survey features
- Support for ITC students and non-ITC/external respondents
- Internal external ID generation for non-ITC respondents
- K-Modes-based cluster assignment
- Saving recommendation outputs to PostgreSQL
- Saving raw 33-feature inputs for future model tuning
"""
        )

    st.markdown("---")

    st.markdown("### 🎓 Thesis Positioning")
    st.markdown(
        """
The prototype demonstrates a **segment-based personalized recommendation system** for blended learning.  
A saved **K-Modes clustering model** assigns new submissions to the closest learned learner segment based on the same **33 survey features** used during model training.

The original data collection contained **445 raw survey responses**. After the automated preprocessing pipeline, **420 valid responses** remained and were used for clustering and recommendation model development.

Because the original data collection included both ITC students and non-ITC/external respondents, the prototype uses a unified internal `student_id` field. Official ITC IDs are preserved for student lookup, while non-ITC respondents may receive generated external IDs such as `ext_8f3a91c204` for backend storage and future analysis.

The public lookup function is limited to ITC students because they have official IDs that are known and stable. External respondent IDs are treated as internal database identifiers rather than user-facing lookup credentials.

The system does **not automatically retrain** the clustering model during prediction. Instead, new inputs are stored in PostgreSQL and can be combined with the original survey dataset later for future model refinement or retraining.
"""
    )

    st.markdown("### 🔄 Data Flow")
    st.markdown(
        """
**Original Dataset Preparation**  
→ 445 raw responses  
→ Automated preprocessing pipeline  
→ 420 valid cleaned responses  
→ 33 clustering features  
→ K-Modes learner segmentation

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
        The current version supports both ITC students and non-ITC/external respondents, while the lookup function is limited to official ITC student IDs.
    </div>
    """,
    unsafe_allow_html=True
)