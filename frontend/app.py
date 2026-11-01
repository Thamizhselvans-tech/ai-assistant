"""AI Knowledge Assistant - Streamlit Frontend Application Entrypoint."""

import streamlit as st
from frontend.config import inject_custom_css, APP_TITLE
from frontend.auth import init_session_state, is_authenticated, render_auth_form
from frontend.components.sidebar import render_sidebar
from frontend.components.dashboard_ui import render_dashboard_view
from frontend.components.doc_ui import render_documents_view
from frontend.components.chat_ui import render_chat_view
from frontend.components.history_ui import render_history_view
from frontend.components.admin_ui import render_admin_view
from frontend.components.settings_ui import render_settings_view

# Page Configuration
st.set_page_config(
    page_title=f"{APP_TITLE} - Enterprise RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom SaaS Design System
inject_custom_css()

# Initialize Session State
init_session_state()


def main():
    """Main application router."""
    if not is_authenticated():
        render_auth_form()
        return

    # Render Sidebar and retrieve active page
    selected_page = render_sidebar()
    token = st.session_state.get("token")

    # Route view based on sidebar selection
    if selected_page == "📊 Dashboard":
        render_dashboard_view(token)
    elif selected_page == "📁 Documents":
        render_documents_view(token)
    elif selected_page == "💬 AI Chat":
        render_chat_view(token)
    elif selected_page == "🕒 Chat History":
        render_history_view(token)
    elif selected_page == "🛡️ Admin":
        render_admin_view(token)
    elif selected_page == "⚙️ Settings":
        render_settings_view(token)
    else:
        render_dashboard_view(token)


if __name__ == "__main__":
    main()
