"""Minimalist top navigation header with dynamic LLM provider and Low-RAM telemetry."""

from typing import Optional
import streamlit as st
from frontend.api_client import api_client


def render_header(
    title: str = "AI Knowledge Assistant",
    subtitle: Optional[str] = None,
    show_status: bool = True,
    badge_text: Optional[str] = None,
    *args,
    **kwargs
) -> None:
    """Render a minimal top bar displaying active provider, model, and low-RAM status."""
    # Query health status once per session/render with fast cache
    health_res = api_client.health_check()
    provider_pill = "⚡ OpenAI (gpt-4o-mini)"
    ram_text = "4GB Mode"
    status_color = "#10A37F"  # green
    status_label = "Online"

    if health_res.get("success"):
        services = health_res.get("data", {}).get("services", {})
        prov_name = services.get("llm_provider_display") or services.get("llm_provider", "OpenAI")
        model_name = services.get("llm_model", "gpt-4o-mini")
        is_configured = services.get("llm_configured", True)

        ram_data = services.get("ram", {})
        avail_gb = ram_data.get("available_gb")
        if avail_gb is not None:
            ram_text = f"RAM: {avail_gb}GB Free"
        else:
            ram_text = "4GB Low-RAM"

        if not is_configured:
            status_color = "#E2A336"  # amber
            status_label = "Unconfigured"
            provider_pill = f"⚠️ {prov_name} (Direct RAG Fallback)"
        else:
            provider_pill = f"⚡ {prov_name} ({model_name})"
    else:
        status_color = "#E05252"
        status_label = "Backend Offline"
        provider_pill = "Offline"

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0 16px 0; border-bottom: 1px solid #ECECEC; margin-bottom: 1.5rem;">
            <div style="font-size: 1.05rem; font-weight: 600; color: #0D0D0D; display: flex; align-items: center; gap: 8px;">
                <span>🧠</span> AI Knowledge Assistant 
                <span style="font-size: 0.75rem; color: #4F46E5; font-weight: 500; background: #EEF2FF; padding: 2px 8px; border-radius: 12px; border: 1px solid #E0E7FF;">
                    {ram_text}
                </span>
            </div>
            <div style="display: flex; align-items: center; gap: 12px; font-size: 0.8rem; color: #5D5D5D;">
                <span style="background: #F4F4F4; border: 1px solid #E5E5E5; color: #374151; padding: 3px 10px; border-radius: 14px; font-weight: 500;">
                    {provider_pill}
                </span>
                <div style="display: inline-flex; align-items: center; gap: 6px; font-weight: 500;">
                    <span style="width: 7px; height: 7px; background-color: {status_color}; border-radius: 50%; display: inline-block;"></span>
                    {status_label}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


__all__ = ["render_header"]
