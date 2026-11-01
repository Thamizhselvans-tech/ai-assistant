"""Chat message rendering component for conversational dialogue."""

from typing import Any, Dict, List, Optional
import streamlit as st
from frontend.components.citation_viewer import render_citation_viewer


def render_chat_message(role: str, content: str, sources: Optional[List[Dict[str, Any]]] = None, message_id: Optional[str] = None) -> None:
    """Render a conversation message bubble with citations and actions."""
    if role == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(content)
    else:
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(content)
            if sources:
                render_citation_viewer(sources)


__all__ = ["render_chat_message"]
