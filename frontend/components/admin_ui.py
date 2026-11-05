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

    render_header()

    st.markdown("<h2 style='font-size: 1.5rem; font-weight: 600; color: #0D0D0D; margin-bottom: 0.5rem;'>Admin Control Center</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8E8E8E; font-size: 0.9rem; margin-bottom: 1.5rem;'>System oversight, user directory, document audit, and infrastructure health monitoring.</p>", unsafe_allow_html=True)

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
                st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #0D0D0D; margin-bottom: 0.5rem;'>Status Breakdown</div>", unsafe_allow_html=True)
                breakdown = data.get("document_status_breakdown", {})
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 10px; padding: 14px; font-size: 0.85rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #166534; font-weight: 500;">● Completed:</span> <strong>{breakdown.get('completed', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #075985; font-weight: 500;">● Processing:</span> <strong>{breakdown.get('processing', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #92400E; font-weight: 500;">● Warnings:</span> <strong>{breakdown.get('warning', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #991B1B; font-weight: 500;">● Failed:</span> <strong>{breakdown.get('failed', 0)}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #0D0D0D; margin-bottom: 0.5rem;'>Recent System Uploads</div>", unsafe_allow_html=True)
                recent_docs = data.get("recent_documents", [])
                if not recent_docs:
                    st.info("No recent uploads.")
                else:
                    for d in recent_docs[:4]:
                        user_str = d.get("username") or f"User #{d.get('user_id')}"
                        st.markdown(
                            f"""
                            <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 8px; padding: 8px 12px; margin-bottom: 4px; font-size: 0.8rem; display: flex; justify-content: space-between;">
                                <span>📄 <strong>{d.get('filename')}</strong> <span style='color: #8E8E8E;'>({user_str})</span></span>
                                <span style="color: #8E8E8E;">{d.get('created_at', '')[:10]}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        else:
            st.error(f"Failed to load admin dashboard: {dash_res.get('error')}")

    with tab_users:
        with st.spinner("Fetching users..."):
            users_res = api_client.get_admin_users(token, skip=0, limit=100)

        if users_res.get("success"):
            users_data = users_res["data"].get("users", [])
            for u in users_data:
                admin_label = '<span class="badge-completed">ADMIN</span>' if u.get("is_admin") else '<span class="badge-processing">USER</span>'
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 8px; padding: 10px 14px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-weight: 500; color: #0D0D0D;">👤 {u.get('username')}</span>
                            <span style="color: #8E8E8E; font-size: 0.8rem; margin-left: 10px;">{u.get('email')}</span>
                        </div>
                        {admin_label}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab_docs:
        with st.spinner("Fetching all documents..."):
            docs_res = api_client.get_admin_documents(token, skip=0, limit=100)

        if docs_res.get("success"):
            docs_data = docs_res["data"].get("documents", [])
            for d in docs_data:
                status_val = d.get('status', 'completed')
                badge_class = f"badge-{status_val}"
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 8px; padding: 10px 14px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-weight: 500; color: #0D0D0D;">📄 {d.get('filename')}</span>
                            <span style="color: #8E8E8E; font-size: 0.8rem; margin-left: 10px;">{d.get('chunk_count', 0)} chunks</span>
                        </div>
                        <span class="{badge_class}">{status_val.upper()}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab_health:
        with st.spinner("Pinging health..."):
            h_res = api_client.health_check()
        if h_res.get("success"):
            st.success("All systems operational.")
            st.json(h_res.get("data", {}))
        else:
            st.error(f"Health error: {h_res.get('error')}")


__all__ = ["render_admin_view"]
