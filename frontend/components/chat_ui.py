"""Chat and RAG QA UI component."""

import streamlit as st
from typing import List, Optional
from frontend.services.api_client import api_client


def render_chat_view(token: str):
    """Render the AI Knowledge Assistant chat interface."""
    # Top bar: Conversation info & actions
    col_title, col_actions = st.columns([3, 2])

    with col_title:
        st.markdown("## 💬 AI Knowledge Assistant")
        st.markdown("<p style='color: #64748B;'>Ask questions grounded exclusively in your uploaded documents.</p>", unsafe_allow_html=True)

    with col_actions:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("➕ New Chat", use_container_width=True):
                st.session_state["active_conversation_id"] = None
                st.session_state["messages"] = []
                st.rerun()
        with btn_c2:
            if st.button("🧹 Clear Chat", use_container_width=True):
                st.session_state["messages"] = []
                st.rerun()

    # Document filter & retrieval controls
    docs_res = api_client.list_documents(token)
    doc_options = {}
    if docs_res.get("success"):
        for d in docs_res.get("data", {}).get("documents", []):
            if d.get("status") == "completed":
                doc_options[d["id"]] = f"{d['original_filename']} ({d['page_count']} pgs)"

    with st.expander("⚙️ Retrieval Scope & Options", expanded=False):
        f_col1, f_col2 = st.columns([3, 1])
        with f_col1:
            default_selected = st.session_state.get("filter_doc_ids", [])
            valid_defaults = [d for d in default_selected if d in doc_options]
            selected_doc_ids = st.multiselect(
                "Filter Knowledge Scope (leave empty to search all documents):",
                options=list(doc_options.keys()),
                format_func=lambda x: doc_options.get(x, x),
                default=valid_defaults,
                key="chat_scope_filter"
            )
        with f_col2:
            top_k = st.slider("Top Sources (k)", min_value=1, max_value=8, value=4, step=1)

    # Initialize chat history state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # If conversation_id is set but messages are empty, load from backend
    active_conv_id = st.session_state.get("active_conversation_id")
    if active_conv_id and not st.session_state["messages"]:
        with st.spinner("Loading conversation history..."):
            hist_res = api_client.get_conversation_history(active_conv_id, token)
            if hist_res.get("success"):
                raw_messages = hist_res["data"].get("messages", [])
                st.session_state["messages"] = [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "sources": m.get("sources", [])
                    }
                    for m in raw_messages
                ]

    # Empty State & Suggested Starter Questions
    if not st.session_state["messages"]:
        if not doc_options:
            st.warning("⚠️ You have no documents uploaded yet. Go to **📁 Documents** to upload your first document!")
        else:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 2rem; margin: 1.5rem 0; text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
                    <h3 style="color: #1E293B; font-weight: 600; margin-bottom: 0.5rem;">How can I help you today?</h3>
                    <p style="color: #64748B; font-size: 0.95rem; max-width: 600px; margin: 0 auto 1.5rem auto;">
                        Ask any factual question regarding your indexed documents. Answers are strictly synthesized from retrieved evidence with full page citations.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("<p style='font-weight: 600; color: #475569; font-size: 0.9rem;'>Suggested starter questions:</p>", unsafe_allow_html=True)
            starter_cols = st.columns(3)
            starters = [
                "Summarize the key objectives and main findings.",
                "What are the primary conclusions reached in these documents?",
                "List the critical data points, metrics, and definitions mentioned."
            ]
            for idx, starter in enumerate(starters):
                with starter_cols[idx]:
                    if st.button(starter, key=f"starter_{idx}", use_container_width=True):
                        st.session_state["prompt_input"] = starter
                        st.rerun()

    # Display Chat Messages
    for msg in st.session_state["messages"]:
        role = msg["role"]
        content = msg["content"]
        sources = msg.get("sources", [])

        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🤖"):
            st.markdown(content)

            # Display source citations if assistant message and sources exist
            if role == "assistant" and sources:
                st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
                with st.expander(f"📚 Grounded in {len(sources)} Source Citation{'s' if len(sources) > 1 else ''}", expanded=False):
                    for idx, src in enumerate(sources, 1):
                        filename = src.get("filename", "Unknown document")
                        page = src.get("page_number")
                        page_str = f"Page {page}" if page else "Page N/A"
                        score = src.get("score")
                        score_badge = f"<span style='background:#E0E7FF; color:#3730A3; padding:2px 6px; border-radius:4px; font-size:0.75rem; font-weight:600;'>Match: {int(score * 100)}%</span>" if score else ""

                        st.markdown(
                            f"""
                            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
                                    <strong>Source {idx}: {filename}</strong>
                                    <div>
                                        <span style="font-size:0.8rem; color:#64748B; margin-right:6px;">{page_str}</span>
                                        {score_badge}
                                    </div>
                                </div>
                                <blockquote style="margin: 0; padding-left: 10px; border-left: 3px solid #2563EB; font-size: 0.88rem; color: #334155; font-style: italic;">
                                    {src.get('excerpt', '')}
                                </blockquote>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    # Chat Input Box
    default_prompt = st.session_state.pop("prompt_input", None) or st.session_state.pop("suggested_prompt", None)
    prompt = st.chat_input("Ask a question about your documents...", key="chat_user_input") or default_prompt

    if prompt:
        # 1. Add user message to UI immediately
        st.session_state["messages"].append({"role": "user", "content": prompt, "sources": []})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # 2. Call backend RAG API
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Searching document vectors and formulating grounded response..."):
                doc_filter_arg = selected_doc_ids if selected_doc_ids else None
                res = api_client.ask_question(
                    question=prompt,
                    token=token,
                    conversation_id=active_conv_id,
                    document_ids=doc_filter_arg,
                    top_k=top_k
                )

                if res.get("success"):
                    ans_data = res["data"]
                    answer = ans_data.get("answer", "")
                    citations = ans_data.get("sources", [])
                    st.session_state["active_conversation_id"] = ans_data.get("conversation_id")

                    st.markdown(answer)

                    if citations:
                        st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
                        with st.expander(f"📚 Grounded in {len(citations)} Source Citation{'s' if len(citations) > 1 else ''}", expanded=False):
                            for idx, src in enumerate(citations, 1):
                                filename = src.get("filename", "Unknown document")
                                page = src.get("page_number")
                                page_str = f"Page {page}" if page else "Page N/A"
                                score = src.get("score")
                                score_badge = f"<span style='background:#E0E7FF; color:#3730A3; padding:2px 6px; border-radius:4px; font-size:0.75rem; font-weight:600;'>Match: {int(score * 100)}%</span>" if score else ""

                                st.markdown(
                                    f"""
                                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
                                            <strong>Source {idx}: {filename}</strong>
                                            <div>
                                                <span style="font-size:0.8rem; color:#64748B; margin-right:6px;">{page_str}</span>
                                                {score_badge}
                                            </div>
                                        </div>
                                        <blockquote style="margin: 0; padding-left: 10px; border-left: 3px solid #2563EB; font-size: 0.88rem; color: #334155; font-style: italic;">
                                            {src.get('excerpt', '')}
                                        </blockquote>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                    # Save to state
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": answer,
                        "sources": citations
                    })
                    st.rerun()
                else:
                    err_msg = res.get("error", "Error generating response.")
                    st.error(f"❌ {err_msg}")
