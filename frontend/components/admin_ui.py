"""Admin dashboard UI component for privileged system administration and telemetry."""

import streamlit as st
from frontend.api_client import api_client
from frontend.auth import is_admin
from frontend.components.header import render_header
from frontend.components.metrics_cards import render_metrics_cards
from frontend.components.document_card import format_file_size


def render_admin_view(token: str):
    """Render administrative management view guarded by RBAC."""
    if not is_admin():
        st.error("🛡️ **Access Denied**: You do not have permission to view the administrative panel.")
        st.stop()
        return

    render_header(
        title="Admin Control Center",
        subtitle="System oversight, user directory, document audit, and infrastructure health monitoring.",
        badge_text="ROOT ACCESS"
    )

    tab_dash, tab_users, tab_docs, tab_health = st.tabs([
        "📊 System Dashboard",
        "👥 User Directory",
        "📑 System Documents Audit",
        "🩺 Infrastructure Health"
    ])

    with tab_dash:
        with st.spinner("Fetching system metrics..."):
            dash_res = api_client.get_admin_dashboard(token)

        if dash_res.get("success"):
            data = dash_res["data"]
            metrics = [
                ("Total Registered Users", str(data.get("total_users", 0)), "Registered accounts", "completed"),
                ("Total Documents (All Users)", str(data.get("total_documents", 0)), "System-wide", "processing"),
                ("Total Conversations", str(data.get("total_conversations", 0)), "Chat threads", "completed"),
                ("ChromaDB Vector Chunks", str(data.get("total_vector_chunks", 0)), "Stored dense vectors", "processing"),
            ]
            render_metrics_cards(metrics)

            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Ingestion Status Breakdown")
                breakdown = data.get("document_status_breakdown", {})
                st.markdown(
                    f"""
                    <div style="background: #161F30; border: 1px solid #27354A; border-radius: 10px; padding: 14px; font-size: 0.88rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #10B981;">● Completed (Indexed):</span> <strong>{breakdown.get('completed', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #3B82F6;">● Processing:</span> <strong>{breakdown.get('processing', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #F59E0B;">● Warnings (e.g. Scanned):</span> <strong>{breakdown.get('warning', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #EF4444;">● Failed:</span> <strong>{breakdown.get('failed', 0)}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown("### Recent System Activity")
                recent_docs = data.get("recent_documents", [])
                if not recent_docs:
                    st.info("No recent document uploads.")
                else:
                    for d in recent_docs[:4]:
                        user_str = d.get("username") or f"User #{d.get('user_id')}"
                        st.markdown(
                            f"""
                            <div style="background: #161F30; border: 1px solid #27354A; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; font-size: 0.82rem; display: flex; justify-content: space-between;">
                                <span>📄 <strong>{d.get('filename')}</strong> (by {user_str})</span>
                                <span style="color: #94A3B8;">{d.get('created_at', '')[:10]}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        else:
            st.error(f"Failed to load admin dashboard: {dash_res.get('error')}")

    with tab_users:
        st.markdown("### System Users Directory")
        with st.spinner("Fetching registered users..."):
            users_res = api_client.get_admin_users(token, skip=0, limit=100)

        if users_res.get("success"):
            users_data = users_res["data"].get("users", [])
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.85rem;'>Total users: {len(users_data)}</p>", unsafe_allow_html=True)
            for u in users_data:
                admin_label = '<span style="background: rgba(245, 158, 11, 0.2); color: #F59E0B; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">ADMIN</span>' if u.get("is_admin") else '<span style="background: rgba(100, 116, 139, 0.2); color: #94A3B8; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem;">USER</span>'
                st.markdown(
                    f"""
                    <div style="background: #161F30; border: 1px solid #27354A; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #F8FAFC; font-size: 0.9rem;">
                                {u.get('username')} {admin_label}
                            </div>
                            <div style="font-size: 0.78rem; color: #94A3B8;">
                                {u.get('email')} • Registered: {u.get('created_at', '')[:10]}
                            </div>
                        </div>
                        <div style="text-align: right; font-size: 0.78rem; color: #94A3B8;">
                            <strong>{u.get('document_count', 0)}</strong> docs • <strong>{u.get('conversation_count', 0)}</strong> chats
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.error(f"Error: {users_res.get('error')}")

    with tab_docs:
        st.markdown("### System Documents Audit")
        with st.spinner("Fetching document audit list..."):
            docs_res = api_client.get_admin_documents(token, skip=0, limit=100)

        if docs_res.get("success"):
            all_docs = docs_res["data"].get("documents", [])
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.85rem;'>Total documents audited: {len(all_docs)}</p>", unsafe_allow_html=True)
            for d in all_docs:
                owner = d.get("username") or f"User #{d.get('user_id')}"
                st.markdown(
                    f"""
                    <div style="background: #161F30; border: 1px solid #27354A; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-weight: 600; font-size: 0.9rem; color: #F8FAFC;">
                                📄 {d.get('filename')}
                            </div>
                            <span style="font-size: 0.75rem; color: #10B981; font-weight: 600;">{d.get('status', '').upper()}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">
                            Owner: <strong>{owner}</strong> • {format_file_size(d.get('file_size_bytes', 0))} • {d.get('page_count', 0)} pages • {d.get('chunk_count', 0)} chunks • {d.get('created_at', '')[:10]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.error(f"Error: {docs_res.get('error')}")

    with tab_health:
        st.markdown("### Infrastructure Health & Diagnostics")
        with st.spinner("Auditing system health..."):
            health_res = api_client.get_admin_system_health(token)

        if health_res.get("success"):
            h = health_res["data"]
            st.markdown(
                f"""
                <div style="background: #161F30; border: 1px solid #27354A; border-radius: 10px; padding: 16px; margin-bottom: 12px;">
                    <div style="font-weight: 700; color: #10B981; font-size: 1rem; margin-bottom: 12px;">
                        Overall Status: {h.get('overall_status', '').upper()}
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; font-size: 0.85rem; color: #CBD5E1;">
                        <div>
                            <strong>Database (SQLite):</strong><br>
                            Status: <span style="color: #10B981;">{h.get('database', {}).get('status')}</span><br>
                            URL: <code>{h.get('database', {}).get('database_url')}</code>
                        </div>
                        <div>
                            <strong>Vector Store (ChromaDB):</strong><br>
                            Status: <span style="color: #10B981;">{h.get('vector_store', {}).get('status')}</span><br>
                            Total Vector Chunks: <strong>{h.get('vector_store', {}).get('total_chunks')}</strong><br>
                            Collection: <code>{h.get('vector_store', {}).get('collection_name')}</code>
                        </div>
                        <div>
                            <strong>Embedding Engine:</strong><br>
                            Model: <code>{h.get('embedding_engine', {}).get('model_name')}</code><br>
                            Dimension: <strong>{h.get('embedding_engine', {}).get('dimension')}</strong> (Normalized)
                        </div>
                        <div>
                            <strong>LLM Service:</strong><br>
                            Status: <strong>{h.get('llm_service', {}).get('status').upper()}</strong><br>
                            Model: <code>{h.get('llm_service', {}).get('model')}</code><br>
                            API Key Set: <strong>{h.get('llm_service', {}).get('api_key_configured')}</strong>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.error(f"Error: {health_res.get('error')}")


__all__ = ["render_admin_view"]
