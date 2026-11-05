"""Settings view displaying user profile, theme toggles, and RAG configuration parameters."""

import streamlit as st
from frontend.api_client import api_client
from frontend.auth import get_current_user
from frontend.config import BACKEND_API_URL, MAX_UPLOAD_SIZE_MB, SUPPORTED_FILE_TYPES
from frontend.components.header import render_header


def render_settings_view(token: str):
    """Render system settings, theme options, and configuration inspection."""
    render_header(
        title="Profile & Settings",
        subtitle="Review account profile, theme preferences, and backend RAG pipeline configurations.",
        badge_text="CONFIG"
    )

    tab_profile, tab_rag, tab_diagnostics = st.tabs(["👤 Profile & Preferences", "⚙️ RAG Configuration", "🩺 Diagnostics"])

    user = get_current_user()

    with tab_profile:
        st.markdown("<h3 style='color: #0F172A; font-weight: 700; margin-bottom: 1rem;'>User Profile</h3>", unsafe_allow_html=True)
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.text_input("Username", value=user.get("username", ""), disabled=True)
            st.text_input("Email Address", value=user.get("email", ""), disabled=True)
        with col_u2:
            st.text_input("Role", value=user.get("role", "user").upper(), disabled=True)
            st.text_input("Account Created", value=user.get("created_at", "")[:10], disabled=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #0F172A; font-weight: 700; margin-bottom: 0.5rem;'>Interface Theme</h3>", unsafe_allow_html=True)
        st.caption("The application is configured to the modern SaaS Enterprise light theme.")

    with tab_rag:
        st.markdown("<h3 style='color: #0F172A; font-weight: 700; margin-bottom: 1rem;'>RAG Pipeline Parameters</h3>", unsafe_allow_html=True)
        st.info("ℹ️ Pipeline parameters are configured in the backend environment. Below are the active client and server parameters.")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; font-size: 0.88rem; line-height: 1.8; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong>Embedding Model:</strong> <code>sentence-transformers/all-MiniLM-L6-v2</code><br>
                    <strong>Vector Dimensionality:</strong> 384 dimensions (Normalized)<br>
                    <strong>Vector Index Metric:</strong> Cosine Similarity (<code>hnsw:space: cosine</code>)<br>
                    <strong>Persistent Vector DB:</strong> ChromaDB (Local persistent storage)
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_r2:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; font-size: 0.88rem; line-height: 1.8; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong>Default Chunk Size:</strong> 800 - 1000 characters<br>
                    <strong>Default Chunk Overlap:</strong> 150 - 200 characters<br>
                    <strong>Similarity Threshold:</strong> 0.20 (adaptive fallback: 0.15)<br>
                    <strong>Max Upload Size:</strong> {MAX_UPLOAD_SIZE_MB} MB ({', '.join(SUPPORTED_FILE_TYPES).upper()})
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_diagnostics:
        st.markdown("<h3 style='color: #0F172A; font-weight: 700; margin-bottom: 1rem;'>Live Backend Telemetry</h3>", unsafe_allow_html=True)
        st.write(f"**Connected API Base URL:** `{BACKEND_API_URL}`")

        with st.spinner("Pinging backend health..."):
            health = api_client.health_check()

        if health.get("success"):
            st.success("✅ FastAPI Backend is operational and responsive.")
            st.json(health.get("data", {}))
        else:
            st.error(f"❌ Backend unreachable: {health.get('error')}")


__all__ = ["render_settings_view"]
