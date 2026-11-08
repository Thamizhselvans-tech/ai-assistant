"""Settings view displaying user profile, theme toggles, cloud LLM providers, and low-RAM hardware diagnostics."""

import streamlit as st
from frontend.api_client import api_client
from frontend.auth import get_current_user
from frontend.config import BACKEND_API_URL, MAX_UPLOAD_SIZE_MB, SUPPORTED_FILE_TYPES
from frontend.components.header import render_header


def render_settings_view(token: str):
    """Render system settings, cloud LLM provider configuration, and low-RAM hardware inspection."""
    render_header()

    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.8rem;">⚙️</span> Settings & Hardware
            </div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">
                Configure AI generation providers, multi-lingual RAG settings, and 4GB low-RAM system diagnostics.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_profile, tab_providers, tab_rag, tab_diagnostics = st.tabs([
        "👤 Profile", 
        "⚡ Cloud LLM Providers", 
        "⚙️ RAG Configuration", 
        "🩺 4GB Hardware & Diagnostics"
    ])

    user = get_current_user()

    with tab_profile:
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.text_input("Username", value=user.get("username", "Thamizhselvan"), disabled=True)
            st.text_input("Email Address", value=user.get("email", "thamizhselvan@example.com"), disabled=True)
        with col_u2:
            st.text_input("Role", value=user.get("role", "Student").upper(), disabled=True)
            st.text_input("Account Created", value=user.get("created_at", "")[:10] or "Active", disabled=True)

    with tab_providers:
        st.markdown("<h4 style='color: #00F298;'>⚡ Configured Generation Provider Layer</h4>", unsafe_allow_html=True)
        st.info(
            "💡 **Low-RAM Architecture:** On 4GB RAM laptops, running a heavy 7B/8B LLM locally causes system freeze. "
            "Our platform offloads text generation to cloud APIs (Google Gemini Free Tier / OpenAI) while keeping vector embeddings (`all-MiniLM-L6-v2` ~90MB) "
            "and ChromaDB 100% local on your machine."
        )

        prov_col1, prov_col2 = st.columns(2)
        with prov_col1:
            st.markdown(
                """
                <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 12px; padding: 16px; font-size: 0.85rem; line-height: 1.7; color: #CBD5E1;">
                    <strong style="color: #00F298;">1. Google Gemini (Active Free Tier)</strong><br>
                    • Model: <code>gemini-2.5-flash-lite</code><br>
                    • Key in <code>backend/.env</code>: <code>GEMINI_API_KEY</code><br>
                    • Features: 1M context, high speed, natural Tamil/Tanglish support<br><br>
                    <strong style="color: #00F298;">2. OpenAI (Optional)</strong><br>
                    • Models: <code>gpt-4o-mini</code>, <code>gpt-4o</code><br>
                    • Key in <code>backend/.env</code>: <code>OPENAI_API_KEY</code>
                </div>
                """,
                unsafe_allow_html=True
            )
        with prov_col2:
            st.markdown(
                """
                <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 12px; padding: 16px; font-size: 0.85rem; line-height: 1.7; color: #CBD5E1;">
                    <strong style="color: #00F298;">3. Multilingual Detection Engine</strong><br>
                    • Languages: Tamil (தமிழ்), Tanglish, English<br>
                    • Automatic same-language responses<br>
                    • Rule-based particle classifier + LLM grounding<br><br>
                    <strong style="color: #00F298;">4. Fallback Architecture</strong><br>
                    • Direct synthesized RAG fallback if cloud quota is exhausted
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_rag:
        st.markdown("<h4 style='color: #00F298;'>⚙️ RAG Vector Retrieval Parameters</h4>", unsafe_allow_html=True)
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            st.markdown(
                f"""
                <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 12px; padding: 16px; font-size: 0.88rem; color: #CBD5E1;">
                    <div>• <strong>Embedding Model:</strong> <code>all-MiniLM-L6-v2</code> (~90MB RAM)</div>
                    <div style="margin-top: 6px;">• <strong>Vector DB:</strong> ChromaDB (Local Persistent)</div>
                    <div style="margin-top: 6px;">• <strong>Chunk Size:</strong> 500 characters (100 char overlap)</div>
                    <div style="margin-top: 6px;">• <strong>Max Upload Size:</strong> {MAX_UPLOAD_SIZE_MB}MB</div>
                    <div style="margin-top: 6px;">• <strong>Supported Extensions:</strong> {', '.join(SUPPORTED_FILE_TYPES).upper()}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with rcol2:
            st.markdown(
                """
                <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 12px; padding: 16px; font-size: 0.88rem; color: #CBD5E1;">
                    <div>• <strong>RAG Isolation:</strong> Per-user metadata filtering</div>
                    <div style="margin-top: 6px;">• <strong>Anti-Hallucination:</strong> Strict confidence checks</div>
                    <div style="margin-top: 6px;">• <strong>Default Top K:</strong> 4 chunks</div>
                    <div style="margin-top: 6px;">• <strong>Default Threshold:</strong> 0.15</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_diagnostics:
        st.markdown("<h4 style='color: #00F298;'>🩺 Live Backend Health & RAM Diagnostics</h4>", unsafe_allow_html=True)
        with st.spinner("Querying backend system diagnostics..."):
            health = api_client.health_check()

        if health.get("success"):
            data = health.get("data", {})
            serv = data.get("services", {})
            ram = serv.get("ram", {})

            d1, d2, d3 = st.columns(3)
            with d1:
                st.metric("Total RAM", f"{ram.get('total_gb', 4.0):.1f} GB")
            with d2:
                st.metric("Available RAM", f"{ram.get('available_gb', 2.0):.1f} GB")
            with d3:
                st.metric("RAM Used", f"{ram.get('percent_used', 50)}%")

            st.json(data)
        else:
            st.error(f"Cannot connect to backend: {health.get('error')}")


__all__ = ["render_settings_view"]
