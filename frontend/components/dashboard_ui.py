"""Premium Emerald Dark UI Dashboard Component matching the reference UI."""

import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import streamlit as st
from frontend.api_client import api_client
from frontend.config import BACKEND_API_URL
from frontend.components.header import render_header
from frontend.components.document_card import format_file_size
from frontend.components.chat_composer import render_chat_composer

_MASCOT_B64_CACHE: Optional[str] = None


def get_mascot_base64() -> str:
    """Retrieve base64-encoded mascot illustration with in-memory caching."""
    global _MASCOT_B64_CACHE
    if _MASCOT_B64_CACHE:
        return _MASCOT_B64_CACHE
    assets_dir = Path(__file__).parent.parent / "assets"
    for fname in ["ai_mascot.png", "ai_mascot.jpg"]:
        p = assets_dir / fname
        if p.exists():
            try:
                _MASCOT_B64_CACHE = base64.b64encode(p.read_bytes()).decode("utf-8")
                return _MASCOT_B64_CACHE
            except Exception:
                pass
    return ""


def format_relative_time(dt_str: Optional[str]) -> str:
    """Format ISO timestamp into relative time string (e.g. '2 days ago', 'Today')."""
    if not dt_str:
        return "Recently"
    try:
        clean = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        diff = datetime.now() - dt.replace(tzinfo=None)
        if diff.days == 0:
            return "Today"
        elif diff.days == 1:
            return "1 day ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = max(1, diff.days // 7)
            return f"{weeks}w ago"
        else:
            return dt.strftime("%b %d")
    except Exception:
        return "Recently"


def render_dashboard_view(token: str, on_query_submit: Optional[Callable[[str], None]] = None):
    """Render complete dashboard matching the reference screenshot."""
    render_header()

    # Query live documents and stats
    docs_res = api_client.list_documents(token) if token else {"success": False}
    live_docs = docs_res.get("data", {}).get("documents", []) if docs_res.get("success") else []
    
    # 2-Column Responsive SaaS Grid (Left: Hero & Actions, Right: Widgets)
    col_main, col_sidebar = st.columns([13, 7], gap="large")

    # =========================================================================
    # LEFT COLUMN: Hero Banner, 4 Action Cards, Capsule Input, Suggestion Pills
    # =========================================================================
    with col_main:
        # 1. Main Headings
        st.markdown(
            """
            <div class="hero-container">
                <div class="hero-title">AI Knowledge Assistant</div>
                <div class="hero-subtitle">Ask • Upload • Analyze • Learn</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. 3D Mascot Banner
        mascot_b64 = get_mascot_base64()
        if mascot_b64:
            st.markdown(
                f"""
                <div class="mascot-banner-card">
                    <img src="data:image/png;base64,{mascot_b64}" alt="AI Mascot" />
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # High-tech SVG Mascot Fallback
            st.markdown(
                """
                <div class="mascot-banner-card" style="padding: 40px 20px; text-align: center;">
                    <div style="font-size: 4rem; filter: drop-shadow(0 0 20px #00F298);">🤖</div>
                    <div style="font-size: 1.1rem; color: #00F298; font-weight: 700; margin-top: 8px;">AI Companion Active</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # 3. 4 Action Cards
        ac1, ac2, ac3, ac4 = st.columns(4)
        with ac1:
            if st.button("💬 Ask Anything\n\nGet answers in Tamil or English", key="dash_card_ask", use_container_width=True):
                st.session_state["prompt_input"] = "Explain the key concepts and architecture from my documents."
                st.session_state["navigation_page"] = "💬 Chat Assistant"
                st.rerun()
        with ac2:
            if st.button("📄 Upload Documents\n\nPDF, DOCX, TXT, etc.", key="dash_card_upload", use_container_width=True):
                st.info("💡 Click the 📎 paperclip icon on the left of the composer, or drag & drop files into the Upload Document widget on the right!")
        with ac3:
            if st.button("📋 Summarize\n\nGet key points instantly", key="dash_card_sum", use_container_width=True):
                st.session_state["prompt_input"] = "Please provide an executive summary of the uploaded documents."
                st.session_state["navigation_page"] = "💬 Chat Assistant"
                st.rerun()
        with ac4:
            if st.button("💡 Learn & Explore\n\nUnderstand concepts with examples", key="dash_card_learn", use_container_width=True):
                st.session_state["prompt_input"] = "Explain the most important topics from my documents with clear real-world examples."
                st.session_state["navigation_page"] = "💬 Chat Assistant"
                st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 4. Functional Emerald Chat Composer Component
        initial_prompt = st.session_state.pop("prompt_input", None)
        composer_event = render_chat_composer(
            token=token or "",
            api_url=BACKEND_API_URL,
            conversation_id=st.session_state.get("active_conversation_id"),
            initial_text=initial_prompt or "",
            key="dashboard_active_composer"
        )

        # Process events from custom composer
        if composer_event and isinstance(composer_event, dict):
            action = composer_event.get("action")
            ts = composer_event.get("ts", 0)

            if action == "send":
                text = (composer_event.get("text") or "").strip()
                if text and ts != st.session_state.get("last_dash_composer_ts"):
                    st.session_state["last_dash_composer_ts"] = ts
                    st.session_state["prompt_input"] = text
                    st.session_state["navigation_page"] = "💬 Chat Assistant"
                    st.rerun()

            elif action == "uploaded":
                fname = composer_event.get("filename")
                if fname and ts != st.session_state.get("last_dash_upload_ts"):
                    st.session_state["last_dash_upload_ts"] = ts
                    st.session_state["last_uploaded_doc"] = {
                        "filename": fname,
                        "pages": composer_event.get("pages", 0),
                        "chunks": composer_event.get("chunks", 0),
                        "status": composer_event.get("status", "completed")
                    }
                    st.rerun()

        # 5. "Try asking" Suggestion Pills
        st.markdown("<div class='try-asking-wrapper'><span class='try-asking-label'>Try asking:</span></div>", unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            if st.button("🍃 Machine Learning na enna?", key="pill_ml_tanglish", use_container_width=True):
                st.session_state["prompt_input"] = "Machine Learning na enna?"
                st.session_state["navigation_page"] = "💬 Chat Assistant"
                st.rerun()
        with p2:
            if st.button("📖 DBMS Normalization", key="pill_dbms", use_container_width=True):
                st.session_state["prompt_input"] = "What is DBMS Normalization? Explain 1NF, 2NF, and 3NF with examples."
                st.session_state["navigation_page"] = "💬 Chat Assistant"
                st.rerun()
        with p3:
            if st.button("📊 இந்த PDF-ஐ சுருக்கவும்", key="pill_tamil_sum", use_container_width=True):
                st.session_state["prompt_input"] = "இந்த PDF-ஐ சுருக்கமாக தமிழில் விளக்கவும்."
                st.session_state["navigation_page"] = "💬 Chat Assistant"
                st.rerun()
        with p4:
            if st.button("</> Give an example", key="pill_example", use_container_width=True):
                st.session_state["prompt_input"] = "Give a practical code example illustrating the concepts in my documents."
                st.session_state["navigation_page"] = "💬 Chat Assistant"
                st.rerun()

    # =========================================================================
    # RIGHT COLUMN: Upload Widget, Recent Documents, Usage Progress Ring
    # =========================================================================
    with col_sidebar:
        # WIDGET 1: Consolidated Single Upload Widget
        st.markdown(
            """
            <div class="widget-card" style="padding-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span style="font-size: 1.2rem; color: #00F298;">☁️</span>
                    <div>
                        <div style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem;">Upload Document</div>
                        <div style="font-size: 0.78rem; color: #94A3B8;">Drag & drop or browse PDF, DOCX, TXT (Max 50 MB)</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        uploaded_files = st.file_uploader(
            "Upload Document",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="dashboard_drag_drop_uploader",
            label_visibility="collapsed"
        )

        if uploaded_files:
            for uf in uploaded_files:
                fname = uf.name
                fbytes = uf.getvalue()
                if len(fbytes) > 0:
                    with st.spinner(f"Indexing '{fname}' into RAG ChromaDB..."):
                        res = api_client.upload_document(fbytes, fname, token)
                        if res.get("success"):
                            st.success(f"✅ Indexed **{fname}** successfully!")
                            st.session_state["last_uploaded_doc"] = {
                                "filename": fname,
                                "chunks": res.get("data", {}).get("chunk_count", 0),
                                "status": "completed"
                            }
                        else:
                            st.error(f"❌ Upload failed: {res.get('error')}")

        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        # WIDGET 2: Recent Documents List
        st.markdown(
            """
            <div class="widget-card">
                <div class="widget-title-row">
                    <div class="widget-title">Recent Documents</div>
                    <a class="widget-link" href="#" onclick="return false;">View All →</a>
                </div>
            """,
            unsafe_allow_html=True
        )

        # Prepare list of items (using live documents or default showcase items if empty)
        display_items: List[Dict[str, Any]] = []
        if live_docs:
            for d in live_docs[:4]:
                ext = d.get("file_type", "txt").lower()
                display_items.append({
                    "name": d.get("filename", "Document"),
                    "ext": ext,
                    "size": format_file_size(d.get("file_size_bytes", 0)),
                    "time": format_relative_time(d.get("created_at")),
                })
        else:
            # Fallback showcase matching reference screenshot
            display_items = [
                {"name": "Smart_Bus_Business...", "ext": "pdf", "size": "2.4 MB", "time": "2 days ago"},
                {"name": "Project_Proposal.docx", "ext": "docx", "size": "1.1 MB", "time": "3 days ago"},
                {"name": "TNSCST_Guidelines.pdf", "ext": "pdf", "size": "3.8 MB", "time": "4 days ago"},
                {"name": "Notes_Algorithms.txt", "ext": "txt", "size": "156 KB", "time": "5 days ago"},
            ]

        for item in display_items:
            ext = item["ext"]
            badge_cls = f"doc-badge-{ext}" if ext in ["pdf", "docx", "txt"] else "doc-badge-txt"
            st.markdown(
                f"""
                <div class="recent-doc-item">
                    <span class="doc-badge {badge_cls}">{ext.upper()}</span>
                    <div class="recent-doc-info">
                        <div class="recent-doc-name" title="{item['name']}">{item['name']}</div>
                        <div class="recent-doc-meta">{item['size']} • {item['time']}</div>
                    </div>
                    <div class="recent-doc-menu">⋮</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # WIDGET 3: Your Usage (This Month) Progress Ring
        st.markdown(
            """
            <div class="widget-card">
                <div class="widget-title" style="margin-bottom: 12px;">Your Usage (This Month)</div>
                <div class="usage-widget-body">
                    <svg class="usage-ring-svg" viewBox="0 0 36 36">
                        <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="rgba(255, 255, 255, 0.08)"
                            stroke-width="3"
                        />
                        <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#00F298"
                            stroke-width="3"
                            stroke-dasharray="68, 100"
                            stroke-linecap="round"
                            style="filter: drop-shadow(0 0 6px #00F298);"
                        />
                        <text x="18" y="20.5" font-size="7.5" font-weight="bold" fill="#FFFFFF" text-anchor="middle">68%</text>
                    </svg>
                    <div class="usage-metric-details">
                        <div class="usage-query-stat">42 / 100 Queries</div>
                        <div class="usage-progress-track">
                            <div class="usage-progress-fill" style="width: 68%;"></div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


__all__ = ["render_dashboard_view", "get_mascot_base64"]
