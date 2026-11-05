"""Chat and Grounded RAG QA UI component matching enterprise two-column SaaS layout."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.citation_viewer import render_citation_viewer


def format_chat_time(dt_val: Optional[Any] = None) -> str:
    """Format timestamp into readable string e.g. '10:24 AM' or 'Today, 10:24 AM'."""
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
    """Render modern enterprise RAG chat interface with center chat and right widgets panel."""
    # 1. Top Header Navbar
    render_header(
        title="AI Knowledge Assistant",
        subtitle="Chat with your documents using AI (RAG-powered)",
        show_status=True
    )

    # 2. Fetch User Documents & Recent Conversations Telemetry for Widgets
    docs_res = api_client.list_documents(token)
    user_docs = docs_res.get("data", {}).get("documents", []) if docs_res.get("success") else []
    total_docs = len(user_docs)
    total_chunks = sum(d.get("chunk_count", 0) for d in user_docs)

    doc_options = {
        d["id"]: f"{d.get('original_filename', d.get('filename'))} ({d.get('page_count', 0)} pgs)"
        for d in user_docs if d.get("status") in ["completed", "warning"]
    }

    # Fetch recent conversations
    convs_res = api_client.list_conversations(token, skip=0, limit=5)
    recent_convs = convs_res.get("data", {}).get("conversations", []) if convs_res.get("success") else []

    # 3. Two-Column Layout (Chat Main: ~68%, Right Panel: ~32%)
    col_chat, col_right = st.columns([68, 32], gap="large")

    active_conv_id = st.session_state.get("active_conversation_id")

    with col_chat:
        # Search Settings Expander & Actions Bar
        h_col1, h_col2, h_col3 = st.columns([5, 2, 2])
        with h_col2:
            if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
                st.session_state["active_conversation_id"] = None
                st.session_state["messages"] = []
                st.rerun()
        with h_col3:
            if st.button("🧹 Clear View", use_container_width=True, key="clear_chat_btn"):
                st.session_state["messages"] = []
                st.rerun()

        with st.expander("⚙️ Retrieval Scope & Search Settings", expanded=False):
            f_col1, f_col2, f_col3 = st.columns([3, 1, 1])
            with f_col1:
                default_selected = st.session_state.get("filter_doc_ids", [])
                valid_defaults = [d for d in default_selected if d in doc_options]
                selected_doc_ids = st.multiselect(
                    "Filter Knowledge Scope (leave empty for entire library):",
                    options=list(doc_options.keys()),
                    format_func=lambda x: doc_options.get(x, x),
                    default=valid_defaults,
                    key="chat_scope_filter"
                )
            with f_col2:
                top_k = st.slider("Top Chunks (k)", min_value=1, max_value=10, value=4, step=1)
            with f_col3:
                sim_threshold = st.slider(
                    "Match Threshold",
                    min_value=0.0,
                    max_value=0.50,
                    value=0.10,
                    step=0.05,
                    help="Lower values allow broad/conceptual queries; higher values require exact word matches."
                )

        # Initialize messages state
        if "messages" not in st.session_state:
            st.session_state["messages"] = []

        # Load active conversation if messages are currently empty
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

        # Empty State & Suggested Prompts
        if not st.session_state["messages"]:
            if not doc_options:
                st.info("ℹ️ You have no indexed documents yet. Use the **Upload Documents** button to get started!")
            else:
                st.markdown(
                    """
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 1.75rem 2rem; margin: 1rem 0; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                        <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🤖</div>
                        <h3 style="font-weight: 800; color: #0F172A; margin-bottom: 0.4rem;">How can I assist you today?</h3>
                        <p style="color: #64748B; font-size: 0.9rem; max-width: 550px; margin: 0 auto 1.25rem auto;">
                            Ask natural language questions about your uploaded documents. Responses are synthesized strictly with citations.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown("<p style='font-weight: 700; color: #475569; font-size: 0.85rem; margin-bottom: 6px;'>Suggested Starters:</p>", unsafe_allow_html=True)
                s_cols = st.columns(3)
                starters = [
                    "Summarize the key objectives and main findings.",
                    "What are the primary conclusions stated?",
                    "What is the title and topic of the document?"
                ]
                for idx, starter in enumerate(starters):
                    with s_cols[idx]:
                        if st.button(starter, key=f"starter_btn_{idx}", use_container_width=True):
                            st.session_state["prompt_input"] = starter
                            st.rerun()

        # Render Conversation Message Stream
        for msg in st.session_state["messages"]:
            role = msg["role"]
            content = msg["content"]
            sources = msg.get("sources") or msg.get("citations") or []
            msg_time = msg.get("time") or format_chat_time()

            if role == "user":
                st.markdown(
                    f"""
                    <div style="display: flex; gap: 12px; margin-bottom: 1.25rem; align-items: flex-start;">
                        <div style="width: 38px; height: 38px; border-radius: 50%; background: #2563EB; color: white; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0; box-shadow: 0 2px 6px rgba(37,99,235,0.3);">
                            👤
                        </div>
                        <div style="flex-grow: 1;">
                            <div style="background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 12px; padding: 14px 18px; color: #1E293B; font-size: 0.95rem; line-height: 1.5; font-weight: 500;">
                                {content}
                            </div>
                            <div style="text-align: right; font-size: 0.72rem; color: #94A3B8; margin-top: 4px;">{msg_time}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="display: flex; gap: 12px; margin-bottom: 1.5rem; align-items: flex-start;">
                        <div style="width: 38px; height: 38px; border-radius: 50%; background: #EDE9FE; border: 1px solid #DDD6FE; color: #7C3AED; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;">
                            🤖
                        </div>
                        <div style="flex-grow: 1; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 22px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
                            <div style="font-weight: 700; font-size: 0.98rem; color: #0F172A; margin-bottom: 8px;">Answer</div>
                            <div style="color: #334155; font-size: 0.94rem; line-height: 1.6;">
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(content)

                if sources:
                    render_citation_viewer(sources)

                st.markdown(
                    f"""
                                <div style="text-align: right; font-size: 0.72rem; color: #94A3B8; margin-top: 8px;">{msg_time}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Chat Input Box
        default_prompt = st.session_state.pop("prompt_input", None) or st.session_state.pop("suggested_prompt", None)
        prompt = st.chat_input("Ask a question about your documents...", key="chat_user_input") or default_prompt

        if prompt:
            user_time = format_chat_time()
            st.session_state["messages"].append({
                "role": "user",
                "content": prompt,
                "sources": [],
                "time": user_time
            })

            doc_filter_arg = selected_doc_ids if selected_doc_ids else None
            with st.spinner("Searching document vectors and formulating grounded response..."):
                res = api_client.ask_question(
                    question=prompt,
                    token=token,
                    conversation_id=active_conv_id,
                    document_ids=doc_filter_arg,
                    top_k=top_k,
                    similarity_threshold=sim_threshold
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
                    err_msg = res.get("error", "Error generating response.")
                    st.error(f"❌ {err_msg}")

    # =========================================================================
    # Right Side Panel (Widgets matching reference screenshot)
    # =========================================================================
    with col_right:
        # Card 1: Your Documents
        st.markdown(
            f"""
            <div class="right-panel-card" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px 20px; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 0.95rem; color: #0F172A; margin-bottom: 14px;">
                    <span style="color: #7C3AED; font-size: 1.15rem;">📄</span> Your Documents
                </div>
                <div style="display: flex; justify-content: space-around; text-align: center; border-top: 1px solid #F1F5F9; padding-top: 12px;">
                    <div>
                        <div style="font-size: 1.85rem; font-weight: 800; color: #0F172A; line-height: 1.1;">{total_docs}</div>
                        <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Documents</div>
                    </div>
                    <div style="border-right: 1px solid #F1F5F9; height: 36px; margin-top: 4px;"></div>
                    <div>
                        <div style="font-size: 1.85rem; font-weight: 800; color: #0F172A; line-height: 1.1;">{total_chunks:,}</div>
                        <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Total Chunks</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Card 2: Recent Chats
        st.markdown(
            """
            <div class="right-panel-card" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px 20px; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 0.95rem; color: #0F172A; margin-bottom: 12px;">
                    <span style="color: #0284C7; font-size: 1.15rem;">🕒</span> Recent Chats
                </div>
            """,
            unsafe_allow_html=True
        )

        if not recent_convs:
            st.markdown(
                "<div style='font-size: 0.82rem; color: #94A3B8; padding: 6px 0;'>No recent conversations.</div>",
                unsafe_allow_html=True
            )
        else:
            for c in recent_convs:
                cid = c.get("id")
                c_title = c.get("title", "Conversation")
                truncated_title = (c_title[:28] + "...") if len(c_title) > 28 else c_title
                c_time = format_chat_time(c.get("updated_at") or c.get("created_at"))
                is_active = (cid == active_conv_id)

                bg_style = "background: #EFF6FF; border: 1px solid #BFDBFE;" if is_active else "background: #FFFFFF; border: 1px solid #F1F5F9;"

                st.markdown(
                    f"""
                    <div style="{bg_style} border-radius: 10px; padding: 10px 12px; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.85rem; color: #0F172A;">
                            <span style="color: #2563EB;">💬</span> <span>{truncated_title}</span>
                        </div>
                        <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 3px; padding-left: 22px;">
                            Today, {c_time}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                # Invisible/small click button to activate conversation
                if st.button(f"Open: {truncated_title}", key=f"open_conv_{cid}", use_container_width=True):
                    st.session_state["active_conversation_id"] = cid
                    st.session_state["messages"] = []
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Card 3: Quick Actions
        st.markdown(
            """
            <div class="right-panel-card" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 0.95rem; color: #0F172A; margin-bottom: 12px;">
                    <span style="color: #2563EB; font-size: 1.15rem;">⚡</span> Quick Actions
                </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("⬆ Upload Documents", use_container_width=True, key="qa_upload_docs_btn"):
            st.session_state["navigation_page"] = "📁 Document Library"
            st.rerun()

        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        if st.button("📊 View Analytics", use_container_width=True, key="qa_view_analytics_btn"):
            st.session_state["navigation_page"] = "📊 Analytics"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


__all__ = ["render_chat_view"]
