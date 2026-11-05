"""Chat and Grounded RAG QA UI component."""

from typing import List, Optional
import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.citation_viewer import render_citation_viewer


def render_chat_view(token: str):
    """Render the AI Knowledge Assistant chat interface."""
    col_title, col_actions = st.columns([3, 2])

    with col_title:
        render_header(
            title="AI Knowledge Assistant",
            subtitle="Ask factual questions synthesized strictly from your uploaded documents.",
            badge_text="RAG QA"
        )

    with col_actions:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("➕ New Chat", use_container_width=True):
                st.session_state["active_conversation_id"] = None
                st.session_state["messages"] = []
                st.rerun()
        with btn_c2:
            if st.button("🧹 Clear View", use_container_width=True):
                st.session_state["messages"] = []
                st.rerun()

    # Scope & Options
    docs_res = api_client.list_documents(token)
    doc_options = {}
    if docs_res.get("success"):
        for d in docs_res.get("data", {}).get("documents", []):
            if d.get("status") == "completed":
                doc_options[d["id"]] = f"{d['original_filename']} ({d['page_count']} pgs)"

    with st.expander("⚙️ Retrieval Scope & Search Settings", expanded=False):
        f_col1, f_col2, f_col3 = st.columns([3, 1, 1])
        with f_col1:
            default_selected = st.session_state.get("filter_doc_ids", [])
            valid_defaults = [d for d in default_selected if d in doc_options]
            selected_doc_ids = st.multiselect(
                "Filter Knowledge Scope (leave empty to query entire document library):",
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

    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # If conversation_id is active but messages empty, fetch from backend
    active_conv_id = st.session_state.get("active_conversation_id")
    if active_conv_id and not st.session_state["messages"]:
        with st.spinner("Loading conversation messages..."):
            hist_res = api_client.get_conversation_history(active_conv_id, token)
            if hist_res.get("success"):
                raw_messages = hist_res["data"].get("messages", [])
                st.session_state["messages"] = [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "sources": m.get("sources") or m.get("citations") or []
                    }
                    for m in raw_messages
                ]

    # Empty State & Suggested Questions
    if not st.session_state["messages"]:
        if not doc_options:
            st.info("ℹ️ You have no indexed documents yet. Upload a document in **Documents** to ask grounded questions.")
        else:
            st.markdown(
                """
                <div style="background: #161F30; border: 1px solid #27354A; border-radius: 12px; padding: 2rem; margin: 1.5rem 0; text-align: center;">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🤖</div>
                    <h3 style="font-weight: 800; background: linear-gradient(90deg, #10B981 0%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; display: inline-block;">How can I assist you today?</h3>
                    <p style="color: #94A3B8; font-size: 0.92rem; max-width: 600px; margin: 0 auto 1.5rem auto;">
                        Ask natural language questions about your uploaded documents. Responses are generated with strict provenance citations and zero hallucinated facts.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("<p style='font-weight: 600; color: #94A3B8; font-size: 0.85rem;'>Suggested Prompts:</p>", unsafe_allow_html=True)
            starter_cols = st.columns(3)
            starters = [
                "Summarize the key objectives and main findings.",
                "What are the primary conclusions and metrics stated?",
                "List the critical system requirements and definitions."
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
        sources = msg.get("sources") or msg.get("citations") or []

        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🧠"):
            st.markdown(content)
            if role == "assistant" and sources:
                render_citation_viewer(sources)

    # Chat Input Box
    default_prompt = st.session_state.pop("prompt_input", None) or st.session_state.pop("suggested_prompt", None)
    prompt = st.chat_input("Ask a question about your documents...", key="chat_user_input") or default_prompt

    if prompt:
        # Add user message to UI
        st.session_state["messages"].append({"role": "user", "content": prompt, "sources": []})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # Call backend RAG API
        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Searching document vectors and formulating grounded response..."):
                doc_filter_arg = selected_doc_ids if selected_doc_ids else None
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

                    st.markdown(answer)
                    if citations:
                        render_citation_viewer(citations)

                    # Save assistant message to state
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": answer,
                        "sources": citations
                    })
                    st.rerun()
                else:
                    err_msg = res.get("error", "Error generating response.")
                    st.error(f"❌ {err_msg}")


__all__ = ["render_chat_view"]
