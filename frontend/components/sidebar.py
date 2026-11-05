"""ChatGPT-style minimalist sidebar with recent chats, document collections, and user profile."""

from typing import Optional
import streamlit as st
from frontend.auth import get_current_user, is_admin, logout
from frontend.api_client import api_client


def render_sidebar() -> str:
    """Render clean, white, ChatGPT-style sidebar with compact spacing and minimal icons."""
    token = st.session_state.get("token")
    user = get_current_user()
    username = user.get("username", "User")
    email = user.get("email", "user@example.com")
    initials = (username[:2] if len(username) >= 2 else "TS").upper()

    with st.sidebar:
        # 1. Top Section: App Brand, Search & Toggle Icons
        st.markdown(
            """
            <div class="sidebar-chatgpt-header">
                <div class="sidebar-brand-title">
                    <span style="font-size: 1.25rem;">🧠</span> AI Knowledge Assistant
                </div>
                <div class="sidebar-header-icons">
                    <span title="Search">🔍</span>
                    <span title="Collapse sidebar">◨</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. "New chat" button in ChatGPT rounded pill style
        st.markdown('<div class="new-chat-btn-container">', unsafe_allow_html=True)
        if st.button("📝 New chat", key="sidebar_new_chat_btn", use_container_width=True):
            st.session_state["active_conversation_id"] = None
            st.session_state["messages"] = []
            st.session_state["navigation_page"] = "💬 AI Chat"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 3. Core Application Navigation
        pages = [
            "💬 AI Chat",
            "📁 Document Library",
            "📊 Analytics",
            "🕒 Chat History"
        ]
        if is_admin():
            pages.append("🛡️ Admin")

        page_mapping = {
            "🏠 Home": "💬 AI Chat",
            "📊 Dashboard": "💬 AI Chat",
            "💬 AI Chat": "💬 AI Chat",
            "📁 Documents": "📁 Document Library",
            "📁 Document Library": "📁 Document Library",
            "📊 Analytics": "📊 Analytics",
            "🕒 Chat History": "🕒 Chat History",
            "⚙️ Profile & Settings": "⚙️ Profile & Settings",
            "⚙️ Settings": "⚙️ Profile & Settings",
            "🛡️ Admin": "🛡️ Admin"
        }

        current_nav = st.session_state.get("navigation_page", "💬 AI Chat")
        mapped_current = page_mapping.get(current_nav, "💬 AI Chat")
        current_idx = pages.index(mapped_current) if mapped_current in pages else 0

        selected = st.radio(
            "Navigation Menu",
            pages,
            index=current_idx,
            label_visibility="collapsed",
            key="main_nav_radio"
        )
        st.session_state["navigation_page"] = selected

        st.markdown("<div style='height: 10px; border-bottom: 1px solid #ECECEC; margin: 8px 0;'></div>", unsafe_allow_html=True)

        # 4. Recent Chats Section (ChatGPT Style)
        st.markdown("<div class='sidebar-section-title'>RECENT CHATS</div>", unsafe_allow_html=True)

        show_more = st.session_state.get("show_more_history", False)
        limit = 12 if show_more else 5

        convs_res = api_client.list_conversations(token, skip=0, limit=limit) if token else {"success": False}
        recent_convs = convs_res.get("data", {}).get("conversations", []) if convs_res.get("success") else []
        total_convs = convs_res.get("data", {}).get("total", len(recent_convs)) if convs_res.get("success") else 0
        active_cid = st.session_state.get("active_conversation_id")

        if not recent_convs:
            st.markdown("<div style='font-size: 0.8rem; color: #8E8E8E; padding: 4px 8px;'>No chats yet</div>", unsafe_allow_html=True)
        else:
            for c in recent_convs:
                cid = c.get("id")
                c_title = c.get("title", "Conversation")
                truncated = (c_title[:24] + "...") if len(c_title) > 24 else c_title
                is_active = (cid == active_cid)
                active_cls = "active" if is_active else ""

                # Render item button in minimalist ChatGPT style
                btn_label = f"💬 {truncated}"
                if st.button(btn_label, key=f"nav_conv_{cid}", use_container_width=True):
                    st.session_state["active_conversation_id"] = cid
                    st.session_state["messages"] = []
                    st.session_state["navigation_page"] = "💬 AI Chat"
                    st.rerun()

            if total_convs > 5:
                toggle_label = "Show less" if show_more else "Show more"
                if st.button(toggle_label, key="toggle_show_more_btn", use_container_width=True):
                    st.session_state["show_more_history"] = not show_more
                    st.rerun()

        # 5. Projects & Document Collections Section
        st.markdown("<div class='sidebar-section-title'>PROJECTS & COLLECTIONS</div>", unsafe_allow_html=True)

        docs_res = api_client.list_documents(token) if token else {"success": False}
        user_docs = docs_res.get("data", {}).get("documents", []) if docs_res.get("success") else []

        if not user_docs:
            st.markdown("<div style='font-size: 0.8rem; color: #8E8E8E; padding: 4px 8px;'>No document collections</div>", unsafe_allow_html=True)
        else:
            for d in user_docs[:4]:
                doc_id = d.get("id")
                doc_name = d.get("filename", "Document")
                trunc_doc = (doc_name[:22] + "...") if len(doc_name) > 22 else doc_name
                if st.button(f"📁 {trunc_doc}", key=f"sidebar_doc_{doc_id}", use_container_width=True):
                    st.session_state["filter_doc_ids"] = [doc_id]
                    st.session_state["active_conversation_id"] = None
                    st.session_state["messages"] = []
                    st.session_state["navigation_page"] = "💬 AI Chat"
                    st.rerun()

        # Spacer
        st.markdown("<div style='min-height: 40px; height: 6vh;'></div>", unsafe_allow_html=True)

        # 6. Bottom User Profile Card (ChatGPT Style)
        st.markdown(
            f"""
            <div class="sidebar-profile-card">
                <div class="sidebar-profile-avatar">
                    {initials}
                </div>
                <div style="flex-grow: 1; overflow: hidden;">
                    <div class="sidebar-profile-name">{username}</div>
                    <div class="sidebar-profile-sub">Account • RAG Pro</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_set, col_log = st.columns(2)
        with col_set:
            if st.button("⚙️ Settings", key="sidebar_settings_btn", use_container_width=True):
                st.session_state["navigation_page"] = "⚙️ Profile & Settings"
                st.rerun()
        with col_log:
            if st.button("🚪 Logout", key="sidebar_logout_btn", use_container_width=True):
                logout()

        return selected


__all__ = ["render_sidebar"]
