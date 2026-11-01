"""Dashboard overview component showing knowledge base metrics, status breakdown, and recent activity."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.metrics_cards import render_metrics_cards
from frontend.components.document_card import format_file_size


def render_dashboard_view(token: str):
    """Render overall metrics, status cards, and recent activity."""
    render_header(
        title="Knowledge Base Dashboard",
        subtitle="Real-time metrics, document ingestion telemetry, and activity overview.",
        badge_text="LIVE TELEMETRY"
    )

    # 1. Fetch live data from backend APIs
    with st.spinner("Fetching system metrics..."):
        docs_res = api_client.list_documents(token)
        convs_res = api_client.list_conversations(token, skip=0, limit=5)
        health_res = api_client.health_check()

    docs = docs_res.get("data", {}).get("documents", []) if docs_res.get("success") else []
    convs_data = convs_res.get("data", {}) if convs_res.get("success") else {}
    convs = convs_data.get("conversations", [])
    total_convs = convs_data.get("total", len(convs))

    total_docs = len(docs)
    total_pages = sum(d.get("page_count", 0) for d in docs)
    total_chunks = sum(d.get("chunk_count", 0) for d in docs)

    # Calculate status counts
    completed_count = sum(1 for d in docs if d.get("status") == "completed")
    warning_count = sum(1 for d in docs if d.get("status") == "warning")
    failed_count = sum(1 for d in docs if d.get("status") == "failed")
    processing_count = sum(1 for d in docs if d.get("status") == "processing")

    # 2. Render Top Metric Cards
    metrics = [
        ("Indexed Documents", str(total_docs), f"{completed_count} active", "completed"),
        ("Pages Extracted", str(total_pages), "Page-level provenance", "processing"),
        ("Vector Chunks", str(total_chunks), "Cosine ChromaDB", "processing"),
        ("Conversations", str(total_convs), "Persistent chat threads", "completed"),
    ]
    render_metrics_cards(metrics)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 3. Two-column layout for Activity and System Telemetry
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 📄 Recent Documents")
        if not docs:
            st.info("No documents uploaded yet. Go to **Documents** to upload your first PDF, DOCX, or TXT file.")
        else:
            for d in docs[:5]:
                fname = d.get("filename")
                ftype = d.get("file_type", "").upper()
                fsize = format_file_size(d.get("file_size_bytes", 0))
                chunks = d.get("chunk_count", 0)
                status_val = d.get("status", "completed")
                badge_color = "#10B981" if status_val == "completed" else "#F59E0B" if status_val == "warning" else "#EF4444"

                st.markdown(
                    f"""
                    <div style="background: #161F30; border: 1px solid #27354A; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; font-size: 0.88rem; color: #F8FAFC;">{fname}</div>
                            <div style="font-size: 0.75rem; color: #94A3B8;">{ftype} • {fsize} • {chunks} chunks</div>
                        </div>
                        <span style="background: rgba(16, 185, 129, 0.15); color: {badge_color}; border: 1px solid {badge_color}; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 4px;">
                            {status_val.upper()}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        st.markdown("### 💬 Recent Conversations")
        if not convs:
            st.info("No conversations started yet. Navigate to **AI Chat** to ask your first question.")
        else:
            for c in convs[:5]:
                cid = c.get("id")
                title = c.get("title", "Conversation")
                updated_at = c.get("updated_at", "")[:10]
                st.markdown(
                    f"""
                    <div style="background: #161F30; border: 1px solid #27354A; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: 500; font-size: 0.88rem; color: #CBD5E1;">💬 {title}</div>
                        <div style="font-size: 0.75rem; color: #64748B;">{updated_at}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with col_right:
        st.markdown("### ⚙️ Quick Actions")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Upload Doc", use_container_width=True, type="primary"):
                st.session_state["navigation_page"] = "📁 Documents"
                st.rerun()
        with c2:
            if st.button("💬 Ask Questions", use_container_width=True):
                st.session_state["navigation_page"] = "💬 AI Chat"
                st.rerun()

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        st.markdown("### 🛡️ System & Vector Storage Health")
        if health_res.get("success"):
            hdata = health_res.get("data", {})
            services = hdata.get("services", {})
            db_status = services.get("database", "unknown")
            vs_status = services.get("vector_store", "unknown")
            emb_model = services.get("embedding_model", "unknown")
            llm_model = services.get("llm_model", "unknown")

            st.markdown(
                f"""
                <div style="background: #161F30; border: 1px solid #27354A; border-radius: 10px; padding: 14px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #10B981; font-size: 0.9rem; margin-bottom: 8px;">
                        <span style="width: 8px; height: 8px; background: #10B981; border-radius: 50%;"></span>
                        All Services Operational
                    </div>
                    <div style="font-size: 0.8rem; color: #CBD5E1; line-height: 1.6;">
                        <strong>SQLite Database:</strong> <span style="color: #10B981;">{db_status}</span><br>
                        <strong>ChromaDB Vectors:</strong> <span style="color: #10B981;">{vs_status}</span><br>
                        <strong>Embeddings:</strong> <code>{emb_model}</code> (384-dim)<br>
                        <strong>AI Answer Model:</strong> <code>{llm_model}</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.error("Cannot connect to FastAPI backend server. Ensure backend is running.")

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        st.markdown("### 📊 Document Ingestion Status")
        st.markdown(
            f"""
            <div style="background: #161F30; border: 1px solid #27354A; border-radius: 10px; padding: 14px; font-size: 0.82rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #10B981;">Completed (Indexed):</span> <strong>{completed_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #3B82F6;">Processing:</span> <strong>{processing_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="color: #F59E0B;">Warnings (e.g. Scanned):</span> <strong>{warning_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #EF4444;">Failed:</span> <strong>{failed_count}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


__all__ = ["render_dashboard_view"]
