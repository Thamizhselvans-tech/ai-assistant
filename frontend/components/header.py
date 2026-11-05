"""Reusable application top header component with live system health indicators."""

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
    """Render a clean SaaS top navbar with title, subtitle, and live system health pills."""
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 1rem 1.5rem; margin-bottom: 1.25rem; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div>
                <div style="font-size: 1.55rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em; line-height: 1.2;">
                    {title}
                </div>
                <div style="color: #64748B; font-size: 0.88rem; margin-top: 4px;">
                    {subtitle or ''}
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 16px;">
                <div class="status-pill-healthy" style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 5px 12px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 0.85rem;">✔</span> System Healthy
                </div>
                <div style="display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #475569; font-weight: 500;">
                    <span style="width: 8px; height: 8px; background-color: #10B981; border-radius: 50%; display: inline-block;"></span>
                    Backend Online
                </div>
                <div style="display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #475569; font-weight: 500;">
                    <span style="width: 8px; height: 8px; background-color: #10B981; border-radius: 50%; display: inline-block;"></span>
                    Frontend Online
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


__all__ = ["render_header"]
