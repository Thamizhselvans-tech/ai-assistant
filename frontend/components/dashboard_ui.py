"""Dashboard overview component showing knowledge base metrics, status breakdown, and recent activity."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.metrics_cards import render_metrics_cards
from frontend.components.document_card import format_file_size


def render_dashboard_view(token: str):
    """Render overall metrics, status cards, and recent activity matching modern SaaS layout."""
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
        ("Vector Chunks", f"{total_chunks:,}", "Cosine ChromaDB", "processing"),
        ("Conversations", str(total_convs), "Persistent chat threads", "completed"),
    ]
    render_metrics_cards(metrics)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 3. Two-column layout for Activity and System Telemetry
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown("<h3 style='font-weight: 700; color: #0F172A; font-size: 1.1rem; margin-bottom: 0.75rem;'>📄 Recent Documents</h3>", unsafe_allow_html=True)
        if not docs:
            st.info("No documents uploaded yet. Go to **Document Library** to upload your first PDF, DOCX, or TXT file.")
        else:
            for d in docs[:5]:
                fname = d.get("filename")
                ftype = d.get("file_type", "").upper()
                fsize = format_file_size(d.get("file_size_bytes", 0))
                chunks = d.get("chunk_count", 0)
                status_val = d.get("status", "completed")
                badge_class = f"badge-{status_val}"

                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                        <div>
                            <div style="font-weight: 600; font-size: 0.9rem; color: #0F172A;">{fname}</div>
                            <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">{ftype} • {fsize} • {chunks} chunks</div>
                        </div>
                        <span class="{badge_class}">
                            {status_val.upper()}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        st.markdown("<h3 style='font-weight: 700; color: #0F172A; font-size: 1.1rem; margin-bottom: 0.75rem;'>💬 Recent Conversations</h3>", unsafe_allow_html=True)
        if not convs:
            st.info("No conversations started yet. Navigate to **AI Chat** to ask your first question.")
        else:
            for c in convs[:5]:
                cid = c.get("id")
                title = c.get("title", "Conversation")
                updated_at = c.get("updated_at", "")[:10]
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                        <div style="font-weight: 600; font-size: 0.88rem; color: #0F172A;">💬 {title}</div>
                        <div style="font-size: 0.78rem; color: #64748B;">{updated_at}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with col_right:
        st.markdown("<h3 style='font-weight: 700; color: #0F172A; font-size: 1.1rem; margin-bottom: 0.75rem;'>⚡ System Ingestion Breakdown</h3>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.88rem;">
                    <span style="color: #059669; font-weight: 600;">● Completed (Indexed):</span>
                    <strong style="color: #0F172A;">{completed_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.88rem;">
                    <span style="color: #2563EB; font-weight: 600;">● In Processing:</span>
                    <strong style="color: #0F172A;">{processing_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.88rem;">
                    <span style="color: #D97706; font-weight: 600;">● Warnings (URL / Scanned):</span>
                    <strong style="color: #0F172A;">{warning_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem;">
                    <span style="color: #DC2626; font-weight: 600;">● Failed Ingestion:</span>
                    <strong style="color: #0F172A;">{failed_count}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-weight: 700; color: #0F172A; font-size: 1.1rem; margin-bottom: 0.75rem;'>🚀 Quick Navigation</h3>", unsafe_allow_html=True)

        if st.button("💬 Open AI Chat Workspace", use_container_width=True, type="primary"):
            st.session_state["navigation_page"] = "💬 AI Chat"
            st.rerun()

        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        if st.button("📁 Manage Document Library", use_container_width=True):
            st.session_state["navigation_page"] = "📁 Document Library"
            st.rerun()


__all__ = ["render_dashboard_view"]
