"""Top navigation header matching the Dark Emerald UI design with Tamil greeting and language selector."""

from typing import Optional
import streamlit as st
from frontend.auth import get_current_user
from frontend.api_client import api_client


def render_header(
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    *args,
    **kwargs
) -> None:
    """Render top bar matching the screenshot with Tamil greeting and controls."""
    user = get_current_user()
    raw_name = user.get("full_name") or user.get("username") or "Thamizhselvan"
    # Format display name nicely
    if raw_name.lower() in ["admin", "user", "test"]:
        display_name = "Thamizhselvan"
    else:
        display_name = raw_name.capitalize()

    # Query health/provider status
    health_res = api_client.health_check()
    provider_pill = "Gemini 2.5"
    if health_res.get("success"):
        services = health_res.get("data", {}).get("services", {})
        prov_name = services.get("llm_provider_display") or services.get("llm_provider", "Gemini")
        model_name = services.get("llm_model", "gemini-2.5-flash-lite")
        provider_pill = f"{prov_name} • {model_name.replace('gemini-', '')}"

    st.markdown(
        f"""
        <div class="top-navbar-container">
            <div class="top-navbar-left">
                <div class="top-greeting-title">
                    👋 வணக்கம், {display_name}! 👋
                </div>
                <div class="top-greeting-subtitle">
                    Your AI-powered document assistant
                </div>
            </div>
            <div class="top-navbar-right">
                <div class="top-pill-language" title="Language: Automatic detection for Tamil, Tanglish, and English">
                    <span>🌐</span>
                    <span>Auto (தமிழ் / English)</span>
                    <span style="font-size: 0.7rem; color: #94A3B8;">▼</span>
                </div>
                <div class="top-icon-badge" title="Notifications">
                    <span>🔔</span>
                    <span class="notification-dot"></span>
                </div>
                <div class="top-icon-badge" title="Provider: {provider_pill}">
                    <span>☀️ 🌙</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


__all__ = ["render_header"]
