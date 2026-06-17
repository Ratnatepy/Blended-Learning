import os
import json
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd
try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - allows rule-based fallback without optional client dependency
    OpenAI = None

from blended_learning.config.settings import settings


class OpenRouterStudentRecommender:
    """
    OpenRouter LLM recommender for the blended learning thesis prototype.

    The rule-based recommendations are the source of truth.
    The LLM only rewrites them into readable student-facing feedback.

    Runtime constants are read from config.json under the `llm` section.
    Secrets such as OPENROUTER_API_KEY remain in .env or shell environment
    variables and are never stored in config.json.
    """

    def __init__(
        self,
        api_key=None,
        model=None,
        base_url=None,
        prompt_path=None,
        app_title=None,
        settings_obj=None,
    ):
        self.settings = settings_obj or settings
        self.cfg = getattr(self.settings, "llm", {})
        self.openrouter_cfg = self.cfg.get("openrouter", {})
        self.generation_cfg = self.cfg.get("generation", {})
        self.data_cfg = self.cfg.get("data", {})
        self.safety_cfg = self.cfg.get("safety", {})
        self.saving_cfg = self.cfg.get("saving", {})
        self.fallback_cfg = self.cfg.get("fallback_report", {})
        self.prompt_cfg = self.cfg.get("prompt_building", {})

        env_cfg = self.openrouter_cfg.get("env", {})
        defaults = self.openrouter_cfg.get("defaults", {})

        api_key_env = env_cfg.get("api_key", "OPENROUTER_API_KEY")
        model_env = env_cfg.get("model", "OPENROUTER_MODEL")
        base_url_env = env_cfg.get("base_url", "OPENROUTER_BASE_URL")
        app_title_env = env_cfg.get("app_title", "OPENROUTER_APP_TITLE")
        http_referer_env = env_cfg.get("http_referer", "OPENROUTER_HTTP_REFERER")

        self.api_key = api_key if api_key is not None else os.getenv(api_key_env)
        self.model = os.getenv(
            model_env,
            model or defaults.get("model", "openai/gpt-oss-120b:free"),
        )
        self.base_url = os.getenv(
            base_url_env,
            base_url or defaults.get("base_url", "https://openrouter.ai/api/v1"),
        )
        self.app_title = os.getenv(
            app_title_env,
            app_title or defaults.get("app_title", "Blended Learning Prototype"),
        )
        self.http_referer = os.getenv(
            http_referer_env,
            defaults.get("http_referer", "http://localhost"),
        )

        self.last_generation_source = None
        self.last_generation_error = None
        self.last_error = None

        self.prompt_path = self.resolve_project_path(
            prompt_path or self.openrouter_cfg.get(
                "prompt_path",
                "src/blended_learning/llm/prompts/student_recommendation_prompt.txt",
            )
        )

        self.openai_available = OpenAI is not None
        self.client = (
            OpenAI(base_url=self.base_url, api_key=self.api_key)
            if self.api_key and self.openai_available
            else None
        )

        self.system_prompt = self.load_prompt(self.prompt_path)

    # ---------------------------------------------------------
    # Config helpers
    # ---------------------------------------------------------

    def resolve_project_path(self, path_value):
        """Resolve a path relative to the ML project root unless absolute."""
        path = Path(path_value)
        if path.is_absolute():
            return path
        return (Path(self.settings.root) / path).resolve()

    def get_batch_generation_param(self, name, provided=None):
        """Read generation parameters from config unless explicitly passed."""
        if provided is not None:
            return provided
        batch_cfg = self.generation_cfg.get("clean_batch", {})
        incremental_cfg = self.generation_cfg.get("incremental", {})
        return batch_cfg.get(name, incremental_cfg.get(name))

    def get_csv_write_options(self):
        return self.cfg.get("io", {}).get(
            "write_csv_options",
            {"index": False, "encoding": "utf-8-sig"},
        )

    def get_output_columns(self):
        return self.data_cfg.get(
            "output_columns",
            [
                "student_id",
                "student_segment_label",
                "final_recommendation_tags",
                "llm_recommendation_report",
            ],
        )

    def get_store_columns(self):
        return self.data_cfg.get(
            "store_columns",
            self.get_output_columns()
            + ["generation_source", "generation_error", "generated_at"],
        )

    # ---------------------------------------------------------
    # Prompt
    # ---------------------------------------------------------

    def load_prompt(self, prompt_path):
        """Load the system prompt from a text file."""
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read()

    # ---------------------------------------------------------
    # JSON parsing
    # ---------------------------------------------------------

    def parse_json_field(self, value, default=None):
        """Parse JSON string columns from the CSV."""
        if default is None:
            default = []

        if pd.isna(value):
            return default

        if isinstance(value, (list, dict)):
            return value

        try:
            return json.loads(value)
        except Exception:
            return default

    # ---------------------------------------------------------
    # Data loading
    # ---------------------------------------------------------

    def load_recommendation_data(self, csv_path):
        """Load student recommendation feature CSV and parse JSON columns."""
        read_options = self.cfg.get("io", {}).get("read_csv_options", {})
        df = pd.read_csv(csv_path, **read_options)

        json_columns = self.data_cfg.get(
            "json_columns",
            [
                "strength_themes",
                "challenge_themes",
                "strength_tags",
                "challenge_tags",
                "recommendation_tags",
                "segment_default_tags",
                "final_recommendation_tags",
                "rule_based_recommendations",
            ],
        )

        for col in json_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.parse_json_field)

        return df

    # ---------------------------------------------------------
    # Student package
    # ---------------------------------------------------------

    def build_student_package(self, row):
        """Build one structured evidence package for the LLM."""
        fields = self.data_cfg.get(
            "student_package_fields",
            [
                "student_id",
                "student_segment",
                "student_segment_label",
                "cluster_label",
                "open_strengths_clean",
                "open_challenges_clean",
                "strength_sentiment_label",
                "challenge_sentiment_label",
                "strength_compound",
                "challenge_compound",
                "strength_themes",
                "challenge_themes",
                "recommendation_tags",
                "segment_default_tags",
                "final_recommendation_tags",
                "rule_based_recommendations",
            ],
        )
        list_default_fields = set(self.data_cfg.get("list_default_fields", []))

        student_package = {}
        for field in fields:
            default = [] if field in list_default_fields else ""
            student_package[field] = row.get(field, default)

        return student_package

    # ---------------------------------------------------------
    # Rule-based fallback
    # ---------------------------------------------------------

    def build_rule_based_report(self, student_package):
        """Fallback report if API key is missing or LLM generation fails."""
        segment_col = self.data_cfg.get(
            "segment_label_column",
            "student_segment_label",
        )
        segment = student_package.get(
            segment_col,
            self.fallback_cfg.get("default_segment", "Unknown segment"),
        )

        strengths = student_package.get("strength_themes", [])
        challenges = student_package.get("challenge_themes", [])
        recommendations = student_package.get("rule_based_recommendations", [])

        report = [self.fallback_cfg.get(
            "title",
            "# Personalized Blended Learning Recommendation Report",
        ), ""]

        report.append(self.fallback_cfg.get(
            "profile_heading",
            "## 1. Student Learning Profile",
        ))
        profile_template = self.fallback_cfg.get(
            "profile_template",
            "The student belongs to the **{segment}** profile.",
        )
        report.append(profile_template.format(segment=segment))
        report.append("")

        report.append(self.fallback_cfg.get(
            "strength_heading",
            "## 2. Main Strengths",
        ))
        if strengths:
            for theme in strengths:
                report.append(f"- {theme}")
        else:
            report.append(f"- {self.fallback_cfg.get('no_strength_text', 'No clear strength theme was detected.')}")
        report.append("")

        report.append(self.fallback_cfg.get(
            "challenge_heading",
            "## 3. Main Challenges",
        ))
        if challenges:
            for theme in challenges:
                report.append(f"- {theme}")
        else:
            report.append(f"- {self.fallback_cfg.get('no_challenge_text', 'No clear challenge theme was detected.')}")
        report.append("")

        report.append(self.fallback_cfg.get(
            "recommendation_heading",
            "## 4. Personalized Recommendations",
        ))
        if recommendations:
            for rec in recommendations:
                title = rec.get("title", "Recommendation")
                text = rec.get("recommendation", "")
                report.append(f"- **{title}:** {text}")
        else:
            report.append(f"- {self.fallback_cfg.get('no_recommendation_text', 'Use the student profile to provide general support.')}")
        report.append("")

        report.append(self.fallback_cfg.get(
            "action_plan_heading",
            "## 5. Short Action Plan",
        ))
        for item in self.fallback_cfg.get("action_plan_items", []):
            report.append(f"- {item}")

        return "\n".join(report)

    # ---------------------------------------------------------
    # Prompt building
    # ---------------------------------------------------------

    def build_user_prompt(self, student_package):
        """Build the user prompt dynamically from student evidence."""
        task_instruction = self.prompt_cfg.get(
            "task_instruction",
            "Create a personalized blended learning recommendation report for this student.",
        )
        evidence_heading = self.prompt_cfg.get("evidence_heading", "Student evidence:")
        rules = self.prompt_cfg.get("rules", [])
        rules_text = "\n".join(f"- {rule}" for rule in rules)

        return f"""
{task_instruction}

{evidence_heading}
{json.dumps(student_package, ensure_ascii=False, indent=2)}

Rules:
{rules_text}
""".strip()

    # ---------------------------------------------------------
    # LLM generation
    # ---------------------------------------------------------

    def generate_report(self, student_package, temperature=None, max_tokens=None):
        """
        Generate one recommendation report.

        With OPENROUTER_API_KEY configured, this calls OpenRouter.
        If the key is missing or the request fails, it returns the
        rule-based fallback so the prototype remains usable.
        """
        self.last_generation_source = None
        self.last_generation_error = None
        self.last_error = None

        temperature = self.get_batch_generation_param("temperature", temperature)
        max_tokens = self.get_batch_generation_param("max_tokens", max_tokens)

        if not self.client:
            self.last_generation_source = self.safety_cfg.get(
                "missing_api_key_source",
                "rule_based_fallback_no_api_key",
            )
            if self.api_key and not self.openai_available:
                self.last_generation_error = self.safety_cfg.get(
                    "missing_openai_package_error",
                    "The openai package is not installed, so OpenRouter generation is unavailable.",
                )
            else:
                self.last_generation_error = self.safety_cfg.get(
                    "missing_api_key_error",
                    "OPENROUTER_API_KEY is not configured.",
                )
            self.last_error = self.last_generation_error
            return self.build_rule_based_report(student_package)

        user_prompt = self.build_user_prompt(student_package)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers={
                    "HTTP-Referer": self.http_referer,
                    "X-Title": self.app_title,
                },
            )

            self.last_generation_source = self.safety_cfg.get(
                "openrouter_success_source",
                "openrouter_llm",
            )
            self.last_generation_error = None
            self.last_error = None
            return response.choices[0].message.content

        except Exception as error:
            self.last_generation_source = self.safety_cfg.get(
                "openrouter_error_source",
                "rule_based_fallback_openrouter_error",
            )
            self.last_generation_error = str(error)
            self.last_error = self.last_generation_error
            print("OpenRouter generation failed:", error)
            print("Returning rule-based fallback report.")
            return self.build_rule_based_report(student_package)

    # ---------------------------------------------------------
    # Output row
    # ---------------------------------------------------------

    def build_output_row(self, row, student_package, report):
        """Build one output row for the recommendation result CSV."""
        return {
            "student_id": row.get("student_id", None),
            "student_segment_label": row.get("student_segment_label", None),
            "final_recommendation_tags": json.dumps(
                student_package.get("final_recommendation_tags", []),
                ensure_ascii=False,
            ),
            "llm_recommendation_report": report,
        }

    # ---------------------------------------------------------
    # Backup and rollback
    # ---------------------------------------------------------

    def backup_file(self, file_path):
        """Create a timestamped backup of an existing file."""
        if not os.path.exists(file_path):
            return None

        timestamp = datetime.now().strftime(
            self.saving_cfg.get("timestamp_format", "%Y%m%d_%H%M%S")
        )
        backup_prefix = self.saving_cfg.get("backup_prefix", ".backup_")
        backup_path = f"{file_path}{backup_prefix}{timestamp}"
        shutil.copy2(file_path, backup_path)
        return backup_path

    def rollback_file(self, backup_path, output_csv):
        """Restore output CSV from backup."""
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, output_csv)
            print(f"Rollback completed. Restored from: {backup_path}")
        else:
            print("No backup file found. Rollback skipped.")

    def save_output_safely(self, output_df, output_csv):
        """Save DataFrame safely using a temporary file first."""
        output_dir = os.path.dirname(output_csv)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        temp_output_csv = output_csv + self.saving_cfg.get("temp_suffix", ".tmp")
        output_df.to_csv(temp_output_csv, **self.get_csv_write_options())
        os.replace(temp_output_csv, output_csv)

    # ---------------------------------------------------------
    # Append progress
    # ---------------------------------------------------------

    def append_output_row_safely(self, output_row, output_csv):
        """Append one student result to output CSV immediately."""
        output_dir = os.path.dirname(output_csv)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        row_df = pd.DataFrame([output_row])
        file_exists = os.path.exists(output_csv)
        write_options = self.get_csv_write_options().copy()
        write_options.update({"mode": "a", "header": not file_exists})
        row_df.to_csv(output_csv, **write_options)

    # ---------------------------------------------------------
    # Direct one-student generation without CSV
    # ---------------------------------------------------------

    def generate_report_from_package(self, student_data, temperature=None, max_tokens=None):
        """Generate one report from a dictionary or pandas Series."""
        student_package = self.build_student_package(student_data)
        return self.generate_report(
            student_package=student_package,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # ---------------------------------------------------------
    # One student by ID from CSV
    # ---------------------------------------------------------

    def generate_report_for_student_id(
        self,
        input_csv,
        student_id,
        output_csv=None,
        temperature=None,
        max_tokens=None,
    ):
        """Generate a recommendation report for one student by student_id."""
        df = self.load_recommendation_data(input_csv)
        student_id_col = self.data_cfg.get("student_id_column", "student_id")

        if student_id_col not in df.columns:
            raise ValueError(f"The input CSV does not contain '{student_id_col}'.")

        student_rows = df[df[student_id_col].astype(str) == str(student_id)]
        if student_rows.empty:
            raise ValueError(f"No student found with student_id: {student_id}")

        row = student_rows.iloc[0]
        student_package = self.build_student_package(row)
        report = self.generate_report(
            student_package=student_package,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        output_row = self.build_output_row(row=row, student_package=student_package, report=report)
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
        temperature=None,
        max_tokens=None,
        resume=None,
        save_each_student=None,
    ):
        """Generate recommendation reports using input, optional resume, and output CSV files."""
        def make_student_key(series):
            return series.astype(str).str.strip()

        clean_batch_cfg = self.generation_cfg.get("clean_batch", {})
        if limit is None:
            limit = clean_batch_cfg.get("limit")
        if temperature is None:
            temperature = clean_batch_cfg.get("temperature")
        if max_tokens is None:
            max_tokens = clean_batch_cfg.get("max_tokens")
        if resume is None:
            resume = clean_batch_cfg.get("resume", True)
        if save_each_student is None:
            save_each_student = clean_batch_cfg.get("save_each_student", True)

        student_id_col = self.data_cfg.get("student_id_column", "student_id")
        student_key_col = self.saving_cfg.get("student_key_column", "_student_id_key")
        order_col = self.saving_cfg.get("order_column", "_order")

        output_csv = str(output_csv)
        backup_path = self.backup_file(output_csv)

        try:
            df = self.load_recommendation_data(input_csv)
            if student_id_col not in df.columns:
                raise ValueError(f"The input CSV does not contain '{student_id_col}'.")

            df_to_process = df.head(limit).copy() if limit is not None else df.copy()
            df_to_process[student_key_col] = make_student_key(df_to_process[student_id_col])
            current_student_ids = set(df_to_process[student_key_col])
            print(f"Input dataset shape: {df_to_process.shape}")

            reusable_previous_reports = pd.DataFrame()
            processed_student_ids = set()

            if resume and resume_csv is not None and os.path.exists(resume_csv):
                previous_df = pd.read_csv(resume_csv, **self.cfg.get("io", {}).get("read_csv_options", {}))
                if student_id_col not in previous_df.columns:
                    raise ValueError(f"The resume CSV does not contain '{student_id_col}'.")

                previous_df[student_key_col] = make_student_key(previous_df[student_id_col])
                previous_df = previous_df[previous_df[student_key_col].isin(current_student_ids)].copy()
                previous_df = previous_df.drop_duplicates(subset=student_key_col, keep="last")
                reusable_previous_reports = previous_df.copy()
                processed_student_ids = set(reusable_previous_reports[student_key_col])
                print(f"Resume file loaded: {resume_csv}")
                print(f"Reusable previous reports: {len(reusable_previous_reports)}")
            else:
                print("No resume file used. Starting fresh.")

            output_cols = self.get_output_columns()
            if not reusable_previous_reports.empty:
                reusable_to_save = reusable_previous_reports[
                    [c for c in output_cols if c in reusable_previous_reports.columns]
                ].copy()
                self.save_output_safely(reusable_to_save, output_csv)
            else:
                self.save_output_safely(pd.DataFrame(columns=output_cols), output_csv)

            results = []
            total_students = len(df_to_process)

            for count, (_, row) in enumerate(df_to_process.iterrows(), start=1):
                student_id = row.get(student_id_col, None)
                student_key = str(student_id).strip()

                if resume and student_key in processed_student_ids:
                    print(f"[{count}/{total_students}] Skipping already processed student: {student_id}")
                    continue

                print(f"[{count}/{total_students}] Generating report for student: {student_id}")
                student_package = self.build_student_package(row)
                report = self.generate_report(
                    student_package=student_package,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                output_row = self.build_output_row(row=row, student_package=student_package, report=report)
                results.append(output_row)

                if save_each_student:
                    self.append_output_row_safely(output_row=output_row, output_csv=output_csv)
                    processed_student_ids.add(student_key)
                    print(f"Saved progress for student: {student_id}")

            final_output_df = pd.read_csv(output_csv, **self.cfg.get("io", {}).get("read_csv_options", {}))
            final_output_df[student_key_col] = make_student_key(final_output_df[student_id_col])
            final_output_df = final_output_df[
                final_output_df[student_key_col].isin(current_student_ids)
            ].copy()
            final_output_df = final_output_df.drop_duplicates(subset=student_key_col, keep="last")

            student_order = df_to_process[student_key_col].tolist()
            final_output_df[order_col] = pd.Categorical(
                final_output_df[student_key_col], categories=student_order, ordered=True
            )
            final_output_df = (
                final_output_df
                .sort_values(order_col)
                .drop(columns=[student_key_col, order_col], errors="ignore")
            )

            self.save_output_safely(final_output_df, output_csv)
            print(f"\nGenerated reports saved to: {output_csv}")
            print(f"Final output shape: {final_output_df.shape}")
            return final_output_df

        except KeyboardInterrupt:
            print("Process interrupted by user.")
            print("Progress already saved in output CSV.")
            if os.path.exists(output_csv):
                return pd.read_csv(output_csv, **self.cfg.get("io", {}).get("read_csv_options", {}))
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
        temperature=None,
        max_tokens=None,
        save_after_each_new_student=None,
    ):
        """Incremental LLM report generation using current input, master store, and current output."""
        incremental_cfg = self.generation_cfg.get("incremental", {})
        if limit is None:
            limit = incremental_cfg.get("limit")
        if temperature is None:
            temperature = incremental_cfg.get("temperature")
        if max_tokens is None:
            max_tokens = incremental_cfg.get("max_tokens")
        if save_after_each_new_student is None:
            save_after_each_new_student = incremental_cfg.get("save_after_each_new_student", True)

        input_csv = str(input_csv)
        store_csv = str(store_csv)
        output_csv = str(output_csv)

        student_id_col = self.data_cfg.get("student_id_column", "student_id")
        student_key_col = self.saving_cfg.get("student_key_column", "_student_id_key")
        input_order_col = self.saving_cfg.get("input_order_column", "_input_order")

        def normalize_student_id(value):
            if pd.isna(value):
                return ""
            return str(value).strip()

        def clean_store_df(store_df):
            if store_df.empty:
                return store_df
            store_df[student_key_col] = store_df[student_id_col].apply(normalize_student_id)
            store_df = store_df[store_df[student_key_col] != ""].copy()
            store_df = store_df.drop_duplicates(subset=student_key_col, keep="last")
            return store_df

        df = self.load_recommendation_data(input_csv)
        if student_id_col not in df.columns:
            raise ValueError(f"input_csv must contain '{student_id_col}' column.")

        df_to_process = df.head(limit).copy() if limit is not None else df.copy()
        df_to_process[student_key_col] = df_to_process[student_id_col].apply(normalize_student_id)
        df_to_process = df_to_process[df_to_process[student_key_col] != ""].copy()
        print(f"Current input dataset shape: {df_to_process.shape}")

        read_options = self.cfg.get("io", {}).get("read_csv_options", {})
        if os.path.exists(store_csv):
            store_df = pd.read_csv(store_csv, **read_options)
            print(f"Loaded existing store file: {store_csv}")
            print(f"Store shape before cleaning: {store_df.shape}")
        else:
            store_df = pd.DataFrame(columns=self.get_store_columns())
            print("No existing store file found. Creating new store.")

        if not store_df.empty and student_id_col not in store_df.columns:
            raise ValueError(f"store_csv must contain '{student_id_col}' column.")

        store_df = clean_store_df(store_df)
        existing_student_ids = set(store_df[student_key_col]) if not store_df.empty else set()
        print(f"Store shape after cleaning: {store_df.shape}")
        print(f"Existing generated students in store: {len(existing_student_ids)}")

        new_rows = []
        total_students = len(df_to_process)

        for count, (_, row) in enumerate(df_to_process.iterrows(), start=1):
            student_id = row.get(student_id_col, None)
            student_key = normalize_student_id(student_id)

            if student_key in existing_student_ids:
                print(f"[{count}/{total_students}] Already exists in store, skip LLM: {student_id}")
                continue

            print(f"[{count}/{total_students}] New student detected, calling LLM: {student_id}")
            student_package = self.build_student_package(row)
            report = self.generate_report(
                student_package=student_package,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            output_row = self.build_output_row(row=row, student_package=student_package, report=report)
            output_row["generation_source"] = self.last_generation_source
            output_row["generation_error"] = self.last_generation_error
            output_row["generated_at"] = datetime.now().strftime(
                self.saving_cfg.get("generated_at_format", "%Y-%m-%d %H:%M:%S")
            )
            output_row[student_key_col] = student_key

            new_rows.append(output_row)
            existing_student_ids.add(student_key)

            if save_after_each_new_student:
                store_df = pd.concat([store_df, pd.DataFrame([output_row])], ignore_index=True)
                store_df = clean_store_df(store_df)
                store_to_save = store_df.drop(columns=[student_key_col], errors="ignore")
                self.save_output_safely(store_to_save, store_csv)
                print(f"Saved new report to store for student: {student_id}")

        if new_rows and not save_after_each_new_student:
            store_df = pd.concat([store_df, pd.DataFrame(new_rows)], ignore_index=True)

        store_df = clean_store_df(store_df)
        store_to_save = store_df.drop(columns=[student_key_col], errors="ignore")
        self.save_output_safely(store_to_save, store_csv)
        print(f"\nMaster store saved to: {store_csv}")
        print(f"Master store shape: {store_to_save.shape}")

        current_keys = df_to_process[[student_key_col]].copy()
        current_keys[input_order_col] = range(len(current_keys))
        final_output_df = current_keys.merge(store_df, on=student_key_col, how="left")

        report_col = self.data_cfg.get("report_column", "llm_recommendation_report")
        missing_after_generation = final_output_df[final_output_df[report_col].isna()]
        if len(missing_after_generation) > 0:
            print("\nWarning: Some current students still have no report:")
            print(missing_after_generation[[student_key_col]].to_string(index=False))

        final_output_df = (
            final_output_df
            .sort_values(input_order_col)
            .drop(columns=[student_key_col, input_order_col], errors="ignore")
        )

        self.save_output_safely(final_output_df, output_csv)
        print(f"\nCurrent output saved to: {output_csv}")
        print(f"Current output shape: {final_output_df.shape}")
        print(f"New LLM calls made: {len(new_rows)}")
        print(f"Reused reports from store: {total_students - len(new_rows)}")

        return final_output_df
