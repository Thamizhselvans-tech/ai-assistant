"""Document management UI component: upload dropzone, document library, and deletion actions."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.upload_component import render_upload_component
from frontend.components.document_card import render_document_card


def render_documents_view(token: str):
    """Render Document Management interface."""
    render_header(
        title="Document Management",
        subtitle="Upload, review, and manage your private documents for semantic search and AI analysis.",
        badge_text="KNOWLEDGE BASE"
    )

    # 1. Upload Component
    with st.expander("📤 Upload New Documents", expanded=True):
        render_upload_component(token=token, on_success_callback=lambda: None)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 2. Document Library Controls
    col_hdr, col_refresh = st.columns([5, 1])
    with col_hdr:
        st.markdown("### 📚 Your Document Library")
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Search filter
    search_query = st.text_input("🔍 Filter documents by name...", placeholder="Type filename to search...", label_visibility="collapsed")

    # Fetch user documents
    with st.spinner("Loading document repository..."):
        docs_res = api_client.list_documents(token)

    if not docs_res.get("success"):
        st.error(f"Failed to fetch documents: {docs_res.get('error')}")
        return

    documents = docs_res.get("data", {}).get("documents", [])

    if not documents:
        st.markdown(
            """
            <div style="background: #161F30; border: 1px solid #27354A; border-radius: 10px; padding: 2.5rem; text-align: center; margin-top: 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📄</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #F8FAFC;">No Documents Ingested Yet</div>
                <div style="color: #94A3B8; font-size: 0.88rem; margin-top: 4px;">
                    Upload your first PDF, DOCX, or TXT file above to start semantic retrieval!
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Filter by search
    if search_query:
        documents = [d for d in documents if search_query.lower() in d.get("filename", "").lower() or search_query.lower() in d.get("original_filename", "").lower()]

    st.markdown(f"<p style='color: #94A3B8; font-size: 0.82rem;'>Showing {len(documents)} document(s)</p>", unsafe_allow_html=True)

    def handle_delete(doc_id: str):
        with st.spinner("Deleting document and vector records..."):
            del_res = api_client.delete_document(doc_id, token)
            if del_res.get("success"):
                st.success("Document and vector records deleted successfully.")
                st.rerun()
            else:
                st.error(f"Delete failed: {del_res.get('error')}")

    for doc in documents:
        render_document_card(doc=doc, on_delete=handle_delete)


__all__ = ["render_documents_view"]
