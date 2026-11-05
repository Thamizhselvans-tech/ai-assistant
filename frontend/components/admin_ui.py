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
                ("ChromaDB Vector Chunks", f"{data.get('total_vector_chunks', 0):,}", "Stored dense vectors", "processing"),
            ]
            render_metrics_cards(metrics)

            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown("<h3 style='color: #0F172A; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.75rem;'>Ingestion Status Breakdown</h3>", unsafe_allow_html=True)
                breakdown = data.get("document_status_breakdown", {})
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; font-size: 0.88rem; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                            <span style="color: #059669; font-weight: 600;">● Completed (Indexed):</span> <strong>{breakdown.get('completed', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                            <span style="color: #2563EB; font-weight: 600;">● Processing:</span> <strong>{breakdown.get('processing', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                            <span style="color: #D97706; font-weight: 600;">● Warnings (e.g. Scanned):</span> <strong>{breakdown.get('warning', 0)}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #DC2626; font-weight: 600;">● Failed:</span> <strong>{breakdown.get('failed', 0)}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown("<h3 style='color: #0F172A; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.75rem;'>Recent System Activity</h3>", unsafe_allow_html=True)
                recent_docs = data.get("recent_documents", [])
                if not recent_docs:
                    st.info("No recent document uploads.")
                else:
                    for d in recent_docs[:4]:
                        user_str = d.get("username") or f"User #{d.get('user_id')}"
                        st.markdown(
                            f"""
                            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px; margin-bottom: 6px; font-size: 0.82rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                                <span>📄 <strong>{d.get('filename')}</strong> <span style='color: #64748B;'>by {user_str}</span></span>
                                <span style="color: #94A3B8;">{d.get('created_at', '')[:10]}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        else:
            st.error(f"Failed to load admin dashboard: {dash_res.get('error')}")

    with tab_users:
        st.markdown("<h3 style='color: #0F172A; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.75rem;'>System Users Directory</h3>", unsafe_allow_html=True)
        with st.spinner("Fetching registered users..."):
            users_res = api_client.get_admin_users(token, skip=0, limit=100)

        if users_res.get("success"):
            users_data = users_res["data"].get("users", [])
            st.markdown(f"<p style='color: #64748B; font-size: 0.85rem;'>Total users: {len(users_data)}</p>", unsafe_allow_html=True)
            for u in users_data:
                admin_label = '<span class="badge-completed">ADMIN</span>' if u.get("is_admin") else '<span class="badge-processing">USER</span>'
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div>
                            <span style="font-weight: 600; color: #0F172A;">👤 {u.get('username')}</span>
                            <span style="color: #64748B; font-size: 0.82rem; margin-left: 12px;">{u.get('email')}</span>
                        </div>
                        {admin_label}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.error(f"Failed to fetch users: {users_res.get('error')}")

    with tab_docs:
        st.markdown("<h3 style='color: #0F172A; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.75rem;'>System Documents Audit</h3>", unsafe_allow_html=True)
        with st.spinner("Fetching all documents..."):
            docs_res = api_client.get_admin_documents(token, skip=0, limit=100)

        if docs_res.get("success"):
            docs_data = docs_res["data"].get("documents", [])
            st.markdown(f"<p style='color: #64748B; font-size: 0.85rem;'>Total indexed documents: {len(docs_data)}</p>", unsafe_allow_html=True)
            for d in docs_data:
                status_val = d.get('status', 'completed')
                badge_class = f"badge-{status_val}"
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div>
                            <span style="font-weight: 600; color: #0F172A;">📄 {d.get('filename')}</span>
                            <span style="color: #64748B; font-size: 0.82rem; margin-left: 12px;">{d.get('chunk_count', 0)} chunks • {d.get('file_type', '').upper()}</span>
                        </div>
                        <span class="{badge_class}">{status_val.upper()}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.error(f"Failed to fetch system documents: {docs_res.get('error')}")

    with tab_health:
        st.markdown("<h3 style='color: #0F172A; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.75rem;'>ChromaDB & Pipeline Health</h3>", unsafe_allow_html=True)
        with st.spinner("Pinging backend health..."):
            h_res = api_client.health_check()
        if h_res.get("success"):
            st.success("✅ ChromaDB and FastAPI systems are operational.")
            st.json(h_res.get("data", {}))
        else:
            st.error(f"❌ Backend health error: {h_res.get('error')}")


__all__ = ["render_admin_view"]
