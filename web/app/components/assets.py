"""Asset and icon helpers for Streamlit UI."""

from __future__ import annotations

from pathlib import Path
import base64
import html

WEB_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = WEB_ROOT / "assets"
ICONS_DIR = ASSETS_DIR / "icons"


def resolve_asset_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    if candidate.exists():
        return candidate
    if str(candidate).startswith("assets/"):
        return WEB_ROOT / candidate
    return ASSETS_DIR / candidate


def image_to_base64(image_path: str | Path) -> str:
    path = resolve_asset_path(image_path)
    if not path.exists():
        return ""
    with path.open("rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def icon_svg(svg_path_or_name: str | Path, size: int = 18, color: str = "#f8fafc") -> str:
    """Return an SVG as an inline HTML string."""

    raw_path = Path(svg_path_or_name)
    if raw_path.suffix.lower() == ".svg":
        path = resolve_asset_path(raw_path)
    else:
        path = ICONS_DIR / f"{svg_path_or_name}.svg"

    if not path.exists():
        return ""

    svg = path.read_text(encoding="utf-8")

    if "width=" in svg:
        svg = svg.replace('width="24"', f'width="{size}"')
    else:
        svg = svg.replace("<svg", f'<svg width="{size}"', 1)

    if "height=" in svg:
        svg = svg.replace('height="24"', f'height="{size}"')
    else:
        svg = svg.replace("<svg", f'<svg height="{size}"', 1)

    safe_color = html.escape(color)
    svg = svg.replace('stroke="currentColor"', f'stroke="{safe_color}"')
    svg = svg.replace('stroke="#f8fafc"', f'stroke="{safe_color}"')
    svg = svg.replace('stroke="black"', f'stroke="{safe_color}"')
    svg = svg.replace("<svg", '<svg style="vertical-align:-3px; margin-right:6px;"', 1)

    return svg


def icon_span(name: str, text: str, size: int = 18, color: str = "#f8fafc") -> str:
    return f'{icon_svg(name, size=size, color=color)}<span>{html.escape(text)}</span>'


def icon_title(name: str, text: str, level: int = 3, color: str = "#f8fafc") -> str:
    level = max(1, min(level, 6))
    return f"""
    <h{level} style="display:flex; align-items:center; gap:0.35rem; color:{color};">
        {icon_svg(name, size=22, color=color)}
        <span>{html.escape(text)}</span>
    </h{level}>
    """
