"""Reusable application header component with breadcrumbs and action triggers."""

from typing import Optional
import streamlit as st


def render_header(title: str, subtitle: Optional[str] = None, badge_text: Optional[str] = None) -> None:
    """Render a consistent, modern page header."""
    badge_html = f'<span style="background: rgba(59, 130, 246, 0.2); color: #3B82F6; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 9999px; vertical-align: middle; margin-left: 8px;">{badge_text}</span>' if badge_text else ""
    subtitle_html = f'<p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.95rem;">{subtitle}</p>' if subtitle else ""

    st.markdown(
        f"""
        <div style="margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 1px solid #27354A;">
            <h1 style="margin: 0; font-size: 1.85rem; font-weight: 700; color: #F8FAFC; display: inline-block;">
                {title} {badge_html}
            </h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True
    )


__all__ = ["render_header"]
