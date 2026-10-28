"""Sidebar navigation and status indicator component."""

import streamlit as st
from frontend.services.api_client import api_client


def render_sidebar() -> str:
    """Render the application sidebar and return the selected navigation page."""
    with st.sidebar:
        # Brand Header
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.5rem;">
                <div style="background: #2563EB; color: white; width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;">
                    AI
                </div>
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: #1E293B;">KnowledgeHub</div>
                    <div style="font-size: 0.75rem; color: #64748B;">AI Knowledge Assistant</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Authenticated User Badge
        username = st.session_state.get("username", "User")
        email = st.session_state.get("email", "")
        st.markdown(
            f"""
            <div style="background: #F1F5F9; padding: 10px 14px; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid #E2E8F0;">
                <div style="font-weight: 600; font-size: 0.88rem; color: #0F172A;">👤 {username}</div>
                <div style="font-size: 0.75rem; color: #64748B; overflow: hidden; text-overflow: ellipsis;">{email}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<p style='font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94A3B8; font-weight: 600; margin-bottom: 0.5rem;'>Navigation</p>", unsafe_allow_html=True)

        pages = [
            "💬 AI Chat",
            "📁 Documents",
            "📊 Dashboard",
            "🕒 Chat History",
            "⚙️ Settings"
        ]

        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "💬 AI Chat"

        selected = st.radio(
            "Go to",
            pages,
            index=pages.index(st.session_state["current_page"]) if st.session_state["current_page"] in pages else 0,
            label_visibility="collapsed"
        )
        st.session_state["current_page"] = selected

        st.divider()

        # System Health Check
        health = api_client.health_check()
        if health.get("success"):
            status_text = "🟢 System Healthy"
            status_color = "#16A34A"
        else:
            status_text = "🔴 Backend Offline"
            status_color = "#DC2626"

        st.markdown(
            f"""
            <div style="font-size: 0.8rem; color: {status_color}; font-weight: 600; margin-bottom: 1rem;">
                {status_text}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Logout button
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in ["token", "user_id", "username", "email", "active_conversation_id", "messages"]:
                st.session_state.pop(key, None)
            st.rerun()

    return selected
