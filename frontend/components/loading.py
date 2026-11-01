"""Loading spinners and visual skeleton states."""

from contextlib import contextmanager
import streamlit as st


@contextmanager
def render_loading(message: str = "Processing request..."):
    """Context manager rendering a loading spinner with custom styling."""
    with st.spinner(message):
        yield


def render_skeleton_card():
    """Render a skeleton placeholder card during data loading."""
    st.markdown(
        """
        <div style="background: #161F30; border: 1px solid #27354A; border-radius: 10px; padding: 18px; margin-bottom: 12px; opacity: 0.6;">
            <div style="height: 16px; background: #27354A; border-radius: 4px; width: 40%; margin-bottom: 10px;"></div>
            <div style="height: 12px; background: #1E293B; border-radius: 4px; width: 70%;"></div>
        </div>
        """,
        unsafe_allow_html=True
    )


__all__ = ["render_loading", "render_skeleton_card"]
