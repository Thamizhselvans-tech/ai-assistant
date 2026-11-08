"""Frontend configuration constants, theme definitions, and backend endpoints."""

import os
from pathlib import Path
import streamlit as st


def get_backend_url() -> str:
    """Retrieve backend API URL dynamically from Streamlit secrets, environment, or fallback.

    Priority order:
    1. Streamlit Community Cloud secrets: st.secrets["BACKEND_API_URL"] or st.secrets["API_BASE_URL"]
    2. Environment variables: BACKEND_API_URL or API_BASE_URL
    3. Local development fallback: http://localhost:8000
    """
    try:
        if hasattr(st, "secrets"):
            if "BACKEND_API_URL" in st.secrets:
                return str(st.secrets["BACKEND_API_URL"]).rstrip("/")
            if "API_BASE_URL" in st.secrets:
                return str(st.secrets["API_BASE_URL"]).rstrip("/")
    except Exception:
        pass

    env_url = os.environ.get("BACKEND_API_URL") or os.environ.get("API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")

    return "http://localhost:8000"


BACKEND_API_URL = get_backend_url()
APP_TITLE = "AI Knowledge Assistant"
APP_SUBTITLE = "Enterprise Document RAG Platform"
APP_VERSION = "1.0.0"

SUPPORTED_FILE_TYPES = ["pdf", "docx", "txt"]
MAX_UPLOAD_SIZE_MB = 15

# Theme Palettes
THEMES = {
    "dark": {
        "bg_primary": "#0E131F",
        "bg_card": "#161F30",
        "bg_secondary": "#1E293B",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "accent_emerald": "#10B981",
        "accent_blue": "#3B82F6",
        "border_color": "#27354A",
    },
    "light": {
        "bg_primary": "#F8FAFC",
        "bg_card": "#FFFFFF",
        "bg_secondary": "#F1F5F9",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "accent_emerald": "#059669",
        "accent_blue": "#2563EB",
        "border_color": "#E2E8F0",
    }
}

FILE_ICONS = {
    "pdf": "📄",
    "docx": "📝",
    "txt": "📃",
}

STATUS_COLORS = {
    "completed": "#10B981",  # Emerald Green
    "processing": "#3B82F6", # Sky Blue
    "warning": "#F59E0B",    # Amber
    "failed": "#EF4444",     # Crimson Red
    "pending": "#64748B",    # Slate Gray
}


def inject_custom_css() -> None:
    """Inject custom SaaS CSS into Streamlit page."""
    base_dir = Path(__file__).parent
    css_path = base_dir / "styles" / "custom.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
