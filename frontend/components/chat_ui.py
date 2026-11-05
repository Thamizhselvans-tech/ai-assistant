"""ChatGPT-style conversational interface with document upload (+) attachment icon on left."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st
from frontend.api_client import api_client
from frontend.config import MAX_UPLOAD_SIZE_MB
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


def extract_chat_input(raw_input: Any):
    """Extract text prompt and attached files list from chat_input return value."""
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
    """Render ChatGPT-style conversational interface with document attachment (+) icon."""
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
                "Filter Knowledge Scope (leave empty for entire library):",
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options.get(x, x),
                default=valid_defaults,
                key="chat_scope_filter"
            )
        with c2:
            sim_threshold = st.slider("Match Threshold", 0.0, 0.5, 0.15, 0.05, help="Match tolerance")

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

        # Top New Chat Action
        top_c1, top_c2 = st.columns([6, 1])
        with top_c2:
            if st.button("📝 New", key="top_new_chat_btn", use_container_width=True, help="Start new chat"):
                st.session_state["active_conversation_id"] = None
                st.session_state["messages"] = []
                st.rerun()

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
    # Status Banner for Last Uploaded Document (if present)
    # =========================================================================
    if st.session_state.get("last_uploaded_doc"):
        last_doc = st.session_state["last_uploaded_doc"]
        chip_col1, chip_col2 = st.columns([7, 1])
        with chip_col1:
            st.markdown(
                f"""
                <div class="uploaded-doc-chip">
                    <span>📄</span> <strong>{last_doc.get('filename')}</strong>
                    <span>({last_doc.get('chunks', 0)} chunks indexed)</span>
                    <span>• Status: {last_doc.get('status', 'completed').upper()}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with chip_col2:
            if st.button("✕", key="dismiss_upload_chip", help="Dismiss upload indicator"):
                st.session_state.pop("last_uploaded_doc", None)
                st.rerun()

    # =========================================================================
    # Bottom ChatGPT Capsule Composer with Document Attachment (+) on Left
    # [ + Upload ] [ Ask a question about your documents... ] [ ↑ Send ]
    # =========================================================================
    default_prompt = st.session_state.pop("prompt_input", None) or action_prompt

    raw_input = st.chat_input(
        placeholder="Ask a question about your documents...",
        key="chatgpt_user_input",
        accept_file="multiple",
        file_type=["pdf", "docx", "txt"]
    )

    active_input = raw_input or default_prompt

    if active_input:
        prompt_text, attached_files = extract_chat_input(active_input)

        # 1. Process Attached Document Uploads
        upload_successful_count = 0
        newly_indexed_docs = []

        if attached_files:
            max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
            for file_item in attached_files:
                fname = file_item.name
                ext = fname.split(".")[-1].lower() if "." in fname else ""

                if ext not in ["pdf", "docx", "txt"]:
                    st.error(f"❌ '{fname}' is unsupported. Only PDF, DOCX, and TXT are accepted.")
                    continue

                fbytes = file_item.getvalue()
                if len(fbytes) > max_bytes:
                    st.error(f"❌ '{fname}' exceeds the maximum size limit of {MAX_UPLOAD_SIZE_MB}MB.")
                    continue

                if len(fbytes) == 0:
                    st.error(f"❌ '{fname}' is empty (0 bytes).")
                    continue

                with st.spinner(f"Uploading and indexing '{fname}' via FastAPI RAG service..."):
                    res = api_client.upload_document(fbytes, fname, token)

                if res.get("success"):
                    doc_data = res["data"]
                    status_val = doc_data.get("status", "completed")
                    pages_val = doc_data.get("page_count", 0)
                    chunks_val = doc_data.get("chunk_count", 0)
                    doc_id_val = doc_data.get("id")

                    upload_successful_count += 1
                    newly_indexed_docs.append(fname)

                    st.session_state["last_uploaded_doc"] = {
                        "filename": fname,
                        "status": status_val,
                        "pages": pages_val,
                        "chunks": chunks_val
                    }

                    # Automatically add newly uploaded document to knowledge scope
                    if "filter_doc_ids" not in st.session_state:
                        st.session_state["filter_doc_ids"] = []
                    if doc_id_val and doc_id_val not in st.session_state["filter_doc_ids"]:
                        st.session_state["filter_doc_ids"].append(doc_id_val)

                    if status_val == "completed":
                        st.success(f"✅ Indexed **{fname}** ({pages_val} pages, {chunks_val} chunks).")
                    elif status_val == "warning":
                        st.warning(f"⚠️ **{fname}**: {doc_data.get('status_message', 'Warning during extraction.')}")
                else:
                    err_msg = res.get("error", "Upload failed.")
                    st.error(f"❌ Upload failed for '{fname}': {err_msg}")

        # 2. Process User Question (if provided)
        if prompt_text:
            user_time = format_chat_time()
            st.session_state["messages"].append({
                "role": "user",
                "content": prompt_text,
                "sources": [],
                "time": user_time
            })

            doc_filter_arg = selected_doc_ids if 'selected_doc_ids' in locals() and selected_doc_ids else None
            active_sim = sim_threshold if 'sim_threshold' in locals() else 0.15

            with st.spinner("Thinking..."):
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

        # 3. If files were uploaded without question text, post confirmation message in chat
        elif newly_indexed_docs:
            docs_summary = ", ".join(f"**{d}**" for d in newly_indexed_docs)
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"✅ Successfully uploaded and indexed {docs_summary} into your document library. You can now ask questions about these documents!",
                "sources": [],
                "time": format_chat_time()
            })
            st.rerun()


__all__ = ["render_chat_view"]
