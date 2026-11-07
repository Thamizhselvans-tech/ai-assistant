"""Settings view displaying user profile, theme toggles, cloud LLM providers, and low-RAM hardware diagnostics."""

import streamlit as st
from frontend.api_client import api_client
from frontend.auth import get_current_user
from frontend.config import BACKEND_API_URL, MAX_UPLOAD_SIZE_MB, SUPPORTED_FILE_TYPES
from frontend.components.header import render_header


def render_settings_view(token: str):
    """Render system settings, cloud LLM provider configuration, and low-RAM hardware inspection."""
    render_header()

    st.markdown("<h2 style='font-size: 1.5rem; font-weight: 600; color: #0D0D0D; margin-bottom: 0.5rem;'>Settings & Account</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8E8E8E; font-size: 0.9rem; margin-bottom: 1.5rem;'>Manage account profile, cloud LLM providers, and 4GB low-RAM hardware optimization.</p>", unsafe_allow_html=True)

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
            st.text_input("Username", value=user.get("username", ""), disabled=True)
            st.text_input("Email Address", value=user.get("email", ""), disabled=True)
        with col_u2:
            st.text_input("Role", value=user.get("role", "user").upper(), disabled=True)
            st.text_input("Account Created", value=user.get("created_at", "")[:10], disabled=True)

    with tab_providers:
        st.markdown("### ☁️ Cloud LLM Provider Layer (0MB Local LLM RAM)")
        st.info(
            "💡 **Low-RAM Architecture:** On 4GB RAM laptops, running a heavy 7B/8B LLM locally causes system freeze. "
            "Our platform offloads text generation to cloud APIs while keeping vector embeddings (`all-MiniLM-L6-v2` ~90MB) "
            "and ChromaDB 100% local on your machine."
        )

        prov_col1, prov_col2 = st.columns(2)
        with prov_col1:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 10px; padding: 14px; font-size: 0.85rem; line-height: 1.7;">
                    <strong>1. OpenAI</strong><br>
                    • Models: <code>gpt-4o-mini</code>, <code>gpt-4o</code><br>
                    • Key in <code>.env</code>: <code>OPENAI_API_KEY</code><br><br>
                    <strong>2. Groq (Recommended for Speed & Free Tier)</strong><br>
                    • Models: <code>llama-3.1-8b-instant</code>, <code>mixtral-8x7b-32768</code><br>
                    • Key in <code>.env</code>: <code>GROQ_API_KEY</code><br><br>
                    <strong>3. Google Gemini (OpenAI Endpoint)</strong><br>
                    • Models: <code>gemini-1.5-flash</code><br>
                    • Key in <code>.env</code>: <code>GEMINI_API_KEY</code>
                </div>
                """,
                unsafe_allow_html=True
            )
        with prov_col2:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 10px; padding: 14px; font-size: 0.85rem; line-height: 1.7;">
                    <strong>4. OpenRouter (Free & Open Source Models)</strong><br>
                    • Models: <code>meta-llama/llama-3.1-8b-instruct:free</code><br>
                    • Key in <code>.env</code>: <code>OPENROUTER_API_KEY</code><br><br>
                    <strong>5. DeepSeek</strong><br>
                    • Models: <code>deepseek-chat</code><br>
                    • Key in <code>.env</code>: <code>DEEPSEEK_API_KEY</code><br><br>
                    <strong>6. Custom / Local Endpoint (e.g. Ollama)</strong><br>
                    • URL: <code>CUSTOM_LLM_BASE_URL=http://127.0.0.1:11434/v1</code><br>
                    • Lightweight model: <code>qwen2.5:0.5b</code> (Only ~400MB RAM)
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            """
            <div style="margin-top: 15px; padding: 10px 14px; background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; font-size: 0.85rem;">
                <strong>To switch providers:</strong> Simply set <code>LLM_PROVIDER=groq</code> or <code>LLM_PROVIDER=openai</code> in your <code>.env</code> file. No code or RAG changes are required!
            </div>
            """,
            unsafe_allow_html=True
        )

    with tab_rag:
        st.info("ℹ️ Pipeline parameters are configured in the backend environment.")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 10px; padding: 14px; font-size: 0.85rem; line-height: 1.8;">
                    <strong>Embedding Model:</strong> <code>all-MiniLM-L6-v2</code> (~90MB RAM)<br>
                    <strong>PyTorch Threading:</strong> Capped at 2 threads (avoids memory bloat)<br>
                    <strong>Embedding Batch Size:</strong> 16 chunks per batch<br>
                    <strong>Vector DB:</strong> ChromaDB (Local persistent)
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_r2:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 10px; padding: 14px; font-size: 0.85rem; line-height: 1.8;">
                    <strong>Languages Supported:</strong> Tamil, Tanglish, English<br>
                    <strong>Fallback Strategy:</strong> Verified Grounded Citations (Direct RAG)<br>
                    <strong>Similarity Threshold:</strong> 0.20 (synthesis fallback: 0.15)<br>
                    <strong>Max Upload Size:</strong> {MAX_UPLOAD_SIZE_MB} MB ({', '.join(SUPPORTED_FILE_TYPES).upper()})
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_diagnostics:
        st.write(f"**Connected API Base URL:** `{BACKEND_API_URL}`")
        with st.spinner("Pinging backend health & hardware telemetry..."):
            health = api_client.health_check()

        if health.get("success"):
            data = health.get("data", {})
            services = data.get("services", {})
            ram = services.get("ram", {})

            st.success("FastAPI Backend & Low-RAM Pipeline are operational.")

            c_ram1, c_ram2, c_ram3 = st.columns(3)
            with c_ram1:
                st.metric("System RAM Used", f"{ram.get('percent', 0)}%")
            with c_ram2:
                st.metric("Available RAM", f"{ram.get('available_gb', 0)} GB")
            with c_ram3:
                st.metric("Total RAM", f"{ram.get('total_gb', 0)} GB")

            st.markdown("#### Detailed Diagnostic Payload")
            st.json(data)
        else:
            st.error(f"Backend unreachable: {health.get('error')}")


__all__ = ["render_settings_view"]
