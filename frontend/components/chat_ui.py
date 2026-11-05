"""ChatGPT-style conversational interface with centered 'Ready when you are.' home view."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.citation_viewer import render_citation_viewer


def format_chat_time(dt_val: Optional[Any] = None) -> str:
    """Format timestamp into readable string."""
    now = datetime.now()
    if not dt_val:
        return now.strftime("%I:%M %p")
    try:
        if isinstance(dt_val, str):
            clean_str = dt_val.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(clean_str)
            return parsed.strftime("%I:%M %p")
        elif isinstance(dt_val, datetime):
            return dt_val.strftime("%I:%M %p")
    except Exception:
        pass
    return now.strftime("%I:%M %p")


def render_chat_view(token: str):
    """Render ChatGPT-style minimalist conversational interface."""
    # 1. Minimal Top Header
    render_header()

    # 2. Fetch User Documents
    docs_res = api_client.list_documents(token)
    user_docs = docs_res.get("data", {}).get("documents", []) if docs_res.get("success") else []
    doc_options = {
        d["id"]: f"{d.get('original_filename', d.get('filename'))} ({d.get('page_count', 0)} pgs)"
        for d in user_docs if d.get("status") in ["completed", "warning"]
    }

    active_conv_id = st.session_state.get("active_conversation_id")

    # Initialize messages state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Load active conversation if messages are empty and an active conversation is set
    if active_conv_id and not st.session_state["messages"]:
        with st.spinner("Loading conversation..."):
            hist_res = api_client.get_conversation_history(active_conv_id, token)
            if hist_res.get("success"):
                raw_messages = hist_res["data"].get("messages", [])
                st.session_state["messages"] = [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "sources": m.get("sources") or m.get("citations") or [],
                        "time": format_chat_time(m.get("created_at"))
                    }
                    for m in raw_messages
                ]

    # Scope & Search Settings Expander (Minimal)
    with st.expander("⚙️ Scope & Search Settings", expanded=False):
        c1, c2 = st.columns([3, 1])
        with c1:
            default_selected = st.session_state.get("filter_doc_ids", [])
            valid_defaults = [d for d in default_selected if d in doc_options]
            selected_doc_ids = st.multiselect(
                "Filter Documents:",
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options.get(x, x),
                default=valid_defaults,
                key="chat_scope_filter"
            )
        with c2:
            sim_threshold = st.slider("Match Threshold", 0.0, 0.5, 0.15, 0.05)

    has_messages = bool(st.session_state["messages"])
    action_prompt: Optional[str] = None

    # =========================================================================
    # STATE A: Welcome / Home Screen ("Ready when you are.")
    # =========================================================================
    if not has_messages:
        st.markdown(
            """
            <div class="chatgpt-home-wrapper">
                <div class="chatgpt-home-heading">Ready when you are.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Quick Actions Centered below Heading (matching ChatGPT screenshot)
        col_pad1, col_center, col_pad2 = st.columns([1, 4, 1])
        with col_center:
            if st.button("📄  Ask your documents", key="qa_act_ask", use_container_width=True):
                action_prompt = "What are the primary objectives and key findings in the documents?"

            if st.button("✏️  Summarize a document", key="qa_act_summarize", use_container_width=True):
                action_prompt = "Summarize the key objectives and main findings from the uploaded document."

            if st.button("🔍  Search uploaded documents", key="qa_act_search", use_container_width=True):
                action_prompt = "What topics and methodologies are covered across my uploaded documents?"

    # =========================================================================
    # STATE B: Active Conversation Stream (ChatGPT Style)
    # =========================================================================
    else:
        st.markdown('<div class="chatgpt-thread-container">', unsafe_allow_html=True)

        for msg in st.session_state["messages"]:
            role = msg["role"]
            content = msg["content"]
            sources = msg.get("sources") or msg.get("citations") or []

            if role == "user":
                st.markdown(
                    f"""
                    <div class="chatgpt-user-msg-row">
                        <div class="chatgpt-user-bubble">
                            {content}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="chatgpt-ai-msg-row">
                        <div class="chatgpt-ai-avatar">🧠</div>
                        <div class="chatgpt-ai-body">
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(content)
                if sources:
                    render_citation_viewer(sources)
                st.markdown(
                    """
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # Bottom ChatGPT Capsule Composer
    # =========================================================================
    default_prompt = st.session_state.pop("prompt_input", None) or action_prompt
    user_input = st.chat_input("Ask anything about your documents...", key="chatgpt_user_input") or default_prompt

    if user_input:
        user_time = format_chat_time()
        st.session_state["messages"].append({
            "role": "user",
            "content": user_input,
            "sources": [],
            "time": user_time
        })

        doc_filter_arg = selected_doc_ids if 'selected_doc_ids' in locals() and selected_doc_ids else None
        active_sim = sim_threshold if 'sim_threshold' in locals() else 0.15

        with st.spinner("Thinking..."):
            res = api_client.ask_question(
                question=user_input,
                token=token,
                conversation_id=active_conv_id,
                document_ids=doc_filter_arg,
                top_k=4,
                similarity_threshold=active_sim
            )

            if res.get("success"):
                ans_data = res["data"]
                answer = ans_data.get("answer", "")
                citations = ans_data.get("sources") or ans_data.get("citations") or []
                st.session_state["active_conversation_id"] = ans_data.get("conversation_id")

                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": answer,
                    "sources": citations,
                    "time": format_chat_time()
                })
                st.rerun()
            else:
                st.error(f"❌ {res.get('error', 'Error generating response.')}")


__all__ = ["render_chat_view"]
