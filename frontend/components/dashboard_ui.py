"""Dashboard overview component showing knowledge base metrics, status breakdown, and recent activity."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.metrics_cards import render_metrics_cards
from frontend.components.document_card import format_file_size


def render_dashboard_view(token: str):
    """Render overall metrics, status cards, and recent activity matching minimalist layout."""
    render_header()

    st.markdown("<h2 style='font-size: 1.5rem; font-weight: 600; color: #0D0D0D; margin-bottom: 0.5rem;'>System Overview & Telemetry</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8E8E8E; font-size: 0.9rem; margin-bottom: 1.5rem;'>Live statistics across document ingestion, vector storage, and query activity.</p>", unsafe_allow_html=True)

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
        ("Pages Extracted", str(total_pages), "Page-level", "processing"),
        ("Vector Chunks", f"{total_chunks:,}", "ChromaDB", "processing"),
        ("Conversations", str(total_convs), "Chat threads", "completed"),
    ]
    render_metrics_cards(metrics)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 3. Two-column layout for Activity and System Telemetry
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown("<div style='font-weight: 600; font-size: 1.05rem; color: #0D0D0D; margin-bottom: 0.75rem;'>Recent Documents</div>", unsafe_allow_html=True)
        if not docs:
            st.info("No documents uploaded yet.")
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
                    <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 500; font-size: 0.88rem; color: #0D0D0D;">{fname}</div>
                            <div style="font-size: 0.75rem; color: #8E8E8E; margin-top: 2px;">{ftype} • {fsize} • {chunks} chunks</div>
                        </div>
                        <span class="{badge_class}">
                            {status_val.upper()}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with col_right:
        st.markdown("<div style='font-weight: 600; font-size: 1.05rem; color: #0D0D0D; margin-bottom: 0.75rem;'>Ingestion Breakdown</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 10px; padding: 14px 18px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.86rem;">
                    <span style="color: #166534; font-weight: 500;">● Completed:</span>
                    <strong style="color: #0D0D0D;">{completed_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.86rem;">
                    <span style="color: #075985; font-weight: 500;">● Processing:</span>
                    <strong style="color: #0D0D0D;">{processing_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.86rem;">
                    <span style="color: #92400E; font-weight: 500;">● Warnings:</span>
                    <strong style="color: #0D0D0D;">{warning_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.86rem;">
                    <span style="color: #991B1B; font-weight: 500;">● Failed:</span>
                    <strong style="color: #0D0D0D;">{failed_count}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


__all__ = ["render_dashboard_view"]
