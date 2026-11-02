"""Document card rendering component with status badges and deletion triggers."""

from typing import Any, Callable, Dict, Optional
import streamlit as st
from frontend.config import FILE_ICONS


def format_file_size(bytes_count: int) -> str:
    """Format bytes into readable KB/MB string."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    else:
        return f"{bytes_count / (1024 * 1024):.1f} MB"


def render_document_card(doc: Dict[str, Any], on_delete: Optional[Callable[[str], None]] = None) -> None:
    """Render a card displaying document provenance metadata, status, and delete action."""
    doc_id = doc.get("id")
    filename = doc.get("filename", "document")
    file_type = doc.get("file_type", "txt").lower()
    file_size = format_file_size(doc.get("file_size_bytes", 0))
    status_str = doc.get("status", "completed").lower()
    page_count = doc.get("page_count", 0)
    chunk_count = doc.get("chunk_count", 0)
    created_at = doc.get("created_at", "")[:10]

    icon = FILE_ICONS.get(file_type, "📄")
    badge_class = f"badge-{status_str}" if status_str in ["completed", "processing", "warning", "failed"] else "badge-processing"

    col_info, col_action = st.columns([5, 1])

    with col_info:
        pages_badge = f'<span style="color: #94A3B8; font-size: 0.78rem;">• {page_count} pages</span>' if page_count > 0 else ""
        warning_msg = doc.get("status_message")
        warning_html = f'<div style="color: #FBBF24; font-size: 0.78rem; margin-top: 6px;">⚠️ {warning_msg}</div>' if (status_str == "warning" and warning_msg) else ""
        st.markdown(
            f"""
            <div style="background: #161F30; border: 1px solid #27354A; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="font-weight: 600; font-size: 0.95rem; color: #F8FAFC; display: flex; align-items: center; gap: 8px;">
                        <span>{icon}</span> <span>{filename}</span>
                    </div>
                    <div>
                        <span class="metric-badge {badge_class}">{status_str.upper()}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; font-size: 0.78rem; color: #94A3B8; margin-top: 6px; align-items: center;">
                    <span>Size: {file_size}</span>
                    {pages_badge}
                    <span>• {chunk_count} vector chunks</span>
                    <span>• Uploaded: {created_at}</span>
                </div>
                {warning_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_action:
        if on_delete:
            if st.button("🗑️", key=f"del_doc_{doc_id}", help="Delete document and vector chunks", use_container_width=True):
                on_delete(doc_id)


__all__ = ["render_document_card", "format_file_size"]
