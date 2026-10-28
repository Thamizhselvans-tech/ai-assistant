"""Settings view displaying system parameters and profile information."""

import os
import streamlit as st
from frontend.services.api_client import api_client, BACKEND_URL


def render_settings_view(token: str):
    """Render system settings and configuration details."""
    st.markdown("## ⚙️ Application Settings & Configuration")
    st.markdown("<p style='color: #64748B;'>Inspect active environment configurations, models, and account parameters.</p>", unsafe_allow_html=True)

    tab_profile, tab_system = st.tabs(["👤 User Profile", "🛠️ System Architecture"])

    with tab_profile:
        st.markdown("### Account Details")
        st.write(f"**Username:** `{st.session_state.get('username')}`")
        st.write(f"**Email:** `{st.session_state.get('email')}`")
        st.write(f"**User ID:** `{st.session_state.get('user_id')}`")
        st.success("Your session is secured using HMAC-SHA256 JWT tokens. Data is strictly isolated.")

    with tab_system:
        st.markdown("### Backend & Model Configuration")
        st.markdown(
            f"""
            - **Backend API Base URL:** `{BACKEND_URL}`
            - **Embedding Model:** `Sentence Transformers (all-MiniLM-L6-v2)`
            - **Vector Database:** `ChromaDB Persistent Store (Cosine Distance)`
            - **LLM Engine:** `OpenAI API (gpt-4o-mini / configurable via .env)`
            - **Supported File Types:** `.pdf`, `.docx`, `.txt`
            - **Default Max File Size:** `15 MB`
            """
        )

        st.markdown("### Health Check Diagnostics")
        health = api_client.health_check()
        if health.get("success"):
            st.json(health["data"])
        else:
            st.error(f"Cannot reach backend: {health.get('error')}")
