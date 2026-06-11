import os
import json
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd
from openai import OpenAI

from ml.src.blended_learning.config.settings import settings


class OpenRouterStudentRecommender:
    """
    OpenRouter LLM recommender for the blended learning thesis prototype.

    The rule-based recommendations are the source of truth.
    The LLM only rewrites them into readable student-facing feedback.

    Features:
    - Generate one student report
    - Generate reports from CSV
    - Resume after pause/interruption
    - Save progress after each student
    - Backup previous output CSV
    - Rollback if saving fails
    - Rule-based fallback if OpenRouter fails
    """

    def __init__(
        self,
        api_key=None,
        model="openai/gpt-oss-120b:free",
        base_url="https://openrouter.ai/api/v1",
        prompt_path=None,
        app_title="Blended Learning Prototype"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", model)
        self.base_url = os.getenv("OPENROUTER_BASE_URL", base_url)
        self.app_title = os.getenv("OPENROUTER_APP_TITLE", app_title)
        self.last_generation_source = None
        self.last_generation_error = None
        self.last_error = None

        if prompt_path is None:
            self.prompt_path = (
                Path(settings.path["prompts_path"])
                / "student_recommendation_prompt.txt"
            )
        else:
            self.prompt_path = Path(prompt_path)

        self.client = (
            OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            if self.api_key
            else None
        )

        self.system_prompt = self.load_prompt(self.prompt_path)

    # ---------------------------------------------------------
    # Prompt
    # ---------------------------------------------------------

    def load_prompt(self, prompt_path):
        """
        Load the system prompt from a text file.
        """
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read()

    # ---------------------------------------------------------
    # JSON parsing
    # ---------------------------------------------------------

    def parse_json_field(self, value, default=None):
        """
        Parse JSON string columns from the CSV.
        """
        if default is None:
            default = []

        if pd.isna(value):
            return default

        if isinstance(value, list) or isinstance(value, dict):
            return value

        try:
            return json.loads(value)
        except Exception:
            return default

    # ---------------------------------------------------------
    # Data loading
    # ---------------------------------------------------------

    def load_recommendation_data(self, csv_path):
        """
        Load student recommendation feature CSV and parse JSON columns.
        """
        df = pd.read_csv(csv_path)

        json_columns = [
            "strength_themes",
            "challenge_themes",
            "strength_tags",
            "challenge_tags",
            "recommendation_tags",
            "segment_default_tags",
            "final_recommendation_tags",
            "rule_based_recommendations"
        ]

        for col in json_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.parse_json_field)

        return df

    # ---------------------------------------------------------
    # Student package
    # ---------------------------------------------------------

    def build_student_package(self, row):
        """
        Build one structured evidence package for the LLM.

        Works with:
        - pandas Series
        - dictionary
        """
        return {
            "student_id": row.get("student_id", None),
            "student_segment": row.get("student_segment", None),
            "student_segment_label": row.get("student_segment_label", None),
            "cluster_label": row.get("cluster_label", None),

            "open_strengths_clean": row.get("open_strengths_clean", ""),
            "open_challenges_clean": row.get("open_challenges_clean", ""),

            "strength_sentiment_label": row.get(
                "strength_sentiment_label",
                None
            ),
            "challenge_sentiment_label": row.get(
                "challenge_sentiment_label",
                None
            ),
            "strength_compound": row.get("strength_compound", None),
            "challenge_compound": row.get("challenge_compound", None),

            "strength_themes": row.get("strength_themes", []),
            "challenge_themes": row.get("challenge_themes", []),

            "recommendation_tags": row.get("recommendation_tags", []),
            "segment_default_tags": row.get("segment_default_tags", []),
            "final_recommendation_tags": row.get(
                "final_recommendation_tags",
                []
            ),

            "rule_based_recommendations": row.get(
                "rule_based_recommendations",
                []
            )
        }

    # ---------------------------------------------------------
    # Rule-based fallback
    # ---------------------------------------------------------

    def build_rule_based_report(self, student_package):
        """
        Fallback report if API key is missing or LLM generation fails.
        """
        segment = student_package.get(
            "student_segment_label",
            "Unknown segment"
        )

        strengths = student_package.get("strength_themes", [])
        challenges = student_package.get("challenge_themes", [])
        recommendations = student_package.get(
            "rule_based_recommendations",
            []
        )

        report = []

        report.append("# Personalized Blended Learning Recommendation Report")
        report.append("")

        report.append("## 1. Student Learning Profile")
        report.append(f"The student belongs to the **{segment}** profile.")
        report.append("")

        report.append("## 2. Main Strengths")
        if strengths:
            for theme in strengths:
                report.append(f"- {theme}")
        else:
            report.append(
                "- No clear strength theme was detected from the "
                "open-ended response."
            )
        report.append("")

        report.append("## 3. Main Challenges")
        if challenges:
            for theme in challenges:
                report.append(f"- {theme}")
        else:
            report.append(
                "- No clear challenge theme was detected from the "
                "open-ended response."
            )
        report.append("")

        report.append("## 4. Personalized Recommendations")
        if recommendations:
            for rec in recommendations:
                title = rec.get("title", "Recommendation")
                text = rec.get("recommendation", "")
                report.append(f"- **{title}:** {text}")
        else:
            report.append(
                "- Use the student's segment profile to provide general "
                "blended learning support."
            )
        report.append("")

        report.append("## 5. Short Action Plan")
        report.append("- Review learning materials regularly.")
        report.append("- Follow a weekly study schedule.")
        report.append("- Ask questions during in-person or online sessions.")
        report.append(
            "- Use available digital resources and recorded lessons "
            "for revision."
        )

        return "\n".join(report)

    # ---------------------------------------------------------
    # Prompt building
    # ---------------------------------------------------------

    def build_user_prompt(self, student_package):
        """
        Build the user prompt dynamically from student evidence.
        """
        return f"""
Create a personalized blended learning recommendation report for this student.

Student evidence:
{json.dumps(student_package, ensure_ascii=False, indent=2)}

Rules:
- Use only the provided evidence.
- Do not invent facts.
- Keep it concise.
- Mention the student segment.
- The rule-based recommendations are the source of truth.
- If open-ended evidence is weak or empty, explain that the recommendation is based mainly on the segment profile.
"""

    # ---------------------------------------------------------
    # LLM generation
    # ---------------------------------------------------------

    def generate_report(
        self,
        student_package,
        temperature=0.3,
        max_tokens=900
    ):
        """
        Generate one recommendation report.

        With OPENROUTER_API_KEY configured, this calls OpenRouter.
        If the key is missing or the request fails, it returns the
        rule-based fallback so the prototype remains usable.
        FastAPI can inspect last_generation_source and
        last_generation_error after this method returns.
        """
        self.last_generation_source = None
        self.last_generation_error = None
        self.last_error = None

        if not self.client:
            self.last_generation_source = "rule_based_fallback_no_api_key"
            self.last_generation_error = "OPENROUTER_API_KEY is not configured."
            self.last_error = self.last_generation_error
            return self.build_rule_based_report(student_package)

        user_prompt = self.build_user_prompt(student_package)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers={
                    "HTTP-Referer": os.getenv(
                        "OPENROUTER_HTTP_REFERER",
                        "http://localhost"
                    ),
                    "X-Title": self.app_title
                }
            )

            self.last_generation_source = "openrouter_llm"
            self.last_generation_error = None
            self.last_error = None
            return response.choices[0].message.content

        except Exception as error:
            self.last_generation_source = "rule_based_fallback_openrouter_error"
            self.last_generation_error = str(error)
            self.last_error = self.last_generation_error
            print("OpenRouter generation failed:", error)
            print("Returning rule-based fallback report.")
            return self.build_rule_based_report(student_package)

    # ---------------------------------------------------------
    # Output row
    # ---------------------------------------------------------

    def build_output_row(self, row, student_package, report):
        """
        Build one output row for the recommendation result CSV.
        """
        return {
            "student_id": row.get("student_id", None),
            "student_segment_label": row.get(
                "student_segment_label",
                None
            ),
            "final_recommendation_tags": json.dumps(
                student_package.get("final_recommendation_tags", []),
                ensure_ascii=False
            ),
            "llm_recommendation_report": report
        }

    # ---------------------------------------------------------
    # Backup and rollback
    # ---------------------------------------------------------

    def backup_file(self, file_path):
        """
        Create a timestamped backup of an existing file.

        Returns backup path if file exists.
        Returns None if file does not exist.
        """
        if not os.path.exists(file_path):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"

        shutil.copy2(file_path, backup_path)

        return backup_path

    def rollback_file(self, backup_path, output_csv):
        """
        Restore output CSV from backup.
        """
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, output_csv)
            print(f"Rollback completed. Restored from: {backup_path}")
        else:
            print("No backup file found. Rollback skipped.")

    def save_output_safely(self, output_df, output_csv):
        """
        Save DataFrame safely using a temporary file first.
        """
        output_dir = os.path.dirname(output_csv)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        temp_output_csv = output_csv + ".tmp"

        output_df.to_csv(
            temp_output_csv,
            index=False,
            encoding="utf-8-sig"
        )

        os.replace(temp_output_csv, output_csv)

    # ---------------------------------------------------------
    # Append progress
    # ---------------------------------------------------------

    def append_output_row_safely(self, output_row, output_csv):
        """
        Append one student result to output CSV immediately.

        This is useful for pause/interruption recovery.
        """
        output_dir = os.path.dirname(output_csv)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        row_df = pd.DataFrame([output_row])

        file_exists = os.path.exists(output_csv)

        row_df.to_csv(
            output_csv,
            mode="a",
            header=not file_exists,
            index=False,
            encoding="utf-8-sig"
        )

    # ---------------------------------------------------------
    # Direct one-student generation without CSV
    # ---------------------------------------------------------

    def generate_report_from_package(
        self,
        student_data,
        temperature=0.3,
        max_tokens=900
    ):
        """
        Generate one report from a dictionary or pandas Series.

        This does not require a CSV.
        """
        student_package = self.build_student_package(student_data)

        report = self.generate_report(
            student_package=student_package,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return report

    # ---------------------------------------------------------
    # One student by ID from CSV
    # ---------------------------------------------------------

    def generate_report_for_student_id(
        self,
        input_csv,
        student_id,
        output_csv=None,
        temperature=0.3,
        max_tokens=900
    ):
        """
        Generate a recommendation report for one student by student_id.

        If output_csv is provided, the result is saved safely.
        """
        df = self.load_recommendation_data(input_csv)

        if "student_id" not in df.columns:
            raise ValueError("The input CSV does not contain 'student_id'.")

        student_rows = df[df["student_id"].astype(str) == str(student_id)]

        if student_rows.empty:
            raise ValueError(f"No student found with student_id: {student_id}")

        row = student_rows.iloc[0]
        student_package = self.build_student_package(row)

        report = self.generate_report(
            student_package=student_package,
            temperature=temperature,
            max_tokens=max_tokens
        )

        output_row = self.build_output_row(
            row=row,
            student_package=student_package,
            report=report
        )

        output_df = pd.DataFrame([output_row])

        if output_csv:
            backup_path = self.backup_file(output_csv)

            try:
                self.save_output_safely(output_df, output_csv)
            except Exception as error:
                print("Saving single-student report failed:", error)
                self.rollback_file(backup_path, output_csv)
                raise error

        return output_df

    # ---------------------------------------------------------
    # Batch generation from CSV
    # ---------------------------------------------------------

    def generate_reports_from_csv(
        self,
        input_csv,
        output_csv,
        resume_csv=None,
        limit=None,
        temperature=0.3,
        max_tokens=900,
        resume=True,
        save_each_student=True
    ):
        """
        Generate recommendation reports using three files:

        1. input_csv:
            Current recommendation feature dataset.
            Example: 567 rows.

        2. resume_csv:
            Previous generated report CSV.
            Used only for resuming/skipping already generated students.
            This file is NOT appended to directly.

        3. output_csv:
            New clean output CSV for the current run.
            Final row count should match current input students.
        """

        def make_student_key(series):
            return series.astype(str).str.strip()

        output_csv = str(output_csv)

        # Backup existing output file, then start clean
        backup_path = self.backup_file(output_csv)

        try:
            # =====================================================
            # 1. Load current input dataset
            # =====================================================

            df = self.load_recommendation_data(input_csv)

            if "student_id" not in df.columns:
                raise ValueError("The input CSV does not contain 'student_id'.")

            if limit is not None:
                df_to_process = df.head(limit).copy()
            else:
                df_to_process = df.copy()

            df_to_process["_student_id_key"] = make_student_key(
                df_to_process["student_id"]
            )

            current_student_ids = set(df_to_process["_student_id_key"])

            print(f"Input dataset shape: {df_to_process.shape}")


            # =====================================================
            # 2. Load previous resume file, if provided
            # =====================================================

            reusable_previous_reports = pd.DataFrame()
            processed_student_ids = set()

            if resume and resume_csv is not None and os.path.exists(resume_csv):

                previous_df = pd.read_csv(resume_csv)

                if "student_id" not in previous_df.columns:
                    raise ValueError(
                        "The resume CSV does not contain 'student_id'."
                    )

                previous_df["_student_id_key"] = make_student_key(
                    previous_df["student_id"]
                )

                # Keep only reports that still exist in current input
                previous_df = previous_df[
                    previous_df["_student_id_key"].isin(current_student_ids)
                ].copy()

                # If previous file has duplicate reports, keep the latest one
                previous_df = previous_df.drop_duplicates(
                    subset="_student_id_key",
                    keep="last"
                )

                reusable_previous_reports = previous_df.copy()
                processed_student_ids = set(
                    reusable_previous_reports["_student_id_key"]
                )

                print(f"Resume file loaded: {resume_csv}")
                print(f"Reusable previous reports: {len(reusable_previous_reports)}")

            else:
                print("No resume file used. Starting fresh.")


            # =====================================================
            # 3. Create clean output file
            # =====================================================

            output_cols = [
                "student_id",
                "student_segment_label",
                "final_recommendation_tags",
                "llm_recommendation_report"
            ]

            # Start output with reusable previous reports only
            if not reusable_previous_reports.empty:
                reusable_to_save = reusable_previous_reports[
                    [c for c in output_cols if c in reusable_previous_reports.columns]
                ].copy()

                self.save_output_safely(reusable_to_save, output_csv)

            else:
                # Create empty output file with correct columns
                empty_output = pd.DataFrame(columns=output_cols)
                self.save_output_safely(empty_output, output_csv)


            # =====================================================
            # 4. Generate missing reports only
            # =====================================================

            results = []
            total_students = len(df_to_process)

            for count, (_, row) in enumerate(
                df_to_process.iterrows(),
                start=1
            ):
                student_id = row.get("student_id", None)
                student_key = str(student_id).strip()

                if resume and student_key in processed_student_ids:
                    print(
                        f"[{count}/{total_students}] "
                        f"Skipping already processed student: {student_id}"
                    )
                    continue

                print(
                    f"[{count}/{total_students}] "
                    f"Generating report for student: {student_id}"
                )

                student_package = self.build_student_package(row)

                report = self.generate_report(
                    student_package=student_package,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                output_row = self.build_output_row(
                    row=row,
                    student_package=student_package,
                    report=report
                )

                results.append(output_row)

                if save_each_student:
                    self.append_output_row_safely(
                        output_row=output_row,
                        output_csv=output_csv
                    )

                    processed_student_ids.add(student_key)

                    print(f"Saved progress for student: {student_id}")


            # =====================================================
            # 5. Final cleanup: remove duplicates and reorder
            # =====================================================

            final_output_df = pd.read_csv(output_csv)

            final_output_df["_student_id_key"] = make_student_key(
                final_output_df["student_id"]
            )

            # Keep only current input students
            final_output_df = final_output_df[
                final_output_df["_student_id_key"].isin(current_student_ids)
            ].copy()

            # Remove duplicates again, keeping latest
            final_output_df = final_output_df.drop_duplicates(
                subset="_student_id_key",
                keep="last"
            )

            # Reorder output to follow input order
            student_order = df_to_process["_student_id_key"].tolist()

            final_output_df["_order"] = pd.Categorical(
                final_output_df["_student_id_key"],
                categories=student_order,
                ordered=True
            )

            final_output_df = (
                final_output_df
                .sort_values("_order")
                .drop(columns=["_student_id_key", "_order"], errors="ignore")
            )

            self.save_output_safely(final_output_df, output_csv)

            print(f"\nGenerated reports saved to: {output_csv}")
            print(f"Final output shape: {final_output_df.shape}")

            return final_output_df


        except KeyboardInterrupt:
            print("Process interrupted by user.")
            print("Progress already saved in output CSV.")

            if os.path.exists(output_csv):
                return pd.read_csv(output_csv)

            return pd.DataFrame()


        except Exception as error:
            print("Batch report generation failed:", error)

            if backup_path:
                self.rollback_file(backup_path, output_csv)

            raise error

    def generate_reports_incremental(
        self,
        input_csv,
        store_csv,
        output_csv,
        limit=None,
        temperature=0.3,
        max_tokens=900,
        save_after_each_new_student=True
    ):
        """
        Incremental LLM report generation using 3 files.

        1. input_csv:
            Current collected recommendation feature dataset.
            Example: new 567, 588, or 615 students.

        2. store_csv:
            Master report store.
            Keeps all previously generated reports.
            If student_id already exists here, LLM will NOT be called again.

        3. output_csv:
            Clean output for the current input_csv only.
            Final rows follow the current input dataset.
        """

        import os
        from datetime import datetime

        input_csv = str(input_csv)
        store_csv = str(store_csv)
        output_csv = str(output_csv)

        def normalize_student_id(value):
            if pd.isna(value):
                return ""
            return str(value).strip()

        def clean_store_df(store_df):
            """
            Keep only valid student_id rows and one latest report per student.
            """
            if store_df.empty:
                return store_df

            store_df["_student_id_key"] = (
                store_df["student_id"]
                .apply(normalize_student_id)
            )

            store_df = store_df[store_df["_student_id_key"] != ""].copy()

            store_df = store_df.drop_duplicates(
                subset="_student_id_key",
                keep="last"
            )

            return store_df

        # ---------------------------------------------------------
        # 1. Load current input dataset
        # ---------------------------------------------------------

        df = self.load_recommendation_data(input_csv)

        if "student_id" not in df.columns:
            raise ValueError("input_csv must contain 'student_id' column.")

        if limit is not None:
            df_to_process = df.head(limit).copy()
        else:
            df_to_process = df.copy()

        df_to_process["_student_id_key"] = (
            df_to_process["student_id"]
            .apply(normalize_student_id)
        )

        df_to_process = df_to_process[
            df_to_process["_student_id_key"] != ""
        ].copy()

        print(f"Current input dataset shape: {df_to_process.shape}")


        # ---------------------------------------------------------
        # 2. Load master store file
        # ---------------------------------------------------------

        if os.path.exists(store_csv):
            store_df = pd.read_csv(store_csv)
            print(f"Loaded existing store file: {store_csv}")
            print(f"Store shape before cleaning: {store_df.shape}")
        else:
            store_df = pd.DataFrame(columns=[
                "student_id",
                "student_segment_label",
                "final_recommendation_tags",
                "llm_recommendation_report",
                "generation_source",
                "generation_error",
                "generated_at"
            ])
            print("No existing store file found. Creating new store.")

        if not store_df.empty and "student_id" not in store_df.columns:
            raise ValueError("store_csv must contain 'student_id' column.")

        store_df = clean_store_df(store_df)

        existing_student_ids = set(store_df["_student_id_key"]) if not store_df.empty else set()

        print(f"Store shape after cleaning: {store_df.shape}")
        print(f"Existing generated students in store: {len(existing_student_ids)}")


        # ---------------------------------------------------------
        # 3. Generate reports only for new students
        # ---------------------------------------------------------

        new_rows = []
        total_students = len(df_to_process)

        for count, (_, row) in enumerate(df_to_process.iterrows(), start=1):

            student_id = row.get("student_id", None)
            student_key = normalize_student_id(student_id)

            if student_key in existing_student_ids:
                print(
                    f"[{count}/{total_students}] "
                    f"Already exists in store, skip LLM: {student_id}"
                )
                continue

            print(
                f"[{count}/{total_students}] "
                f"New student detected, calling LLM: {student_id}"
            )

            student_package = self.build_student_package(row)

            report = self.generate_report(
                student_package=student_package,
                temperature=temperature,
                max_tokens=max_tokens
            )

            output_row = self.build_output_row(
                row=row,
                student_package=student_package,
                report=report
            )

            output_row["generation_source"] = self.last_generation_source
            output_row["generation_error"] = self.last_generation_error
            output_row["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output_row["_student_id_key"] = student_key

            new_rows.append(output_row)
            existing_student_ids.add(student_key)

            # Save store after each new student to prevent losing progress
            if save_after_each_new_student:
                store_df = pd.concat(
                    [store_df, pd.DataFrame([output_row])],
                    ignore_index=True
                )

                store_df = clean_store_df(store_df)

                store_to_save = store_df.drop(
                    columns=["_student_id_key"],
                    errors="ignore"
                )

                self.save_output_safely(store_to_save, store_csv)

                print(f"Saved new report to store for student: {student_id}")


        # ---------------------------------------------------------
        # 4. Save store once more after all new students
        # ---------------------------------------------------------

        if new_rows and not save_after_each_new_student:
            store_df = pd.concat(
                [store_df, pd.DataFrame(new_rows)],
                ignore_index=True
            )

        store_df = clean_store_df(store_df)

        store_to_save = store_df.drop(
            columns=["_student_id_key"],
            errors="ignore"
        )

        self.save_output_safely(store_to_save, store_csv)

        print(f"\nMaster store saved to: {store_csv}")
        print(f"Master store shape: {store_to_save.shape}")


        # ---------------------------------------------------------
        # 5. Create clean current output from store
        # ---------------------------------------------------------

        current_keys = df_to_process[["_student_id_key"]].copy()
        current_keys["_input_order"] = range(len(current_keys))

        final_output_df = current_keys.merge(
            store_df,
            on="_student_id_key",
            how="left"
        )

        missing_after_generation = final_output_df[
            final_output_df["llm_recommendation_report"].isna()
        ]

        if len(missing_after_generation) > 0:
            print("\nWarning: Some current students still have no report:")
            display(missing_after_generation[["_student_id_key"]])

        final_output_df = (
            final_output_df
            .sort_values("_input_order")
            .drop(columns=["_student_id_key", "_input_order"], errors="ignore")
        )

        self.save_output_safely(final_output_df, output_csv)

        print(f"\nCurrent output saved to: {output_csv}")
        print(f"Current output shape: {final_output_df.shape}")
        print(f"New LLM calls made: {len(new_rows)}")
        print(f"Reused reports from store: {total_students - len(new_rows)}")

        return final_output_df