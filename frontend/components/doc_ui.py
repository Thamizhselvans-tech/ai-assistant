"""Document management UI component: upload dropzone, document library, and deletion actions."""

import streamlit as st
from frontend.api_client import api_client
from frontend.components.header import render_header
from frontend.components.upload_component import render_upload_component
from frontend.components.document_card import render_document_card


def render_documents_view(token: str):
    """Render Document Management interface matching modern SaaS layout."""
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
        st.markdown("<h3 style='color: #0F172A; font-weight: 700; margin-bottom: 0.5rem;'>📚 Your Document Library</h3>", unsafe_allow_html=True)
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
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 3rem 2rem; text-align: center; margin-top: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="font-size: 2.8rem; margin-bottom: 0.75rem;">📄</div>
                <div style="font-size: 1.15rem; font-weight: 700; color: #0F172A;">No Documents Ingested Yet</div>
                <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px;">
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

    st.markdown(f"<p style='color: #64748B; font-size: 0.85rem; margin-bottom: 1rem;'>Showing {len(documents)} document(s)</p>", unsafe_allow_html=True)

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
