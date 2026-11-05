"""Minimalist top navigation header matching ChatGPT clean interface."""

from typing import Optional
import streamlit as st


def render_header(
    title: str = "AI Knowledge Assistant",
    subtitle: Optional[str] = None,
    show_status: bool = True,
    badge_text: Optional[str] = None,
    *args,
    **kwargs
) -> None:
    """Render a minimal top bar without large boxes or colorful cards."""
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0 16px 0; border-bottom: 1px solid #F4F4F4; margin-bottom: 1.5rem;">
            <div style="font-size: 1.05rem; font-weight: 600; color: #0D0D0D; display: flex; align-items: center; gap: 8px;">
                <span>🧠</span> AI Knowledge Assistant <span style="font-size: 0.75rem; color: #8E8E8E; font-weight: 400; background: #F4F4F4; padding: 2px 8px; border-radius: 12px;">RAG 2.0</span>
            </div>
            <div style="display: flex; align-items: center; gap: 14px; font-size: 0.8rem; color: #5D5D5D;">
                <div style="display: inline-flex; align-items: center; gap: 6px;">
                    <span style="width: 7px; height: 7px; background-color: #10A37F; border-radius: 50%; display: inline-block;"></span>
                    Online
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


__all__ = ["render_header"]
