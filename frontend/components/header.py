"""Reusable application header component with breadcrumbs and action triggers."""

from typing import Optional
import streamlit as st


def render_header(title: str, subtitle: Optional[str] = None, badge_text: Optional[str] = None) -> None:
    """Render a consistent, modern page header with green + pink gradient."""
    badge_html = f'<span style="background: rgba(236, 72, 153, 0.15); color: #EC4899; border: 1px solid rgba(236, 72, 153, 0.3); font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 9999px; vertical-align: middle; margin-left: 8px;">{badge_text}</span>' if badge_text else ""
    subtitle_html = f'<p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.95rem;">{subtitle}</p>' if subtitle else ""

    st.markdown(
        f"""
        <div style="margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 1px solid #27354A;">
            <h1 style="margin: 0; font-size: 1.85rem; font-weight: 800; background: linear-gradient(90deg, #10B981 0%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: inline-block;">
                {title}
            </h1> {badge_html}
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True
    )


__all__ = ["render_header"]
