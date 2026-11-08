"""Dark Emerald Glassmorphic Document Card Component."""

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
    """Render a sleek glassmorphic card displaying document provenance metadata, status, and delete action."""
    doc_id = doc.get("id")
    filename = doc.get("filename", "document")
    file_type = doc.get("file_type", "txt").lower()
    file_size = format_file_size(doc.get("file_size_bytes", 0))
    status_str = doc.get("status", "completed").lower()
    page_count = doc.get("page_count", 0)
    chunk_count = doc.get("chunk_count", 0)
    created_at = doc.get("created_at", "")[:10]

    icon = FILE_ICONS.get(file_type, "📄")
    badge_cls = f"doc-badge-{file_type}" if file_type in ["pdf", "docx", "txt"] else "doc-badge-txt"

    col_info, col_action = st.columns([6, 1])

    with col_info:
        pages_badge = f'<span>• {page_count} pages</span>' if page_count > 0 else ""
        warning_msg = doc.get("status_message")
        warning_html = f'<div style="color: #F59E0B; font-size: 0.8rem; margin-top: 4px;">⚠️ {warning_msg}</div>' if (status_str == "warning" and warning_msg) else ""
        
        st.markdown(
            f"""
            <div style="background: rgba(11, 20, 15, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 12px; padding: 14px 18px; margin-bottom: 8px; backdrop-filter: blur(10px);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="font-weight: 600; font-size: 0.95rem; color: #FFFFFF; display: flex; align-items: center; gap: 10px;">
                        <span class="doc-badge {badge_cls}">{file_type.upper()}</span>
                        <span>{filename}</span>
                    </div>
                    <div>
                        <span style="font-size: 0.72rem; padding: 2px 8px; border-radius: 10px; font-weight: 700; background: rgba(0, 242, 152, 0.15); color: #00F298; border: 1px solid rgba(0, 242, 152, 0.3);">
                            {status_str.upper()}
                        </span>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; font-size: 0.78rem; color: #94A3B8; margin-top: 6px; align-items: center;">
                    <span>Size: {file_size}</span>
                    {pages_badge}
                    <span>• {chunk_count} vector chunks</span>
                    <span>• Indexed: {created_at}</span>
                </div>
                {warning_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_action:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️", key=f"del_doc_{doc_id}", help="Delete document from ChromaDB & Database"):
            if on_delete:
                on_delete(doc_id)


__all__ = ["render_document_card", "format_file_size"]
