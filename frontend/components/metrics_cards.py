"""Reusable dashboard metrics cards component."""

from typing import List, Tuple
import streamlit as st


def render_metrics_cards(metrics: List[Tuple[str, str, str, str]]) -> None:
    """
    Render a responsive row of SaaS metric cards.
    Each item is a tuple: (title, value, badge_text, badge_type).
    badge_type can be 'completed', 'processing', 'warning', 'failed', or 'neutral'.
    """
    cols = st.columns(len(metrics))

    for idx, (title, value, badge_text, badge_type) in enumerate(metrics):
        with cols[idx]:
            badge_class = f"badge-{badge_type}" if badge_type in ["completed", "processing", "warning", "failed"] else "badge-processing"
            st.markdown(
                f"""
                <div class="metric-box">
                    <div>
                        <div class="metric-title">{title}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    {f'<div class="metric-badge {badge_class}">{badge_text}</div>' if badge_text else ''}
                </div>
                """,
                unsafe_allow_html=True
            )


__all__ = ["render_metrics_cards"]
