"""Document management UI component: upload dropzone, document list, status badges, deletion."""

import streamlit as st
from frontend.services.api_client import api_client


def render_documents_view(token: str):
    """Render Document Management dashboard."""
    st.markdown("## 📁 Document Management")
    st.markdown("<p style='color: #64748B;'>Upload, view, and manage your private documents for semantic retrieval and AI analysis.</p>", unsafe_allow_html=True)

    # --- Upload Section ---
    with st.expander("📤 Upload New Document", expanded=True):
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 10px; padding: 1.5rem; text-align: center; margin-bottom: 1rem;">
                <p style="font-weight: 600; color: #1E293B; margin-bottom: 0.25rem;">Supported formats: PDF, DOCX, TXT</p>
                <p style="font-size: 0.85rem; color: #64748B; margin: 0;">Maximum file size: 15 MB. Files are processed locally and securely isolated to your account.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed",
            key="doc_uploader"
        )

        if uploaded_file is not None:
            col1, col2 = st.columns([3, 1])
            with col1:
                size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                st.info(f"Selected: **{uploaded_file.name}** ({size_mb:.2f} MB)")
            with col2:
                if st.button("🚀 Process & Index", use_container_width=True, type="primary"):
                    with st.spinner("Extracting text, chunking, and generating vector embeddings..."):
                        file_bytes = uploaded_file.getvalue()
                        res = api_client.upload_document(file_bytes, uploaded_file.name, token)
                        if res.get("success"):
                            doc_data = res["data"]
                            status = doc_data.get("status")
                            if status == "completed":
                                st.success(f"✅ Successfully indexed '{uploaded_file.name}' ({doc_data.get('page_count', 1)} pages, {doc_data.get('chunk_count', 0)} chunks).")
                            elif status == "warning":
                                st.warning(f"⚠️ {doc_data.get('status_message', 'Document indexed with warnings.')}")
                            
                            # Starter questions suggestion
                            st.session_state["suggested_prompt"] = f"Summarize the key takeaways and main concepts from {uploaded_file.name}"
                            st.session_state["active_doc_id"] = doc_data.get("id")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {res.get('error', 'Unknown error')}")

    st.markdown("### 📚 Your Document Library")

    # Fetch existing documents
    docs_res = api_client.list_documents(token)
    if not docs_res.get("success"):
        st.error(f"Error fetching documents: {docs_res.get('error')}")
        return

    documents = docs_res.get("data", {}).get("documents", [])

    if not documents:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 2.5rem; text-align: center;">
                <p style="font-size: 1.5rem; margin-bottom: 0.5rem;">📄 No documents yet</p>
                <p style="color: #64748B; font-size: 0.95rem;">Upload your first PDF, DOCX, or TXT file above to start asking questions!</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Display documents table/cards
    for doc in documents:
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 2, 1.2])

            with c1:
                icon = "📕" if doc["file_type"] == "pdf" else ("📘" if doc["file_type"] == "docx" else "📄")
                st.markdown(f"**{icon} {doc['original_filename']}**")
                size_kb = doc["file_size_bytes"] / 1024
                st.caption(f"Size: {size_kb:.1f} KB • Uploaded: {doc['created_at'][:10]}")

            with c2:
                pages = doc.get("page_count", 0)
                chunks = doc.get("chunk_count", 0)
                st.markdown(f"**{pages}** pages")
                st.caption(f"{chunks} chunks")

            with c3:
                status = doc.get("status", "pending")
                if status == "completed":
                    st.markdown("<span style='background: #DCFCE7; color: #166534; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;'>● Ready</span>", unsafe_allow_html=True)
                elif status == "warning":
                    st.markdown("<span style='background: #FEF9C3; color: #854D0E; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;'>▲ Scanned / Warning</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='background: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;'>✕ Failed</span>", unsafe_allow_html=True)

            with c4:
                if status == "warning":
                    st.caption(doc.get("status_message") or "Scanned or low text detected.")
                elif status == "completed":
                    if st.button("💬 Ask AI", key=f"chat_doc_{doc['id']}"):
                        st.session_state["filter_doc_ids"] = [doc["id"]]
                        st.session_state["current_page"] = "💬 AI Chat"
                        st.rerun()

            with c5:
                if st.button("🗑️ Delete", key=f"del_doc_{doc['id']}", help="Delete document and vector index"):
                    with st.spinner("Deleting document and vector records..."):
                        del_res = api_client.delete_document(doc["id"], token)
                        if del_res.get("success"):
                            st.success("Document deleted.")
                            st.rerun()
                        else:
                            st.error(del_res.get("error", "Failed to delete document"))

            st.divider()
