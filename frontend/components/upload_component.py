"""Document upload component supporting drag-and-drop for PDF, DOCX, and TXT files."""

import streamlit as st
from frontend.api_client import api_client
from frontend.config import MAX_UPLOAD_SIZE_MB, SUPPORTED_FILE_TYPES


def render_upload_component(token: str, on_success_callback=None) -> None:
    """Render clean, minimalist drag-and-drop uploader with real-time validation."""
    st.markdown(
        f"""
        <div style="background: #F9F9F9; border: 1px dashed #D1D1D1; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 16px;">
            <div style="font-size: 1.8rem; margin-bottom: 6px;">📄</div>
            <div style="font-weight: 600; font-size: 0.95rem; color: #0D0D0D;">Upload Documents</div>
            <div style="font-size: 0.8rem; color: #8E8E8E; margin-top: 2px;">
                PDF, DOCX, or TXT up to {MAX_UPLOAD_SIZE_MB}MB
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        upload_btn = st.button("Index Selected Files", type="primary", use_container_width=True)

        if upload_btn:
            max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
            for file in uploaded_files:
                filename = file.name
                file_bytes = file.getvalue()

                # Client-side size validation
                if len(file_bytes) > max_bytes:
                    st.error(f"❌ '{filename}' exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB.")
                    continue
                if len(file_bytes) == 0:
                    st.error(f"❌ '{filename}' is empty (0 bytes).")
                    continue

                with st.spinner(f"Indexing '{filename}'..."):
                    res = api_client.upload_document(file_bytes, filename, token)
                    if res.get("success"):
                        doc_data = res["data"]
                        status_str = doc_data.get("status", "completed")
                        chunks_str = doc_data.get("chunk_count", 0)
                        pages_str = doc_data.get("page_count", 0)

                        if status_str == "completed":
                            st.success(f"Indexed **{filename}** ({pages_str} pages, {chunks_str} chunks).")
                        elif status_str == "warning":
                            msg = doc_data.get("status_message", "Warning during extraction.")
                            st.warning(f"⚠️ **{filename}**: {msg}")
                        else:
                            st.info(f"ℹ️ **{filename}**: {status_str}.")
                    else:
                        st.error(f"Failed to process '{filename}': {res.get('error')}")

            if on_success_callback:
                on_success_callback()


__all__ = ["render_upload_component"]
