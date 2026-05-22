# src/blended_learning/nlp/translate_kh_service.py

from __future__ import annotations

import os
import time
from typing import Iterable

import requests


class TranslateKHService:
    """
    Service for TranslateKH API.

    Official API format:

    Endpoint:
        POST https://www.translate.kh/api

    Authentication:
        Basic Authentication

    Request:
        {
            "input_text": ["hello"],
            "src_lang": "eng",
            "tgt_lang": "kh"
        }

    Response:
        {
            "translate_text": ["សួស្តី"]
        }

    Supported languages:
        - "kh"  : Khmer
        - "eng" : English
    """

    VALID_LANGS = {"kh", "eng"}

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        api_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_url = api_url or os.getenv(
            "TRANSLATE_KH_API_URL",
            "https://www.translate.kh/api"
        )
        self.username = username or os.getenv("TRANSLATE_KH_USERNAME")
        self.password = password or os.getenv("TRANSLATE_KH_PASSWORD")
        self.timeout = timeout

        if not self.username or not self.password:
            raise ValueError(
                "TranslateKH username or password is missing. "
                "Please set TRANSLATE_KH_USERNAME and TRANSLATE_KH_PASSWORD in your .env file."
            )

    def _validate_langs(self, src_lang: str, tgt_lang: str) -> None:
        if src_lang not in self.VALID_LANGS:
            raise ValueError("src_lang must be either 'kh' or 'eng'.")

        if tgt_lang not in self.VALID_LANGS:
            raise ValueError("tgt_lang must be either 'kh' or 'eng'.")

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
            Single text or list of texts.
            The API requires input_text to be an array.

        src_lang:
            Source language: "kh" or "eng".

        tgt_lang:
            Target language: "kh" or "eng".

        Returns
        -------
        list[str]
            Translated texts in the same order as the cleaned input.
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
        """
        Translate one text and return one translated string.
        """

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
        """
        Translate many texts in small batches.

        This helps avoid duplicate, looping, or excessive API requests.
        """

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

            # Sleep only if there is another batch remaining
            if start + batch_size < len(texts):
                time.sleep(delay)

        return all_results