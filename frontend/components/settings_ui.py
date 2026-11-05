"""Settings view displaying user profile, theme toggles, and RAG configuration parameters."""

import streamlit as st
from frontend.api_client import api_client
from frontend.auth import get_current_user
from frontend.config import BACKEND_API_URL, MAX_UPLOAD_SIZE_MB, SUPPORTED_FILE_TYPES
from frontend.components.header import render_header


def render_settings_view(token: str):
    """Render system settings, theme options, and configuration inspection."""
    render_header()

    st.markdown("<h2 style='font-size: 1.5rem; font-weight: 600; color: #0D0D0D; margin-bottom: 0.5rem;'>Settings & Account</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8E8E8E; font-size: 0.9rem; margin-bottom: 1.5rem;'>Manage account profile, model parameters, and platform diagnostics.</p>", unsafe_allow_html=True)

    tab_profile, tab_rag, tab_diagnostics = st.tabs(["👤 Profile", "⚙️ RAG Configuration", "🩺 Diagnostics"])

    user = get_current_user()

    with tab_profile:
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.text_input("Username", value=user.get("username", ""), disabled=True)
            st.text_input("Email Address", value=user.get("email", ""), disabled=True)
        with col_u2:
            st.text_input("Role", value=user.get("role", "user").upper(), disabled=True)
            st.text_input("Account Created", value=user.get("created_at", "")[:10], disabled=True)

    with tab_rag:
        st.info("ℹ️ Pipeline parameters are configured in the backend environment.")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 10px; padding: 14px; font-size: 0.85rem; line-height: 1.8;">
                    <strong>Embedding Model:</strong> <code>sentence-transformers/all-MiniLM-L6-v2</code><br>
                    <strong>Vector Dimensionality:</strong> 384 dimensions<br>
                    <strong>Index Metric:</strong> Cosine Similarity<br>
                    <strong>Vector DB:</strong> ChromaDB (Local persistent)
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_r2:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 10px; padding: 14px; font-size: 0.85rem; line-height: 1.8;">
                    <strong>Chunk Size:</strong> 800 - 1000 characters<br>
                    <strong>Chunk Overlap:</strong> 150 - 200 characters<br>
                    <strong>Similarity Threshold:</strong> 0.20 (fallback: 0.15)<br>
                    <strong>Max Upload Size:</strong> {MAX_UPLOAD_SIZE_MB} MB ({', '.join(SUPPORTED_FILE_TYPES).upper()})
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_diagnostics:
        st.write(f"**Connected API Base URL:** `{BACKEND_API_URL}`")
        with st.spinner("Pinging backend health..."):
            health = api_client.health_check()

        if health.get("success"):
            st.success("FastAPI Backend is operational.")
            st.json(health.get("data", {}))
        else:
            st.error(f"Backend unreachable: {health.get('error')}")


__all__ = ["render_settings_view"]
