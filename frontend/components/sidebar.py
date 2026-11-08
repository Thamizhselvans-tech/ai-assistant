"""Emerald Dark UI Sidebar with Glowing Active Pill, Navigation, and Profile Card."""

import base64
from pathlib import Path
from typing import Optional
import streamlit as st
from frontend.auth import get_current_user, is_admin, logout
from frontend.api_client import api_client


def render_sidebar() -> str:
    """Render dark emerald glassmorphic sidebar matching the reference UI."""
    token = st.session_state.get("token")
    user = get_current_user()
    username = user.get("username", "Thamizhselvan")
    full_name = user.get("full_name") or ("S. Thamizhselvan" if username.lower() in ["admin", "user", "test"] else username)
    role = "Student" if not is_admin() else "Admin / Student"
    initials = "".join([part[0].upper() for part in full_name.split() if part])[:2] or "ST"

    with st.sidebar:
        # 1. Top Brand Logo
        st.markdown(
            """
            <div class="sidebar-brand-header">
                <span class="sidebar-logo-icon">🧠</span>
                <span class="sidebar-logo-text">AI Knowledge Assistant</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. "New Chat" Action Button
        st.markdown('<div class="sidebar-newchat-btn">', unsafe_allow_html=True)
        if st.button("➕ New Chat", key="sidebar_new_chat_btn", use_container_width=True):
            st.session_state["active_conversation_id"] = None
            st.session_state["messages"] = []
            st.session_state["navigation_page"] = "💬 Chat Assistant"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # 3. Core Application Navigation Items (Matching screenshot exactly)
        pages = [
            "💬 Chat Assistant",
            "📁 My Documents",
            "📖 Knowledge Base",
            "🕒 History",
            "📊 Analytics",
            "⚙️ Settings",
        ]
        if is_admin():
            pages.append("🛡️ Admin")

        # Map previous labels to new labels for smooth backwards compatibility
        nav_remap = {
            "💬 AI Chat": "💬 Chat Assistant",
            "🏠 Home": "💬 Chat Assistant",
            "📊 Dashboard": "💬 Chat Assistant",
            "📁 Document Library": "📁 My Documents",
            "📁 Documents": "📁 My Documents",
            "🕒 Chat History": "🕒 History",
            "⚙️ Profile & Settings": "⚙️ Settings",
        }

        current_nav = st.session_state.get("navigation_page", "💬 Chat Assistant")
        remapped_current = nav_remap.get(current_nav, current_nav)
        if remapped_current not in pages:
            remapped_current = "💬 Chat Assistant"

        current_idx = pages.index(remapped_current)

        selected = st.radio(
            "Navigation Menu",
            pages,
            index=current_idx,
            label_visibility="collapsed",
            key="main_nav_emerald_radio"
        )
        st.session_state["navigation_page"] = selected

        # Spacer to push profile card to bottom
        st.markdown("<div style='min-height: 80px; height: 18vh;'></div>", unsafe_allow_html=True)

        # 4. User Profile Card & Logout (Matching reference footer)
        avatar_html = f"<div class=\"sidebar-profile-avatar\">{initials}</div>"
        assets_dir = Path(__file__).parent.parent / "assets"
        avatar_path = assets_dir / "user_avatar.png"
        if avatar_path.exists():
            try:
                av_b64 = base64.b64encode(avatar_path.read_bytes()).decode("utf-8")
                avatar_html = f"<div class=\"sidebar-profile-avatar\" style=\"padding:0; overflow:hidden; border: 1.5px solid #00F298;\"><img src=\"data:image/png;base64,{av_b64}\" style=\"width:100%; height:100%; object-fit:cover; border-radius:50%; display:block;\" alt=\"User Avatar\" /></div>"
            except Exception:
                pass

        st.markdown(
            f"""
            <div class="sidebar-profile-card">
                {avatar_html}
                <div style="flex-grow: 1; overflow: hidden;">
                    <div class="sidebar-profile-name">{full_name}</div>
                    <div class="sidebar-profile-role">{role}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        col_out1, col_out2 = st.columns([1, 1])
        with col_out1:
            if st.button("🚪 Logout", key="sidebar_logout_btn", use_container_width=True):
                logout()
                st.rerun()
        with col_out2:
            if st.button("⚙️ Config", key="sidebar_quick_cfg_btn", use_container_width=True):
                st.session_state["navigation_page"] = "⚙️ Settings"
                st.rerun()

    return selected


__all__ = ["render_sidebar"]
