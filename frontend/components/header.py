"""Reusable application top header component matching reference UI layout."""

from typing import Optional
import streamlit as st


def render_header(
    title: str = "AI Knowledge Assistant",
    subtitle: Optional[str] = "Chat with your documents using AI (RAG-powered)",
    show_status: bool = True,
    badge_text: Optional[str] = None,
    *args,
    **kwargs
) -> None:
    """Render top navbar matching the exact reference UI layout without boxing cards."""
    st.markdown(
        f"""
        <div class="top-header-clean">
            <div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em; line-height: 1.2;">
                    {title}
                </div>
                <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px; font-weight: 400;">
                    {subtitle or ''}
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 16px;">
                <div class="status-pill-healthy">
                    <span style="font-size: 0.85rem;">✔</span> System Healthy
                </div>
                <div class="status-label">
                    <span class="status-dot-green"></span>
                    Backend Online
                </div>
                <div class="status-label">
                    <span class="status-dot-green"></span>
                    Frontend Online
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


__all__ = ["render_header"]
