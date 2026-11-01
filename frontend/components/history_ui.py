"""Chat history browser and conversation manager component."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.citation_viewer import render_citation_viewer


def render_history_view(token: str):
    """Render conversation history list with pagination, resume, preview, and delete actions."""
    render_header(
        title="Chat History",
        subtitle="Review, resume, and audit your past conversational QA sessions and citations.",
        badge_text="AUDIT LOG"
    )

    # Pagination state
    if "history_page" not in st.session_state:
        st.session_state["history_page"] = 0

    page_size = 10
    skip = st.session_state["history_page"] * page_size

    with st.spinner("Loading conversation threads..."):
        res = api_client.list_conversations(token, skip=skip, limit=page_size)

    if not res.get("success"):
        st.error(f"Error fetching conversation history: {res.get('error')}")
        return

    data = res.get("data", {})
    conversations = data.get("conversations", [])
    total_convs = data.get("total", len(conversations))

    if not conversations:
        st.markdown(
            """
            <div style="background: #161F30; border: 1px solid #27354A; border-radius: 10px; padding: 2.5rem; text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💬</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #F8FAFC;">No Conversations Found</div>
                <div style="color: #94A3B8; font-size: 0.88rem; margin-top: 4px;">
                    Start asking questions in **AI Chat** to build your conversation history.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    st.markdown(f"<p style='color: #94A3B8; font-size: 0.85rem;'>Total Conversations: <strong>{total_convs}</strong> (Page {st.session_state['history_page'] + 1})</p>", unsafe_allow_html=True)

    for conv in conversations:
        cid = conv.get("id")
        title = conv.get("title", "Conversation")
        created_at = conv.get("created_at", "")[:19].replace("T", " ")

        with st.container():
            col1, col2, col3 = st.columns([5, 1.2, 1.2])

            with col1:
                st.markdown(
                    f"""
                    <div style="background: #161F30; border: 1px solid #27354A; border-radius: 8px; padding: 12px 14px; margin-bottom: 4px;">
                        <div style="font-weight: 600; font-size: 0.95rem; color: #F8FAFC;">💬 {title}</div>
                        <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">
                            Created: {created_at} • ID: <code>{cid[:8]}...</code>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                if st.button("📂 Resume", key=f"resume_conv_{cid}", use_container_width=True, type="primary"):
                    st.session_state["active_conversation_id"] = cid
                    st.session_state["messages"] = []  # Reloads from backend
                    st.session_state["navigation_page"] = "💬 AI Chat"
                    st.rerun()

            with col3:
                if st.button("🗑️ Delete", key=f"del_conv_{cid}", use_container_width=True):
                    del_res = api_client.delete_conversation(cid, token)
                    if del_res.get("success"):
                        if st.session_state.get("active_conversation_id") == cid:
                            st.session_state["active_conversation_id"] = None
                            st.session_state["messages"] = []
                        st.success("Conversation deleted.")
                        st.rerun()
                    else:
                        st.error(del_res.get("error", "Failed to delete conversation."))

            # Message details preview expander
            with st.expander("👁️ Preview Conversation & Citations", expanded=False):
                hist_detail = api_client.get_conversation_history(cid, token)
                if hist_detail.get("success"):
                    msgs = hist_detail.get("data", {}).get("messages", [])
                    if not msgs:
                        st.caption("No messages recorded in this conversation.")
                    for m in msgs:
                        role_icon = "🧑‍💻" if m.get("role") == "user" else "🧠"
                        st.markdown(f"**{role_icon} {m.get('role', '').capitalize()}:** {m.get('content')}")
                        srcs = m.get("sources") or m.get("citations") or []
                        if srcs:
                            render_citation_viewer(srcs, title="Saved Citations")
                else:
                    st.caption("Unable to load preview.")

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    # Pagination controls
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        if st.session_state["history_page"] > 0:
            if st.button("⬅️ Previous Page", use_container_width=True):
                st.session_state["history_page"] -= 1
                st.rerun()
    with p_col3:
        if (st.session_state["history_page"] + 1) * page_size < total_convs:
            if st.button("Next Page ➡️", use_container_width=True):
                st.session_state["history_page"] += 1
                st.rerun()


__all__ = ["render_history_view"]
