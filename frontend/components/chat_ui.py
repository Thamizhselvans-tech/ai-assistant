"""Emerald Dark UI ChatGPT-Style Conversational Interface."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st
from frontend.api_client import api_client
from frontend.config import BACKEND_API_URL, MAX_UPLOAD_SIZE_MB
from frontend.components.header import render_header
from frontend.components.dashboard_ui import render_dashboard_view
from frontend.components.citation_viewer import render_citation_viewer
from frontend.components.chat_composer import render_chat_composer


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


def extract_chat_input(raw_input: Any):
    """Extract text prompt and attached files list from chat input return value."""
    if hasattr(raw_input, "text"):
        prompt = (raw_input.text or "").strip()
        files = getattr(raw_input, "files", []) or []
        return prompt, files
    elif isinstance(raw_input, dict):
        prompt = (raw_input.get("text", "") or "").strip()
        files = raw_input.get("files", []) or []
        return prompt, files
    elif isinstance(raw_input, str):
        return raw_input.strip(), []
    return "", []


def render_chat_view(token: str):
    """Render the ChatGPT conversational interface with Dark Emerald SaaS styling."""
    active_conv_id = st.session_state.get("active_conversation_id")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Fetch User Documents for Knowledge Scope Filtering
    docs_res = api_client.list_documents(token) if token else {"success": False}
    user_docs = docs_res.get("data", {}).get("documents", []) if docs_res.get("success") else []
    doc_options = {
        d["id"]: f"{d.get('original_filename', d.get('filename'))} ({d.get('page_count', 0)} pgs)"
        for d in user_docs if d.get("status") in ["completed", "warning"]
    }

    # Load active conversation history from backend if empty in memory
    if active_conv_id and not st.session_state["messages"]:
        with st.spinner("Loading conversation history..."):
            hist_res = api_client.get_conversation_history(active_conv_id, token)
            if hist_res.get("success"):
                raw_messages = hist_res["data"].get("messages", [])
                st.session_state["messages"] = [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "sources": m.get("sources") or m.get("citations") or [],
                        "language": m.get("language", "en"),
                        "time": format_chat_time(m.get("created_at"))
                    }
                    for m in raw_messages
                ]

    has_messages = bool(st.session_state["messages"])
    action_prompt: Optional[str] = st.session_state.pop("prompt_input", None)

    # =========================================================================
    # STATE A: Welcome Screen / Dashboard
    # =========================================================================
    if not has_messages and not action_prompt:
        render_dashboard_view(token)
        return

    # =========================================================================
    # STATE B: Active Conversational Stream
    # =========================================================================
    render_header()

    # Top Control Bar for Chat View
    top_c1, top_c2 = st.columns([6, 1])
    with top_c1:
        st.markdown(
            """
            <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.3rem;">💬</span> Chat Assistant
                <span style="font-size: 0.75rem; color: #00F298; background: rgba(0, 242, 152, 0.15); border: 1px solid rgba(0, 242, 152, 0.3); padding: 2px 8px; border-radius: 12px;">
                    Active Thread
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with top_c2:
        if st.button("➕ New Chat", key="thread_new_chat_btn", use_container_width=True):
            st.session_state["active_conversation_id"] = None
            st.session_state["messages"] = []
            st.rerun()

    # Scope & Similarity Settings Expander
    with st.expander("⚙️ Knowledge Scope & Match Settings", expanded=False):
        c1, c2 = st.columns([3, 1])
        with c1:
            default_selected = st.session_state.get("filter_doc_ids", [])
            valid_defaults = [d for d in default_selected if d in doc_options]
            selected_doc_ids = st.multiselect(
                "Filter Knowledge Scope (leave empty for entire library):",
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options.get(x, x),
                default=valid_defaults,
                key="chat_scope_filter_emerald"
            )
        with c2:
            sim_threshold = st.slider("Match Threshold", 0.0, 0.5, 0.15, 0.05, help="Semantic distance tolerance")

    # If action_prompt was received (e.g. from an action card or "Try asking" pill), process it now
    if action_prompt:
        prompt_text = action_prompt.strip()[:2000]
        if prompt_text:
            st.session_state["messages"].append({
                "role": "user",
                "content": prompt_text,
                "sources": [],
                "time": format_chat_time()
            })

            doc_filter_arg = selected_doc_ids if 'selected_doc_ids' in locals() and selected_doc_ids else None
            active_sim = sim_threshold if 'sim_threshold' in locals() else 0.15

            with st.spinner("AI Assistant is thinking..."):
                res = api_client.ask_question(
                    question=prompt_text,
                    token=token,
                    conversation_id=active_conv_id,
                    document_ids=doc_filter_arg,
                    top_k=4,
                    similarity_threshold=active_sim
                )

                if res.get("success"):
                    ans_data = res["data"]
                    st.session_state["active_conversation_id"] = ans_data.get("conversation_id")
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": ans_data.get("answer", ""),
                        "sources": ans_data.get("sources") or ans_data.get("citations") or [],
                        "language": ans_data.get("language", "en"),
                        "time": format_chat_time()
                    })
                else:
                    err_msg = res.get("error", "Error generating response.")
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": f"❌ **Error generating response**: {err_msg}",
                        "sources": [],
                        "language": "en",
                        "time": format_chat_time(),
                        "is_error": True,
                        "retry_prompt": prompt_text
                    })
            st.rerun()

    # Render Conversation Messages
    st.markdown('<div class="chat-conversation-container">', unsafe_allow_html=True)

    for msg_idx, msg in enumerate(st.session_state["messages"]):
        role = msg["role"]
        content = msg["content"]
        sources = msg.get("sources") or msg.get("citations") or []
        msg_lang = msg.get("language")

        if role == "user":
            st.markdown(
                f"""
                <div class="chat-user-msg-row">
                    <div class="chat-user-bubble">
                        {content}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            lang_tag = f" • <span style='color: #00F298;'>{msg_lang.upper()}</span>" if msg_lang else ""
            st.markdown(
                f"""
                <div class="chat-ai-msg-row">
                    <div class="chat-ai-avatar">🧠</div>
                    <div class="chat-ai-card">
                """,
                unsafe_allow_html=True
            )
            st.markdown(content)

            if sources:
                render_citation_viewer(sources)

            # Retry button if this message had an error
            if msg.get("is_error") and msg.get("retry_prompt"):
                if st.button("🔄 Retry Query", key=f"retry_msg_{msg_idx}"):
                    st.session_state["prompt_input"] = msg["retry_prompt"]
                    st.rerun()

            # Action toolbar (Copy / Regenerate)
            if not msg.get("is_error"):
                act_col1, act_col2, act_col_space = st.columns([1.5, 1.8, 6])
                with act_col1:
                    copy_text = content.replace("'", "\\'").replace("\n", "\\n")
                    st.markdown(
                        f"""
                        <button class="chat-action-btn" onclick="navigator.clipboard.writeText('{copy_text}')" title="Copy response">
                            📋 Copy
                        </button>
                        """,
                        unsafe_allow_html=True
                    )
                with act_col2:
                    if st.button("🔄 Regenerate", key=f"regen_{msg_idx}", help="Regenerate last response"):
                        if msg_idx > 0 and st.session_state["messages"][msg_idx - 1]["role"] == "user":
                            last_user_query = st.session_state["messages"][msg_idx - 1]["content"]
                            st.session_state["messages"] = st.session_state["messages"][:msg_idx]
                            st.session_state["prompt_input"] = last_user_query
                            st.rerun()

            st.markdown(
                """
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # Status Banner for Last Uploaded Document (if present)
    if st.session_state.get("last_uploaded_doc"):
        last_doc = st.session_state["last_uploaded_doc"]
        uc1, uc2 = st.columns([7, 1])
        with uc1:
            st.markdown(
                f"""
                <div style="background: rgba(0, 242, 152, 0.12); border: 1px solid rgba(0, 242, 152, 0.35); border-radius: 20px; padding: 6px 16px; font-size: 0.85rem; color: #FFFFFF; display: inline-flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span>📄</span> <strong>{last_doc.get('filename')}</strong>
                    <span style="color: #94A3B8;">({last_doc.get('chunks', 0)} chunks indexed)</span>
                    <span style="color: #00F298; font-weight: 700;">● READY FOR RAG</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with uc2:
            if st.button("✕", key="dismiss_thread_upload_chip", help="Dismiss"):
                st.session_state.pop("last_uploaded_doc", None)
                st.rerun()

    # =========================================================================
    # Bottom Chat Composer Component
    # [ 📎 Attach ] [ 🎙️ Mic ] [ Multiline Textarea ] [ 0 / 2000 ] [ ✈ Send ]
    # =========================================================================
    composer_event = render_chat_composer(
        token=token or "",
        api_url=BACKEND_API_URL,
        conversation_id=active_conv_id,
        initial_text="",
        key="thread_active_composer"
    )

    if composer_event and isinstance(composer_event, dict):
        action = composer_event.get("action")
        ts = composer_event.get("ts", 0)

        # 1. Handle Send Message Action
        if action == "send":
            sent_text = (composer_event.get("text") or "").strip()
            if sent_text and ts != st.session_state.get("last_thread_composer_ts"):
                st.session_state["last_thread_composer_ts"] = ts
                
                # Check 2000 character limit
                if len(sent_text) > 2000:
                    sent_text = sent_text[:2000]

                st.session_state["messages"].append({
                    "role": "user",
                    "content": sent_text,
                    "sources": [],
                    "time": format_chat_time()
                })

                doc_filter_arg = selected_doc_ids if 'selected_doc_ids' in locals() and selected_doc_ids else None
                active_sim = sim_threshold if 'sim_threshold' in locals() else 0.15

                with st.spinner("AI Assistant is thinking..."):
                    res = api_client.ask_question(
                        question=sent_text,
                        token=token,
                        conversation_id=active_conv_id,
                        document_ids=doc_filter_arg,
                        top_k=4,
                        similarity_threshold=active_sim
                    )

                    if res.get("success"):
                        ans_data = res["data"]
                        st.session_state["active_conversation_id"] = ans_data.get("conversation_id")
                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": ans_data.get("answer", ""),
                            "sources": ans_data.get("sources") or ans_data.get("citations") or [],
                            "language": ans_data.get("language", "en"),
                            "time": format_chat_time()
                        })
                    else:
                        err_msg = res.get("error", "Error generating response.")
                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": f"❌ **Error generating response**: {err_msg}",
                            "sources": [],
                            "language": "en",
                            "time": format_chat_time(),
                            "is_error": True,
                            "retry_prompt": sent_text
                        })
                st.rerun()

        # 2. Handle Document Uploaded via Composer (+)
        elif action == "uploaded":
            fname = composer_event.get("filename")
            if fname and ts != st.session_state.get("last_thread_upload_ts"):
                st.session_state["last_thread_upload_ts"] = ts
                pages_val = composer_event.get("pages", 0)
                chunks_val = composer_event.get("chunks", 0)

                st.session_state["last_uploaded_doc"] = {
                    "filename": fname,
                    "pages": pages_val,
                    "chunks": chunks_val,
                    "status": composer_event.get("status", "completed")
                }

                # Auto-add to scope
                doc_id_val = composer_event.get("id")
                if "filter_doc_ids" not in st.session_state:
                    st.session_state["filter_doc_ids"] = []
                if doc_id_val and doc_id_val not in st.session_state["filter_doc_ids"]:
                    st.session_state["filter_doc_ids"].append(doc_id_val)

                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"✅ Successfully uploaded and indexed **{fname}** ({pages_val} pages, {chunks_val} chunks). You can now ask questions about this document in Tamil, Tanglish, or English!",
                    "sources": [],
                    "language": "en",
                    "time": format_chat_time()
                })
                st.rerun()


__all__ = ["render_chat_view", "extract_chat_input", "format_chat_time"]
