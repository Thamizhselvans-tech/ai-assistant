"""Source citation viewer with provenance badges, page references, and excerpts."""

from typing import Any, Dict, List, Optional
import streamlit as st
from frontend.config import FILE_ICONS


def render_citation_viewer(sources: List[Dict[str, Any]], title: str = "📚 Source References & Grounding Citations") -> None:
    """
    Render structured source citations for an AI response.
    Explicitly distinguishes physical PDF page numbers from non-paged documents (DOCX/TXT).
    """
    if not sources:
        st.markdown(
            """
            <div style="background: rgba(100, 116, 139, 0.1); border-left: 3px solid #64748B; padding: 10px 14px; border-radius: 0 8px 8px 0; margin-top: 10px; font-size: 0.85rem; color: #94A3B8;">
                ℹ️ <em>No relevant supporting document excerpts were cited for this response.</em>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    with st.expander(f"{title} ({len(sources)} cited)", expanded=False):
        for idx, src in enumerate(sources, 1):
            filename = src.get("filename", "Unknown Document")
            page_number = src.get("page_number")
            chunk_index = src.get("chunk_index", 0)
            score = src.get("score")
            excerpt = src.get("excerpt", "").strip()

            # Extension icon
            ext = filename.split(".")[-1].lower() if "." in filename else "txt"
            icon = FILE_ICONS.get(ext, "📄")

            # Page provenance
            if page_number is not None and int(page_number) > 0:
                page_badge = f'<span style="background: rgba(59, 130, 246, 0.15); color: #60A5FA; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">Page {page_number}</span>'
            else:
                page_badge = '<span style="background: rgba(100, 116, 139, 0.15); color: #94A3B8; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">No Page Info (Text/DOCX)</span>'

            # Relevance Score
            score_badge = ""
            if score is not None:
                score_pct = float(score) * 100
                score_color = "#10B981" if score_pct >= 70 else "#3B82F6" if score_pct >= 50 else "#F59E0B"
                score_badge = f'<span style="background: rgba(16, 185, 129, 0.15); color: {score_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">Match: {score_pct:.1f}%</span>'

            st.markdown(
                f"""
                <div style="background: #161F30; border: 1px solid #27354A; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                        <div style="font-weight: 600; font-size: 0.88rem; color: #F8FAFC; display: flex; align-items: center; gap: 6px;">
                            <span>{icon}</span> <span>{filename}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            {page_badge}
                            {score_badge}
                            <span style="font-size: 0.72rem; color: #64748B;">Chunk #{chunk_index}</span>
                        </div>
                    </div>
                    <div class="citation-box">
                        "{excerpt}"
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


__all__ = ["render_citation_viewer"]
