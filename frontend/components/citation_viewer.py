"""Source citation viewer component matching enterprise SaaS card layout."""

from typing import Any, Dict, List
import streamlit as st
from frontend.config import FILE_ICONS


def render_citation_viewer(sources: List[Dict[str, Any]], title: str = "Sources (Citations)") -> None:
    """Render modern citation cards matching the reference screenshot."""
    if not sources:
        return

    with st.expander(f"📚 {title}", expanded=True):
        for idx, src in enumerate(sources, 1):
            filename = src.get("filename", "document.pdf")
            page_number = src.get("page_number")
            chunk_index = src.get("chunk_index", 0)
            score = src.get("score")
            excerpt = src.get("excerpt", "").strip()

            ext = filename.split(".")[-1].lower() if "." in filename else "txt"
            icon = FILE_ICONS.get(ext, "📄")

            # Format page string
            page_str = f"Page {page_number}" if page_number is not None and int(page_number) > 0 else "Document Excerpt"
            score_str = f" | Relevance: {float(score):.2f}" if score is not None else ""

            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="font-weight: 700; font-size: 0.9rem; color: #1E293B; display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 1.1rem;">{icon}</span> <span>{filename}</span>
                        </div>
                        <span style="font-size: 1rem; color: #64748B; cursor: pointer;">↗</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 4px;">
                        {page_str}, Chunk {chunk_index}{score_str}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Show excerpt if expanded or clicked
            if excerpt:
                with st.expander(f"View Excerpt for Chunk {chunk_index}", expanded=False):
                    st.caption(excerpt)


__all__ = ["render_citation_viewer"]
