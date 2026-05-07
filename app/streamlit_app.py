import os
import json
import html
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

        .report-container {
            background: rgba(15, 23, 42, 0.55);
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 18px;
            padding: 1.2rem 1.35rem;
            margin-bottom: 1rem;
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


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## Navigation")

page = st.sidebar.radio(
    "",
    ["Dashboard", "Student Lookup", "New Student Input", "About Prototype"]
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
st.sidebar.caption("Blended Learning Thesis Prototype")
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
            <span class="hero-badge">Streamlit UI</span>
            <span class="hero-badge">FastAPI Backend</span>
            <span class="hero-badge">PostgreSQL Database</span>
            <span class="hero-badge">Segment-based Recommendation</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Dashboard
# -----------------------------
if page == "Dashboard":
    st.markdown(
        '<div class="section-title">Dashboard Summary</div>',
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
                "Total Students",
                total_students,
                "Records stored in PostgreSQL"
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
                "LLM-assisted report generation"
            )

        st.markdown("### Student Segment Distribution")

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
                    yaxis_title="Number of Students",
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
                        "Students: %{value}<br>"
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
# Student Lookup
# -----------------------------
elif page == "Student Lookup":
    st.markdown(
        '<div class="section-title">Student Lookup</div>',
        unsafe_allow_html=True
    )

    st.write("Enter a student ID to retrieve the learner profile and recommendation report.")

    student_id = st.text_input("Student ID", placeholder="Example: e20210528")

    if st.button("Get Student Recommendation", type="primary", use_container_width=False):
        if not student_id.strip():
            st.warning("Please enter a student ID.")
        else:
            response = api_get(f"/students/{student_id.strip()}")

            if response is None:
                st.error("Could not connect to FastAPI backend.")

            elif response.status_code == 200:
                data = response.json()

                st.success("Student record found.")

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("### Student Profile")

                    st.markdown(
                        f"""
                        <div class="info-card">
                            <b>Student ID:</b> {html.escape(str(data.get("student_id", "-")))}<br><br>
                            <b>Student Segment:</b> {html.escape(str(data.get("student_segment_label", "-")))}
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
                    st.markdown(report)
                else:
                    st.info("No recommendation report found.")

            else:
                try:
                    st.error(response.json().get("detail", "Student not found."))
                except Exception:
                    st.error("Student not found.")


# -----------------------------
# New Student Input
# -----------------------------
elif page == "New Student Input":
    st.markdown(
        '<div class="section-title">New Student Input</div>',
        unsafe_allow_html=True
    )

    st.write(
        "This page collects the same 33 survey features used by the saved K-Modes model. "
        "The submitted responses are sent to FastAPI, assigned to the closest learner segment, "
        "and saved with a generated recommendation report."
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
        student_id = st.text_input("Student ID", placeholder="Example: NEW001")

        st.markdown("### 33 K-Modes Clustering Features")
        st.caption("Scale: 1 = Very Low / Strongly Disagree, 5 = Very High / Strongly Agree")

        responses = {}

        tabs = st.tabs([
            "Content Use",
            "Interaction",
            "Lecturer Support",
            "Self-Regulation",
            "Benefits"
        ])

        feature_keys = list(feature_labels.keys())

        with tabs[0]:
            st.markdown("#### Content and Digital Learning Resources")
            for feature in feature_keys[0:6]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        with tabs[1]:
            st.markdown("#### Interaction and Learning Experience")
            for feature in feature_keys[6:12]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        with tabs[2]:
            st.markdown("#### Lecturer Support")
            for feature in feature_keys[12:17]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        with tabs[3]:
            st.markdown("#### Self-Regulation and Learning Readiness")
            for feature in feature_keys[17:27]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        with tabs[4]:
            st.markdown("#### Perceived Benefits of Blended Learning")
            for feature in feature_keys[27:33]:
                responses[feature] = st.slider(
                    feature_labels[feature],
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"slider_{feature}"
                )

        st.markdown("### Open-ended Responses")

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
        if not student_id.strip():
            st.warning("Please enter a student ID.")
        else:
            payload = {
                "student_id": student_id.strip(),
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

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("### Assigned Student Segment")
                    st.markdown(
                        f"""
                        <div class="info-card">
                            <b>{html.escape(str(data.get("student_segment_label", "-")))}</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown("### Recommendation Tags")
                    render_tags(data.get("final_recommendation_tags"))

                st.markdown("### Generated Recommendation Report")

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
# Footer
# -----------------------------
st.markdown(
    """
    <div class="footer-box">
        <b>Prototype Note:</b> This system provides segment-based personalized recommendations for blended learning.
        The current version is intended for thesis demonstration and can later be extended with trained clustering
        models, richer student features, and a more advanced LLM recommendation layer.
    </div>
    """,
    unsafe_allow_html=True
)