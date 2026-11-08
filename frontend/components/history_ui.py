"""Dark Emerald UI Chat History & Conversation Browser."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.citation_viewer import render_citation_viewer


def render_history_view(token: str):
    """Render conversation history list with Dark Emerald styling."""
    render_header()

    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.8rem;">🕒</span> Chat History
            </div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">
                Review, resume, and manage your past conversational sessions across Tamil, Tanglish, and English.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if "history_page" not in st.session_state:
        st.session_state["history_page"] = 0

    page_size = 10
    skip = st.session_state["history_page"] * page_size

    with st.spinner("Loading conversation history..."):
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
            <div style="background: rgba(11, 20, 15, 0.7); border: 1px dashed rgba(0, 242, 152, 0.3); border-radius: 16px; padding: 3rem 2rem; text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem; filter: drop-shadow(0 0 10px #00F298);">💬</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF;">No conversations yet</div>
                <div style="color: #94A3B8; font-size: 0.88rem; margin-top: 6px;">
                    Start asking questions in **Chat Assistant** to build your conversation history.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    st.markdown(f"<p style='color: #00F298; font-size: 0.82rem; font-weight: 600; margin-bottom: 1rem;'>● Total: {total_convs} threads (Page {st.session_state['history_page'] + 1})</p>", unsafe_allow_html=True)

    for conv in conversations:
        cid = conv.get("id")
        title = conv.get("title", "Conversation")
        created_at = conv.get("created_at", "")[:19].replace("T", " ")

        with st.container():
            col1, col2, col3 = st.columns([5, 1.2, 1.2])

            with col1:
                st.markdown(
                    f"""
                    <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 12px; padding: 12px 16px; margin-bottom: 6px; backdrop-filter: blur(10px);">
                        <div style="font-weight: 600; font-size: 0.95rem; color: #FFFFFF;">💬 {title}</div>
                        <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">
                            {created_at} • ID: <code style="color: #00F298;">{cid[:8]}...</code>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                if st.button("Resume", key=f"resume_conv_{cid}", use_container_width=True, type="primary"):
                    st.session_state["active_conversation_id"] = cid
                    st.session_state["messages"] = []
                    st.session_state["navigation_page"] = "💬 Chat Assistant"
                    st.rerun()

            with col3:
                if st.button("Delete", key=f"del_conv_{cid}", use_container_width=True):
                    with st.spinner("Deleting thread..."):
                        del_res = api_client.delete_conversation(cid, token)
                        if del_res.get("success"):
                            st.success("Deleted.")
                            st.rerun()
                        else:
                            st.error(f"Error: {del_res.get('error')}")

            # Preview expander
            with st.expander(f"Preview messages in '{title[:30]}'", expanded=False):
                with st.spinner("Loading messages..."):
                    hres = api_client.get_conversation_history(cid, token)
                    if hres.get("success"):
                        msgs = hres["data"].get("messages", [])
                        for m in msgs:
                            r = m.get("role")
                            c = m.get("content", "")
                            if r == "user":
                                st.markdown(f"**You:** {c}")
                            else:
                                st.markdown(f"**Assistant:** {c}")
                                scs = m.get("sources") or m.get("citations") or []
                                if scs:
                                    render_citation_viewer(scs)
                            st.divider()

    # Pagination controls
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    cprev, cpage, cnext = st.columns([1, 4, 1])
    with cprev:
        if st.session_state["history_page"] > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state["history_page"] -= 1
                st.rerun()
    with cpage:
        max_pages = max(1, (total_convs + page_size - 1) // page_size)
        st.markdown(f"<p style='text-align: center; color: #94A3B8; font-size: 0.85rem;'>Page {st.session_state['history_page'] + 1} of {max_pages}</p>", unsafe_allow_html=True)
    with cnext:
        if (st.session_state["history_page"] + 1) * page_size < total_convs:
            if st.button("Next →", use_container_width=True):
                st.session_state["history_page"] += 1
                st.rerun()


__all__ = ["render_history_view"]
