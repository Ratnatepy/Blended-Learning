# src/blended_learning/nlp/translate_kh_service.py

from __future__ import annotations

import os
import time
from typing import Any, Iterable

import requests

from blended_learning.config.settings import settings


class TranslateKHService:
    """
    Service for TranslateKH API.

    Runtime secrets stay in `.env` / environment variables:
        - TRANSLATE_KH_USERNAME
        - TRANSLATE_KH_PASSWORD
        - TRANSLATE_KH_API_URL, optional

    Non-secret behavior is controlled from `ml/config/config.json`:
        translation_preprocessing.translate_kh_service
    """

    DEFAULT_CONFIG: dict[str, Any] = {
        "env": {
            "api_url": "TRANSLATE_KH_API_URL",
            "username": "TRANSLATE_KH_USERNAME",
            "password": "TRANSLATE_KH_PASSWORD",
        },
        "default_api_url": "https://www.translate.kh/api",
        "timeout_seconds": 30,
        "valid_langs": ["kh", "eng"],
    }

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        api_url: str | None = None,
        timeout: int | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.cfg = self._merged_config(config=config)
        env_cfg = self.cfg["env"]

        self.api_url = (
            api_url
            or os.getenv(env_cfg["api_url"])
            or self.cfg["default_api_url"]
        )
        self.username = username or os.getenv(env_cfg["username"])
        self.password = password or os.getenv(env_cfg["password"])
        self.timeout = timeout if timeout is not None else self.cfg["timeout_seconds"]
        self.valid_langs = set(self.cfg["valid_langs"])

        if not self.username or not self.password:
            raise ValueError(
                "TranslateKH username or password is missing. "
                f"Please set {env_cfg['username']} and {env_cfg['password']} "
                "in your .env file or shell environment."
            )

    def _merged_config(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Merge defaults with config.json and optional explicit overrides."""
        merged = self._deep_copy(self.DEFAULT_CONFIG)
        project_config = (
            getattr(settings, "translation_preprocessing", {})
            .get("translate_kh_service", {})
        )
        self._deep_update(merged, project_config)
        if config:
            self._deep_update(merged, config)
        return merged

    @staticmethod
    def _deep_copy(value: dict[str, Any]) -> dict[str, Any]:
        return {
            key: TranslateKHService._deep_copy(item) if isinstance(item, dict) else item
            for key, item in value.items()
        }

    @staticmethod
    def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                TranslateKHService._deep_update(base[key], value)
            else:
                base[key] = value

    def _validate_langs(self, src_lang: str, tgt_lang: str) -> None:
        if src_lang not in self.valid_langs:
            raise ValueError(
                f"src_lang must be one of {sorted(self.valid_langs)}."
            )

        if tgt_lang not in self.valid_langs:
            raise ValueError(
                f"tgt_lang must be one of {sorted(self.valid_langs)}."
            )

        if src_lang == tgt_lang:
            raise ValueError("src_lang and tgt_lang cannot be the same.")

    def translate_texts(
        self,
        texts: str | Iterable[str],
        src_lang: str = "kh",
        tgt_lang: str = "eng",
    ) -> list[str]:
        """
        Translate one or multiple texts.

        Parameters
        ----------
        texts:
            Single text or list of texts. The API requires `input_text` to be an array.
        src_lang:
            Source language. Defaults to Khmer.
        tgt_lang:
            Target language. Defaults to English.
        """

        self._validate_langs(src_lang, tgt_lang)

        if isinstance(texts, str):
            texts = [texts]

        clean_texts = [
            str(text).strip()
            for text in texts
            if text is not None and str(text).strip() != ""
        ]

        if not clean_texts:
            return []

        payload = {
            "input_text": clean_texts,
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            translated_texts = data.get("translate_text")

            if not isinstance(translated_texts, list):
                print("Invalid API response format. Missing 'translate_text' list.")
                return []

            return translated_texts

        except requests.exceptions.Timeout:
            print("TranslateKH API timeout.")
            return []

        except requests.exceptions.HTTPError as error:
            print(f"TranslateKH API HTTP error: {error}")
            print(f"Response text: {response.text}")
            return []

        except requests.exceptions.RequestException as error:
            print(f"TranslateKH API request error: {error}")
            return []

        except Exception as error:
            print(f"Unexpected translation error: {error}")
            return []

    def translate_one(
        self,
        text: str,
        src_lang: str = "kh",
        tgt_lang: str = "eng",
    ) -> str:
        """Translate one text and return one translated string."""
        result = self.translate_texts(
            texts=[text],
            src_lang=src_lang,
            tgt_lang=tgt_lang,
        )

        return result[0] if result else ""

    def translate_batch_safely(
        self,
        texts: list[str],
        src_lang: str = "kh",
        tgt_lang: str = "eng",
        batch_size: int = 10,
        delay: float = 1.0,
    ) -> list[str]:
        """Translate many texts in small batches."""

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0.")

        all_results: list[str] = []

        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]

            translated_batch = self.translate_texts(
                texts=batch,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
            )

            all_results.extend(translated_batch)

            if start + batch_size < len(texts):
                time.sleep(delay)

        return all_results
