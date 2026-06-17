"""Small reusable FastAPI client for the Streamlit frontend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass(frozen=True)
class ApiClient:
    """Wrap requests so pages share consistent timeout and error handling."""

    base_url: str
    default_get_timeout: int = 20
    default_post_timeout: int = 300

    def _build_url(self, endpoint: str) -> str:
        endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        return f"{self.base_url.rstrip('/')}{endpoint}"

    def get(self, endpoint: str, timeout: int | None = None):
        """Return (response, error_type, error_message) for compatibility with pages."""
        try:
            response = requests.get(
                self._build_url(endpoint),
                timeout=timeout or self.default_get_timeout,
            )
            return response, None, None
        except requests.exceptions.ConnectionError as error:
            return None, "connection_error", str(error)
        except requests.exceptions.Timeout as error:
            return None, "timeout_error", str(error)
        except requests.exceptions.RequestException as error:
            return None, "request_error", str(error)

    def post(self, endpoint: str, payload: dict[str, Any], timeout: int | None = None):
        """Return (response, error_type, error_message) for compatibility with pages."""
        try:
            response = requests.post(
                self._build_url(endpoint),
                json=payload,
                timeout=timeout or self.default_post_timeout,
            )
            return response, None, None
        except requests.exceptions.ConnectionError as error:
            return None, "connection_error", str(error)
        except requests.exceptions.Timeout as error:
            return None, "timeout_error", str(error)
        except requests.exceptions.RequestException as error:
            return None, "request_error", str(error)
