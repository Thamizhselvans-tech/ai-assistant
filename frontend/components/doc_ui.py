"""Document management UI component: upload dropzone, document library, and deletion actions."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.upload_component import render_upload_component
from frontend.components.document_card import render_document_card


def render_documents_view(token: str):
    """Render Document Library interface matching minimalist ChatGPT style."""
    render_header()

    st.markdown("<h2 style='font-size: 1.5rem; font-weight: 600; color: #0D0D0D; margin-bottom: 0.5rem;'>Document Library</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8E8E8E; font-size: 0.9rem; margin-bottom: 1.5rem;'>Upload and manage documents for grounded AI search and question answering.</p>", unsafe_allow_html=True)

    # 1. Upload Component
    with st.expander("📤 Upload New Documents", expanded=True):
        render_upload_component(token=token, on_success_callback=lambda: None)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 2. Document Library Controls
    col_hdr, col_refresh = st.columns([5, 1])
    with col_hdr:
        st.markdown("<div style='font-weight: 600; font-size: 1.05rem; color: #0D0D0D;'>Uploaded Documents</div>", unsafe_allow_html=True)
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Search filter
    search_query = st.text_input("🔍 Filter documents by name...", placeholder="Search documents...", label_visibility="collapsed")

    # Fetch user documents
    with st.spinner("Loading documents..."):
        docs_res = api_client.list_documents(token)

    if not docs_res.get("success"):
        st.error(f"Failed to fetch documents: {docs_res.get('error')}")
        return

    documents = docs_res.get("data", {}).get("documents", [])

    if not documents:
        st.markdown(
            """
            <div style="background: #F9F9F9; border: 1px solid #E5E5E5; border-radius: 12px; padding: 3rem 2rem; text-align: center; margin-top: 1rem;">
                <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">📄</div>
                <div style="font-size: 1.05rem; font-weight: 600; color: #0D0D0D;">No documents uploaded yet</div>
                <div style="color: #8E8E8E; font-size: 0.88rem; margin-top: 4px;">
                    Upload a PDF, DOCX, or TXT file above to begin querying your documents.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Filter by search
    if search_query:
        documents = [d for d in documents if search_query.lower() in d.get("filename", "").lower() or search_query.lower() in d.get("original_filename", "").lower()]

    st.markdown(f"<p style='color: #8E8E8E; font-size: 0.82rem; margin-bottom: 1rem;'>{len(documents)} document(s)</p>", unsafe_allow_html=True)

    def handle_delete(doc_id: str):
        with st.spinner("Deleting document..."):
            del_res = api_client.delete_document(doc_id, token)
            if del_res.get("success"):
                st.success("Document deleted.")
                st.rerun()
            else:
                st.error(f"Delete failed: {del_res.get('error')}")

    for doc in documents:
        render_document_card(doc=doc, on_delete=handle_delete)


__all__ = ["render_documents_view"]
