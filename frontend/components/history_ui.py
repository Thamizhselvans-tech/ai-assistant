"""Chat history browser and conversation manager component."""

import streamlit as st
from frontend.services.api_client import api_client


def render_history_view(token: str):
    """Render conversation history list with open and delete actions."""
    st.markdown("## 🕒 Conversation History")
    st.markdown("<p style='color: #64748B;'>Browse and resume your previous AI chat sessions.</p>", unsafe_allow_html=True)

    res = api_client.list_conversations(token)
    if not res.get("success"):
        st.error(f"Error fetching history: {res.get('error')}")
        return

    conversations = res.get("data", {}).get("conversations", [])

    if not conversations:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 2.5rem; text-align: center;">
                <p style="font-size: 1.5rem; margin-bottom: 0.5rem;">💬 No conversations found</p>
                <p style="color: #64748B; font-size: 0.95rem;">Start asking questions in the AI Chat tab to build your conversation history.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    for conv in conversations:
        with st.container():
            col1, col2, col3 = st.columns([5, 1.5, 1.2])

            with col1:
                st.markdown(f"**💬 {conv['title']}**")
                created_date = conv.get("created_at", "")[:19].replace("T", " ")
                st.caption(f"Created: {created_date} • ID: `{conv['id'][:8]}...`")

            with col2:
                if st.button("📂 Resume", key=f"open_conv_{conv['id']}", use_container_width=True):
                    st.session_state["active_conversation_id"] = conv["id"]
                    st.session_state["messages"] = []  # Triggers fresh reload in chat view
                    st.session_state["current_page"] = "💬 AI Chat"
                    st.rerun()

            with col3:
                if st.button("🗑️ Delete", key=f"del_conv_{conv['id']}", use_container_width=True):
                    del_res = api_client.delete_conversation(conv["id"], token)
                    if del_res.get("success"):
                        if st.session_state.get("active_conversation_id") == conv["id"]:
                            st.session_state["active_conversation_id"] = None
                            st.session_state["messages"] = []
                        st.success("Conversation deleted.")
                        st.rerun()
                    else:
                        st.error(del_res.get("error", "Failed to delete conversation."))

            st.divider()
