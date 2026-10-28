"""Dashboard overview component showing knowledge base metrics and quick actions."""

import streamlit as st
from frontend.services.api_client import api_client


def render_dashboard_view(token: str):
    """Render overall metrics and status cards."""
    st.markdown("## 📊 Knowledge Base Dashboard")
    st.markdown("<p style='color: #64748B;'>High-level overview of your documents, indexing health, and recent activity.</p>", unsafe_allow_html=True)

    # Fetch data
    docs_res = api_client.list_documents(token)
    convs_res = api_client.list_conversations(token)
    health_res = api_client.health_check()

    docs = docs_res.get("data", {}).get("documents", []) if docs_res.get("success") else []
    convs = convs_res.get("data", {}).get("conversations", []) if convs_res.get("success") else []

    total_docs = len(docs)
    total_pages = sum(d.get("page_count", 0) for d in docs)
    total_chunks = sum(d.get("chunk_count", 0) for d in docs)
    total_convs = len(convs)

    # Top Metric KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Indexed Documents</div>
                <div style="font-size: 2rem; font-weight: 700; color: #1E293B; margin-top: 0.25rem;">{total_docs}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Pages Processed</div>
                <div style="font-size: 2rem; font-weight: 700; color: #2563EB; margin-top: 0.25rem;">{total_pages}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Vector Chunks</div>
                <div style="font-size: 2rem; font-weight: 700; color: #7C3AED; margin-top: 0.25rem;">{total_chunks}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Conversations</div>
                <div style="font-size: 2rem; font-weight: 700; color: #059669; margin-top: 0.25rem;">{total_convs}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # Quick action row
    c_act1, c_act2 = st.columns(2)

    with c_act1:
        st.markdown("### 🚀 Quick Actions")
        if st.button("📁 Upload a Document", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "📁 Documents"
            st.rerun()

        if st.button("💬 Start Asking Questions", use_container_width=True):
            st.session_state["current_page"] = "💬 AI Chat"
            st.rerun()

    with c_act2:
        st.markdown("### 🛡️ System & Vector Storage Status")
        if health_res.get("success"):
            data = health_res.get("data", {})
            srv = data.get("services", {})
            st.success(f"**Backend Service:** Connected ({data.get('app_name')} v{data.get('version')})")
            st.info(f"**Database:** {srv.get('database')} • **Vector Store:** {srv.get('vector_store')}")
            st.caption(f"Embedding Model: `{srv.get('embedding_model')}` • LLM Model: `{srv.get('llm_model')}`")
        else:
            st.error("FastAPI Backend service is not reachable at the configured URL.")
