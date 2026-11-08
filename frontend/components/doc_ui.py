"""Document Library View Component in Dark Emerald Theme."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.upload_component import render_upload_component
from frontend.components.document_card import render_document_card


def render_documents_view(token: str):
    """Render My Documents interface with dark emerald glassmorphism."""
    render_header()

    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.8rem;">📁</span> My Documents
            </div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">
                Manage documents indexed into ChromaDB for grounded RAG query answering.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Upload Component Expander
    with st.expander("📤 Upload New Documents to Library", expanded=False):
        render_upload_component(token=token, on_success_callback=lambda: None)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # 2. Controls and Search
    col_hdr, col_refresh = st.columns([5, 1])
    with col_hdr:
        st.markdown("<div style='font-weight: 700; font-size: 1.05rem; color: #FFFFFF;'>Indexed Documents</div>", unsafe_allow_html=True)
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    search_query = st.text_input("🔍 Search documents by name...", placeholder="Search indexed files...", label_visibility="collapsed")

    # Fetch user documents
    with st.spinner("Fetching indexed documents..."):
        docs_res = api_client.list_documents(token)

    if not docs_res.get("success"):
        st.error(f"Failed to fetch documents: {docs_res.get('error')}")
        return

    documents = docs_res.get("data", {}).get("documents", [])

    if not documents:
        st.markdown(
            """
            <div style="background: rgba(11, 20, 15, 0.7); border: 1px dashed rgba(0, 242, 152, 0.3); border-radius: 16px; padding: 3rem 2rem; text-align: center; margin-top: 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem; filter: drop-shadow(0 0 10px #00F298);">📁</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF;">No documents uploaded yet</div>
                <div style="color: #94A3B8; font-size: 0.88rem; margin-top: 6px;">
                    Upload PDF, DOCX, or TXT files above to query them in Tamil, Tanglish, or English.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    if search_query:
        documents = [d for d in documents if search_query.lower() in d.get("filename", "").lower() or search_query.lower() in d.get("original_filename", "").lower()]

    st.markdown(f"<p style='color: #00F298; font-size: 0.82rem; font-weight: 600; margin-bottom: 1rem;'>● {len(documents)} document(s) available in vector library</p>", unsafe_allow_html=True)

    def handle_delete(doc_id: str):
        with st.spinner("Deleting document from ChromaDB and database..."):
            del_res = api_client.delete_document(doc_id, token)
            if del_res.get("success"):
                st.success("Document deleted successfully.")
                st.rerun()
            else:
                st.error(f"Delete failed: {del_res.get('error')}")

    for doc in documents:
        render_document_card(doc=doc, on_delete=handle_delete)


__all__ = ["render_documents_view"]
