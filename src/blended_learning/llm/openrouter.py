import os
import json
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd
from openai import OpenAI

from blended_learning.config.settings import settings


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
        self.base_url = base_url
        self.app_title = app_title

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
        Generate one LLM recommendation report.

        If OpenRouter is unavailable, return rule-based fallback.
        """
        if not self.client:
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
                    "HTTP-Referer": "http://localhost",
                    "X-Title": self.app_title
                }
            )

            return response.choices[0].message.content

        except Exception as error:
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
        limit=10,
        temperature=0.3,
        max_tokens=900,
        resume=True,
        save_each_student=True
    ):
        """
        Generate recommendation reports from CSV.

        Args:
            input_csv:
                Path to input feature CSV.

            output_csv:
                Path to save generated recommendation reports.

            limit:
                Number of students to process.
                Use limit=None to process all students.

            temperature:
                LLM temperature.

            max_tokens:
                Maximum generated tokens per report.

            resume:
                If True, already processed students in output_csv are skipped.

            save_each_student:
                If True, save each student immediately after generation.
                This is best for interruption recovery.

        Recommended for full batch:
            resume=True
            save_each_student=True
        """
        backup_path = self.backup_file(output_csv)

        try:
            df = self.load_recommendation_data(input_csv)

            if limit is not None:
                df_to_process = df.head(limit).copy()
            else:
                df_to_process = df.copy()

            existing_output_df = pd.DataFrame()
            processed_student_ids = set()

            if resume and os.path.exists(output_csv):
                existing_output_df = pd.read_csv(output_csv)

                if "student_id" in existing_output_df.columns:
                    processed_student_ids = set(
                        existing_output_df["student_id"].astype(str)
                    )

            results = []

            total_students = len(df_to_process)

            for count, (_, row) in enumerate(
                df_to_process.iterrows(),
                start=1
            ):
                student_id = row.get("student_id", None)

                if resume and str(student_id) in processed_student_ids:
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

                    processed_student_ids.add(str(student_id))

                    print(f"Saved progress for student: {student_id}")

            if save_each_student:
                if os.path.exists(output_csv):
                    return pd.read_csv(output_csv)

                return pd.DataFrame(results)

            new_output_df = pd.DataFrame(results)

            if resume and not existing_output_df.empty:
                final_output_df = pd.concat(
                    [existing_output_df, new_output_df],
                    ignore_index=True
                )
            else:
                final_output_df = new_output_df

            self.save_output_safely(final_output_df, output_csv)

            return final_output_df

        except KeyboardInterrupt:
            print("Process interrupted by user.")
            print("Progress already saved for completed students.")

            if os.path.exists(output_csv):
                return pd.read_csv(output_csv)

            return pd.DataFrame(results)

        except Exception as error:
            print("Batch report generation failed:", error)

            if not save_each_student:
                self.rollback_file(backup_path, output_csv)
            else:
                print(
                    "Rollback skipped because save_each_student=True. "
                    "Completed student rows were already saved."
                )

            raise error
