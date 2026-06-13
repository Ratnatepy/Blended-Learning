from pathlib import Path
import numpy as np
import pandas as pd


# =========================================================
# PATH SETTINGS
# =========================================================

DATA_PATH = Path("data/processed/cleaned_data.csv")

OUTPUT_DIR = Path("data/processed/reliability")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# CRONBACH'S ALPHA FUNCTION
# =========================================================

def cronbach_alpha(data: pd.DataFrame):
    """
    Compute Cronbach's alpha for Likert-scale items.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing only the items used in one scale or construct.

    Returns
    -------
    alpha : float
        Cronbach's alpha value.
    n_valid : int
        Number of complete valid responses used.
    k_items : int
        Number of items used.
    """

    data = data.apply(pd.to_numeric, errors="coerce")
    data = data.dropna(axis=0, how="any")

    n_valid = len(data)
    k_items = data.shape[1]

    if k_items < 2 or n_valid == 0:
        return np.nan, n_valid, k_items

    item_variances = data.var(axis=0, ddof=1)
    total_score = data.sum(axis=1)
    total_variance = total_score.var(ddof=1)

    if total_variance == 0:
        return np.nan, n_valid, k_items

    alpha = (k_items / (k_items - 1)) * (
        1 - item_variances.sum() / total_variance
    )

    return alpha, n_valid, k_items


# =========================================================
# INTERPRETATION FUNCTION
# =========================================================

def interpret_alpha(alpha: float) -> str:
    """
    Interpret Cronbach's alpha using common academic thresholds.
    """

    if pd.isna(alpha):
        return "Not available"
    elif alpha >= 0.90:
        return "Excellent"
    elif alpha >= 0.80:
        return "Good"
    elif alpha >= 0.70:
        return "Acceptable"
    elif alpha >= 0.60:
        return "Questionable / moderate"
    else:
        return "Low / questionable"


# =========================================================
# ALPHA IF ITEM DELETED
# =========================================================

def alpha_if_item_deleted(data: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Cronbach's alpha after deleting each item one by one.
    This helps identify whether one item reduces the reliability of a construct.
    """

    results = []

    for item in data.columns:
        remaining_items = [col for col in data.columns if col != item]

        alpha, n_valid, k_items = cronbach_alpha(data[remaining_items])

        results.append(
            {
                "Deleted Item": item,
                "Remaining Items": k_items,
                "Valid Responses": n_valid,
                "Alpha if Item Deleted": round(alpha, 3)
                if not pd.isna(alpha)
                else np.nan,
            }
        )

    return pd.DataFrame(results)


# =========================================================
# MAIN SCRIPT
# =========================================================

def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}\n"
            "Please check that the cleaned dataset exists in data/processed/cleaned_data.csv"
        )

    df = pd.read_csv(DATA_PATH)

    # =====================================================
    # CONSTRUCT-LEVEL LIKERT ITEMS
    # =====================================================

    constructs = {
        "Lecturer Support": [
            "lect_clear_instructions",
            "lect_responsive",
            "lect_diverse_tools",
            "lect_timely_feedback",
            "lect_foster_interaction",
        ],
        "Perceived Benefits": [
            "benefit_flexibility",
            "benefit_variety",
            "benefit_recorded_access",
            "benefit_self_study_time",
            "benefit_life_balance",
            "benefit_self_directed",
        ],
        "Learning Material Use": [
            "use_lecture_slides",
            "use_video_lectures",
            "use_quizzes",
            "use_articles",
            "use_forums",
            "use_simulations",
        ],
        "Self-Regulation": [
            "self_prioritize_deadlines",
            "self_study_schedule",
            "self_prepare_class",
            "self_responsibility",
        ],
        "Engagement and Interaction": [
            "online_discussion_participation",
            "peer_collaboration",
            "comfort_asking_questions",
            "sense_of_community",
        ],
    }

    # =====================================================
    # ALL 33 ORDINAL LIKERT ITEMS
    # =====================================================
    # Important:
    # tech_issues_freq is reverse-coded because its original meaning is negative:
    # higher value = more technical issues.
    # After reversing:
    # higher value = fewer technical issues / better technical experience.

    all_33_likert_items = [
        "video_helpfulness",
        "digital_literacy_improvement",
        "use_lecture_slides",
        "use_video_lectures",
        "use_quizzes",
        "use_articles",
        "use_forums",
        "use_simulations",
        "online_discussion_participation",
        "peer_collaboration",
        "comfort_asking_questions",
        "sense_of_community",
        "integration_quality",
        "benefit_flexibility",
        "benefit_variety",
        "benefit_recorded_access",
        "benefit_self_study_time",
        "benefit_life_balance",
        "benefit_self_directed",
        "overall_understanding",
        "lect_clear_instructions",
        "lect_responsive",
        "lect_diverse_tools",
        "lect_timely_feedback",
        "lect_foster_interaction",
        "self_prioritize_deadlines",
        "self_study_schedule",
        "self_prepare_class",
        "self_responsibility",
        "overall_satisfaction",
        "career_preparation",
        "tech_issues_freq",
        "lms_usability",
    ]

    # =====================================================
    # CHECK REQUIRED COLUMNS
    # =====================================================

    required_columns = set(all_33_likert_items)

    for items in constructs.values():
        required_columns.update(items)

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(
            "The following required columns are missing from the cleaned dataset:\n"
            + "\n".join(missing_columns)
        )

    # =====================================================
    # REVERSE-CODE TECHNICAL ISSUE FREQUENCY
    # =====================================================

    df_alpha = df.copy()

    df_alpha["tech_issues_freq"] = pd.to_numeric(
        df_alpha["tech_issues_freq"], errors="coerce"
    )

    df_alpha["tech_issues_freq_reversed"] = 6 - df_alpha["tech_issues_freq"]

    all_33_likert_items_for_alpha = [
        "tech_issues_freq_reversed" if col == "tech_issues_freq" else col
        for col in all_33_likert_items
    ]

    # =====================================================
    # COMPUTE OVERALL 33-ITEM RELIABILITY
    # =====================================================

    results = []

    overall_alpha, overall_n, overall_k = cronbach_alpha(
        df_alpha[all_33_likert_items_for_alpha]
    )

    results.append(
        {
            "Construct": "Overall Likert-Scale Item Pool",
            "Number of Items": overall_k,
            "Valid Responses": overall_n,
            "Cronbach Alpha": round(overall_alpha, 3)
            if not pd.isna(overall_alpha)
            else np.nan,
            "Interpretation": interpret_alpha(overall_alpha),
        }
    )

    # Save alpha-if-item-deleted for all 33 items
    overall_deleted = alpha_if_item_deleted(
        df_alpha[all_33_likert_items_for_alpha]
    )

    overall_deleted.to_csv(
        OUTPUT_DIR / "alpha_if_item_deleted_overall_33_items.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # =====================================================
    # COMPUTE CONSTRUCT-LEVEL RELIABILITY
    # =====================================================

    for construct_name, items in constructs.items():
        construct_data = df[items]

        alpha, n_valid, k_items = cronbach_alpha(construct_data)

        results.append(
            {
                "Construct": construct_name,
                "Number of Items": k_items,
                "Valid Responses": n_valid,
                "Cronbach Alpha": round(alpha, 3)
                if not pd.isna(alpha)
                else np.nan,
                "Interpretation": interpret_alpha(alpha),
            }
        )

        deleted_result = alpha_if_item_deleted(construct_data)

        safe_name = (
            construct_name.lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("-", "_")
        )

        deleted_result.to_csv(
            OUTPUT_DIR / f"alpha_if_item_deleted_{safe_name}.csv",
            index=False,
            encoding="utf-8-sig",
        )

    # =====================================================
    # SAVE MAIN RESULT TABLE
    # =====================================================

    results_df = pd.DataFrame(results)

    results_csv_path = OUTPUT_DIR / "cronbach_alpha_results.csv"
    results_tex_path = OUTPUT_DIR / "cronbach_alpha_table.tex"

    results_df.to_csv(
        results_csv_path,
        index=False,
        encoding="utf-8-sig",
    )

    latex_table = results_df.to_latex(
        index=False,
        escape=False,
        caption="Cronbach's Alpha Reliability Results for Likert-Scale Constructs",
        label="tab:cronbach-alpha",
        column_format="lcccl",
    )

    with open(results_tex_path, "w", encoding="utf-8") as f:
        f.write(latex_table)

    # =====================================================
    # PRINT RESULTS
    # =====================================================

    print("\nCronbach's Alpha Reliability Results")
    print("=" * 80)
    print(results_df.to_string(index=False))

    print("\nSaved output files:")
    print(f"- {results_csv_path}")
    print(f"- {results_tex_path}")
    print(f"- {OUTPUT_DIR / 'alpha_if_item_deleted_overall_33_items.csv'}")
    print("- Alpha-if-item-deleted CSV files for each construct")

    print("\nNote:")
    print(
        "For the overall 33-item alpha, tech_issues_freq was reverse-coded "
        "as tech_issues_freq_reversed before calculation."
    )


if __name__ == "__main__":
    main()