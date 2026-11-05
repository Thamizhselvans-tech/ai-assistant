"""Sidebar navigation, user profile badge, and logout action."""

from typing import Optional
import streamlit as st
from frontend.auth import get_current_user, is_admin, logout
from frontend.config import APP_TITLE


def render_sidebar() -> str:
    """Render modern dark navy sidebar matching enterprise SaaS UI layout."""
    with st.sidebar:
        # 1. Brand Header
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-top: 0.5rem; margin-bottom: 2rem; padding: 0 4px;">
                <div style="width: 38px; height: 38px; background: #FFFFFF; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.35rem; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                    🤖
                </div>
                <div>
                    <div style="font-weight: 800; font-size: 1.05rem; color: #FFFFFF; letter-spacing: -0.01em; line-height: 1.25;">
                        AI Knowledge<br/>Assistant
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. Navigation Items
        pages = [
            "🏠 Home",
            "💬 AI Chat",
            "📁 Document Library",
            "📊 Analytics",
            "⚙️ Profile & Settings"
        ]

        # Only add Admin for administrative accounts
        if is_admin():
            pages.append("🛡️ Admin")

        # Map internal states to the new display labels
        page_mapping = {
            "📊 Dashboard": "🏠 Home",
            "🏠 Home": "🏠 Home",
            "💬 AI Chat": "💬 AI Chat",
            "📁 Documents": "📁 Document Library",
            "📁 Document Library": "📁 Document Library",
            "🕒 Chat History": "📊 Analytics",
            "📊 Analytics": "📊 Analytics",
            "⚙️ Settings": "⚙️ Profile & Settings",
            "⚙️ Profile & Settings": "⚙️ Profile & Settings",
            "🛡️ Admin": "🛡️ Admin"
        }

        current_nav = st.session_state.get("navigation_page", "💬 AI Chat")
        mapped_current = page_mapping.get(current_nav, "💬 AI Chat")
        current_idx = pages.index(mapped_current) if mapped_current in pages else 1

        selected = st.radio(
            "Navigation Menu",
            pages,
            index=current_idx,
            label_visibility="collapsed",
            key="main_nav_radio"
        )
        st.session_state["navigation_page"] = selected

        # Spacer to push profile card to bottom
        st.markdown("<div style='min-height: 140px; height: 18vh;'></div>", unsafe_allow_html=True)

        # 3. Bottom User Profile Card
        user = get_current_user()
        username = user.get("username", "User")
        email = user.get("email", "user@example.com")
        initials = (username[:2] if len(username) >= 2 else "U").upper()

        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; padding: 12px 10px; border-top: 1px solid #1E293B; margin-top: 1rem;">
                <div style="width: 38px; height: 38px; border-radius: 50%; background: #6366F1; color: #FFFFFF; font-weight: 700; font-size: 0.85rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    {initials}
                </div>
                <div style="overflow: hidden; flex-grow: 1;">
                    <div style="font-weight: 700; font-size: 0.88rem; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {username}
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {email}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Logout button styled with red/coral
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout_btn"):
            logout()

        return selected


__all__ = ["render_sidebar"]
