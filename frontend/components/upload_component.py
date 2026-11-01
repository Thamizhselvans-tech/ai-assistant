"""Document upload component supporting drag-and-drop for PDF, DOCX, and TXT files."""

import streamlit as st
from frontend.api_client import api_client
from frontend.config import MAX_UPLOAD_SIZE_MB, SUPPORTED_FILE_TYPES


def render_upload_component(token: str, on_success_callback=None) -> None:
    """Render drag-and-drop uploader with real-time progress and validation."""
    st.markdown(
        f"""
        <div style="background: #161F30; border: 2px dashed #27354A; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 2rem; margin-bottom: 8px;">📤</div>
            <div style="font-weight: 600; font-size: 1rem; color: #F8FAFC;">Upload Knowledge Documents</div>
            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">
                Supported formats: <strong>PDF</strong>, <strong>DOCX</strong>, <strong>TXT</strong> (Up to {MAX_UPLOAD_SIZE_MB}MB per file)
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
        upload_btn = st.button("🚀 Process & Index Selected Files", type="primary", use_container_width=True)

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

                with st.spinner(f"Processing and generating vector embeddings for '{filename}'..."):
                    res = api_client.upload_document(file_bytes, filename, token)
                    if res.get("success"):
                        doc_data = res["data"]
                        status_str = doc_data.get("status", "completed")
                        chunks_str = doc_data.get("chunk_count", 0)
                        pages_str = doc_data.get("page_count", 0)

                        if status_str == "completed":
                            st.success(f"✅ Successfully indexed **{filename}** ({pages_str} pages, {chunks_str} vector chunks).")
                        elif status_str == "warning":
                            msg = doc_data.get("status_message", "Warning during extraction.")
                            st.warning(f"⚠️ **{filename}**: {msg}")
                        else:
                            st.info(f"ℹ️ **{filename}** status: {status_str}.")
                    else:
                        st.error(f"❌ Failed to process '{filename}': {res.get('error')}")

            if on_success_callback:
                on_success_callback()


__all__ = ["render_upload_component"]
