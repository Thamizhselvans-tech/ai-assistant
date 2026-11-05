"""Minimalist ChatGPT-style source citation component."""

from typing import Any, Dict, List
import streamlit as st
from frontend.config import FILE_ICONS


def render_citation_viewer(sources: List[Dict[str, Any]], title: str = "Sources") -> None:
    """Render clean, minimal citation references matching ChatGPT interface."""
    if not sources:
        return

    with st.expander(f"📚 {title} ({len(sources)})", expanded=True):
        for idx, src in enumerate(sources, 1):
            filename = src.get("filename", "document.pdf")
            page_number = src.get("page_number")
            chunk_index = src.get("chunk_index", 0)
            score = src.get("score")
            excerpt = src.get("excerpt", "").strip()

            ext = filename.split(".")[-1].lower() if "." in filename else "txt"
            icon = FILE_ICONS.get(ext, "📄")

            page_str = f"Page {page_number}" if page_number is not None and int(page_number) > 0 else "Doc Excerpt"
            score_str = f" • Relevance: {float(score):.2f}" if score is not None else ""

            st.markdown(
                f"""
                <div class="chatgpt-source-item">
                    <div style="font-weight: 500; font-size: 0.86rem; display: flex; align-items: center; gap: 8px;">
                        <span>{icon}</span> <span>{filename}</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #8E8E8E;">
                        {page_str}, Chunk {chunk_index}{score_str} <span style="cursor: pointer; margin-left: 4px;">↗</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if excerpt:
                with st.expander(f"Preview Chunk {chunk_index}", expanded=False):
                    st.caption(excerpt)


__all__ = ["render_citation_viewer"]
