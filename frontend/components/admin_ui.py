"""Admin dashboard UI component for privileged system administration in Dark Emerald theme."""

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

    render_header()

    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.8rem;">🛡️</span> Admin Control Center
            </div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">
                System oversight, user directory, document audit, and infrastructure telemetry.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_dash, tab_users, tab_docs, tab_health = st.tabs([
        "📊 Dashboard",
        "👥 Users",
        "📑 Documents Audit",
        "🩺 Infrastructure"
    ])

    with tab_dash:
        with st.spinner("Fetching system metrics..."):
            dash_res = api_client.get_admin_dashboard(token)

        if dash_res.get("success"):
            data = dash_res["data"]
            metrics = [
                ("Total Users", str(data.get("total_users", 0)), "Registered", "completed"),
                ("Total Documents", str(data.get("total_documents", 0)), "System-wide", "processing"),
                ("Conversations", str(data.get("total_conversations", 0)), "Threads", "completed"),
                ("ChromaDB Vectors", f"{data.get('total_vector_chunks', 0):,}", "Stored chunks", "processing"),
            ]
            render_metrics_cards(metrics)

            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #FFFFFF; margin-bottom: 0.5rem;'>Status Breakdown</div>", unsafe_allow_html=True)
                breakdown = data.get("document_status_breakdown", {})
                st.markdown(
                    f"""
                    <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 12px; padding: 16px; font-size: 0.88rem; color: #CBD5E1;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #00F298; font-weight: 600;">● Completed:</span> <strong style="color: #FFFFFF;">{breakdown.get('completed', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #38BDF8; font-weight: 600;">● Processing:</span> <strong style="color: #FFFFFF;">{breakdown.get('processing', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #FBBF24; font-weight: 600;">● Warnings:</span> <strong style="color: #FFFFFF;">{breakdown.get('warning', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #F87171; font-weight: 600;">● Failed:</span> <strong style="color: #FFFFFF;">{breakdown.get('failed', 0)}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #FFFFFF; margin-bottom: 0.5rem;'>System Health Snapshot</div>", unsafe_allow_html=True)
                health = data.get("health", {})
                ram = health.get("ram", {})
                st.markdown(
                    f"""
                    <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 12px; padding: 16px; font-size: 0.88rem; color: #CBD5E1;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Overall Status:</span> <strong style="color: #00F298;">{health.get('status', 'healthy').upper()}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Database:</span> <strong style="color: #00F298;">{health.get('database', 'connected').upper()}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Available RAM:</span> <strong style="color: #FFFFFF;">{ram.get('available_gb', 2.0)} GB</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Memory Used:</span> <strong style="color: #FFFFFF;">{ram.get('percent_used', 50)}%</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab_users:
        st.markdown("<div style='font-weight: 600; font-size: 1rem; color: #FFFFFF; margin-bottom: 0.75rem;'>Registered User Directory</div>", unsafe_allow_html=True)
        with st.spinner("Loading users..."):
            users_res = api_client.get_admin_users(token)
        if users_res.get("success"):
            users_list = users_res["data"].get("users", [])
            for u in users_list:
                st.markdown(
                    f"""
                    <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.15); border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #FFFFFF;">{u.get('username')}</strong> ({u.get('email')})
                            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 2px;">
                                Role: <span style="color: #00F298;">{u.get('role', 'user').upper()}</span> • Docs: {u.get('document_count', 0)}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab_docs:
        st.markdown("<div style='font-weight: 600; font-size: 1rem; color: #FFFFFF; margin-bottom: 0.75rem;'>Document Audit Log</div>", unsafe_allow_html=True)
        with st.spinner("Loading audit..."):
            audit_res = api_client.get_admin_documents(token)
        if audit_res.get("success"):
            audit_docs = audit_res["data"].get("documents", [])
            for d in audit_docs[:10]:
                st.markdown(
                    f"""
                    <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.15); border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between;">
                        <div>
                            <strong style="color: #FFFFFF;">{d.get('filename')}</strong>
                            <div style="font-size: 0.75rem; color: #94A3B8;">User: {d.get('user_id')} • {d.get('chunk_count', 0)} chunks • {d.get('status', 'completed').upper()}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab_health:
        st.markdown("<div style='font-weight: 600; font-size: 1rem; color: #FFFFFF; margin-bottom: 0.75rem;'>Infrastructure Status</div>", unsafe_allow_html=True)
        h = api_client.health_check()
        st.json(h.get("data", {}))


__all__ = ["render_admin_view"]
