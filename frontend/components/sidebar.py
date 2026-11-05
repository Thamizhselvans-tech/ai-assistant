"""Sidebar navigation, user profile badge, and backend connectivity indicator."""

import streamlit as st
from frontend.api_client import api_client
from frontend.auth import get_current_user, is_admin, logout
from frontend.config import APP_TITLE, APP_SUBTITLE


def render_sidebar() -> str:
    """Render the application sidebar and return the selected navigation view."""
    with st.sidebar:
        # Brand Header
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.25rem;">
                <div style="background: linear-gradient(135deg, #10B981 0%, #EC4899 100%); color: white; width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.35rem; box-shadow: 0 4px 12px rgba(236, 72, 153, 0.35);">
                    🧠
                </div>
                <div>
                    <div style="font-weight: 800; font-size: 1.15rem; background: linear-gradient(90deg, #10B981 0%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.01em; display: inline-block;">{APP_TITLE}</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">{APP_SUBTITLE}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Authenticated User Badge
        user = get_current_user()
        username = user.get("username", "User")
        email = user.get("email", "")
        admin_tag = '<span style="background: rgba(245, 158, 11, 0.2); color: #F59E0B; font-size: 0.68rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">ADMIN</span>' if is_admin() else ""

        st.markdown(
            f"""
            <div style="background: #161F30; padding: 12px 14px; border-radius: 10px; margin-bottom: 1.25rem; border: 1px solid #27354A;">
                <div style="font-weight: 600; font-size: 0.9rem; color: #F8FAFC; display: flex; align-items: center;">
                    👤 {username} {admin_tag}
                </div>
                <div style="font-size: 0.75rem; color: #94A3B8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 2px;">
                    {email}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<p style='font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748B; font-weight: 700; margin-bottom: 0.4rem;'>Navigation</p>", unsafe_allow_html=True)

        pages = [
            "📊 Dashboard",
            "📁 Documents",
            "💬 AI Chat",
            "🕒 Chat History",
            "⚙️ Settings"
        ]

        # Only add Admin for administrative accounts
        if is_admin():
            pages.append("🛡️ Admin")

        if "navigation_page" not in st.session_state or st.session_state["navigation_page"] not in pages:
            st.session_state["navigation_page"] = "📊 Dashboard"

        current_idx = pages.index(st.session_state["navigation_page"]) if st.session_state["navigation_page"] in pages else 0
        selected = st.radio(
            "Navigation Menu",
            pages,
            index=current_idx,
            label_visibility="collapsed"
        )
        st.session_state["navigation_page"] = selected

        st.divider()

        # Backend Health Status
        health_info = api_client.health_check()
        if health_info.get("success"):
            st.markdown(
                """
                <div style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: #10B981; margin-bottom: 1rem;">
                    <span style="display: inline-block; width: 8px; height: 8px; background-color: #10B981; border-radius: 50%;"></span>
                    Backend Connected (Healthy)
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: #EF4444; margin-bottom: 1rem;">
                    <span style="display: inline-block; width: 8px; height: 8px; background-color: #EF4444; border-radius: 50%;"></span>
                    Backend Disconnected
                </div>
                """,
                unsafe_allow_html=True
            )

        # Logout Button
        if st.button("🚪 Sign Out", use_container_width=True):
            logout()

        return selected


__all__ = ["render_sidebar"]
