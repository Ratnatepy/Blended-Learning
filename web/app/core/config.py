"""Frontend configuration and path resolution helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import os

from dotenv import load_dotenv

WEB_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = WEB_ROOT / "app"
PROJECT_ROOT = WEB_ROOT.parent
DEFAULT_SHARED_CONFIG = PROJECT_ROOT / "ml" / "config" / "config.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _get_nested(data: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


@dataclass(frozen=True)
class ThemeSettings:
    """Visual theme settings for Streamlit CSS and Plotly charts."""

    mode: str = "dark"
    streamlit: dict[str, Any] = field(default_factory=dict)
    colors: dict[str, str] = field(default_factory=dict)
    layout: dict[str, int | float] = field(default_factory=dict)
    plotly: dict[str, str] = field(default_factory=dict)

    def color(self, name: str, default: str) -> str:
        return self.colors.get(name, default)

    def layout_value(self, name: str, default: int | float) -> int | float:
        return self.layout.get(name, default)

    def plotly_value(self, name: str, default: str) -> str:
        return self.plotly.get(name, default)


@dataclass(frozen=True)
class WebSettings:
    """Runtime settings for the Streamlit frontend."""

    project_root: Path
    web_root: Path
    app_root: Path
    assets_dir: Path
    shared_config_path: Path
    shared_config: dict[str, Any] = field(default_factory=dict)
    api_base_url: str = "http://127.0.0.1:8000"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    page_title: str = "Blended Learning Recommendation System"
    logo_filename: str = "itc_logo.png"
    default_get_timeout: int = 20
    default_post_timeout: int = 300
    segment_order: tuple[str, ...] = (
        "Highly Engaged (Active) Learners",
        "Moderately Engaged (Passive) Learners",
    )
    segment_color_map: dict[str, str] = field(default_factory=lambda: {
        "Highly Engaged (Active) Learners": "#22c55e",
        "Moderately Engaged (Passive) Learners": "#ef4444",
        "Unknown": "#94a3b8",
    })
    page_subtitles: dict[str, str] = field(default_factory=dict)
    data_summary: dict[str, int | str] = field(default_factory=dict)
    ux: dict[str, Any] = field(default_factory=dict)
    theme: ThemeSettings = field(default_factory=ThemeSettings)

    @property
    def logo_path(self) -> Path:
        return self.assets_dir / self.logo_filename


def load_web_settings() -> WebSettings:
    """Load frontend settings from environment variables plus shared project config."""

    load_dotenv()

    raw_config_path = os.getenv("WEB_CONFIG_PATH") or os.getenv("CONFIG_PATH")
    config_path = Path(raw_config_path) if raw_config_path else DEFAULT_SHARED_CONFIG
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    # The backend also uses CONFIG_PATH. During local Streamlit runs this may
    # point to a Docker-only path such as /app/ml/config/config.json. Fall back
    # to the project-local config when the environment path does not exist.
    if not config_path.exists():
        config_path = DEFAULT_SHARED_CONFIG

    shared_config = _read_json(config_path)
    web_cfg = shared_config.get("web", {}) if isinstance(shared_config, dict) else {}

    api_cfg = web_cfg.get("api", {})
    admin_cfg = web_cfg.get("admin", {})
    page_cfg = web_cfg.get("page", {})
    segment_cfg = web_cfg.get("segment_display", {})
    theme_cfg = web_cfg.get("theme", {})
    ux_cfg = web_cfg.get("ux", {})

    api_env = api_cfg.get("base_url_env", "API_BASE_URL")
    admin_email_env = admin_cfg.get("email_env", "ADMIN_EMAIL")
    admin_password_env = admin_cfg.get("password_env", "ADMIN_PASSWORD")

    return WebSettings(
        project_root=PROJECT_ROOT,
        web_root=WEB_ROOT,
        app_root=APP_ROOT,
        assets_dir=WEB_ROOT / "assets",
        shared_config_path=config_path,
        shared_config=shared_config,
        api_base_url=os.getenv(api_env, api_cfg.get("default_base_url", "http://127.0.0.1:8000")),
        admin_email=os.getenv(admin_email_env, admin_cfg.get("default_email", "admin@example.com")),
        admin_password=os.getenv(admin_password_env, admin_cfg.get("default_password", "admin123")),
        page_title=page_cfg.get("title", "Blended Learning Recommendation System"),
        logo_filename=page_cfg.get("logo_filename", "itc_logo.png"),
        default_get_timeout=int(api_cfg.get("default_get_timeout_seconds", 20)),
        default_post_timeout=int(api_cfg.get("default_post_timeout_seconds", 300)),
        segment_order=tuple(segment_cfg.get("order", [
            "Highly Engaged (Active) Learners",
            "Moderately Engaged (Passive) Learners",
        ])),
        segment_color_map=segment_cfg.get("colors", {
            "Highly Engaged (Active) Learners": "#22c55e",
            "Moderately Engaged (Passive) Learners": "#ef4444",
            "Unknown": "#94a3b8",
        }),
        page_subtitles=page_cfg.get("subtitles", {}),
        data_summary=web_cfg.get("data_summary", {}),
        ux=ux_cfg if isinstance(ux_cfg, dict) else {},
        theme=ThemeSettings(
            mode=theme_cfg.get("mode", "dark"),
            streamlit=theme_cfg.get("streamlit", {}),
            colors=theme_cfg.get("colors", {}),
            layout=theme_cfg.get("layout", {}),
            plotly=theme_cfg.get("plotly", {}),
        ),
    )
