"""Dark Emerald Glassmorphic Citation Viewer."""

from typing import Any, Dict, List
import streamlit as st
from frontend.config import FILE_ICONS


def render_citation_viewer(sources: List[Dict[str, Any]], title: str = "Sources") -> None:
    """Render glowing emerald citation references."""
    if not sources:
        return

    with st.expander(f"📚 {title} ({len(sources)} grounded chunks)", expanded=False):
        for idx, src in enumerate(sources, 1):
            filename = src.get("filename", "document.pdf")
            page_number = src.get("page_number")
            chunk_index = src.get("chunk_index", 0)
            score = src.get("score")
            excerpt = src.get("excerpt", "").strip()

            ext = filename.split(".")[-1].lower() if "." in filename else "txt"
            icon = FILE_ICONS.get(ext, "📄")

            page_str = f"Page {page_number}" if page_number is not None and int(page_number) > 0 else "Doc Excerpt"
            score_str = f" • Similarity: {float(score):.2f}" if score is not None else ""

            badge_color = "#EF4444" if ext == "pdf" else ("#3B82F6" if ext == "docx" else "#8B5CF6")

            st.markdown(
                f"""
                <div style="background: rgba(14, 25, 19, 0.75); border: 1px solid rgba(0, 242, 152, 0.2); border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="font-weight: 600; font-size: 0.88rem; color: #FFFFFF; display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 1rem;">{icon}</span>
                            <span>{filename}</span>
                            <span style="font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; background: rgba(0, 242, 152, 0.15); color: #00F298; border: 1px solid rgba(0, 242, 152, 0.3);">
                                {ext.upper()}
                            </span>
                        </div>
                        <span style="font-size: 0.75rem; color: #00F298; font-weight: 600;">{page_str}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">
                        Chunk {chunk_index}{score_str}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if excerpt:
                with st.expander(f"🔍 Excerpt from {filename} (Chunk {chunk_index})", expanded=False):
                    st.markdown(
                        f"""
                        <div style="background: rgba(6, 10, 8, 0.9); border-left: 3px solid #00F298; padding: 10px 14px; border-radius: 4px; font-size: 0.82rem; color: #CBD5E1; font-family: monospace;">
                            {excerpt}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


__all__ = ["render_citation_viewer"]
