"""AI Knowledge Assistant - Streamlit Frontend Application Entrypoint."""

import streamlit as st
from frontend.components.auth_ui import render_auth_view
from frontend.components.sidebar import render_sidebar
from frontend.components.doc_ui import render_documents_view
from frontend.components.chat_ui import render_chat_view
from frontend.components.dashboard_ui import render_dashboard_view
from frontend.components.history_ui import render_history_view
from frontend.components.settings_ui import render_settings_view

# Page Configuration
st.set_page_config(
    page_title="AI Knowledge Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Polished Modern SaaS Styling (CSS)
st.markdown(
    """
    <style>
    /* Global Background and Typography */
    .stApp {
        background-color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #0F172A;
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #0F172A !important;
        letter-spacing: -0.02em;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.15s ease-in-out;
    }
    .stButton > button[kind="primary"] {
        background-color: #2563EB;
        color: white;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8;
    }

    /* Input Fields */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
    }
    .stTextInput > div > div > input:focus {
        border-color: #2563EB;
        box-shadow: 0 0 0 1px #2563EB;
    }

    /* Chat Messages */
    .stChatMessage {
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #334155;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def main():
    token = st.session_state.get("token")

    # If user is not authenticated, show Auth View
    if not token:
        render_auth_view()
        return

    # Render Sidebar and retrieve active page
    selected_page = render_sidebar()

    # Route view based on selection
    if selected_page == "💬 AI Chat":
        render_chat_view(token)
    elif selected_page == "📁 Documents":
        render_documents_view(token)
    elif selected_page == "📊 Dashboard":
        render_dashboard_view(token)
    elif selected_page == "🕒 Chat History":
        render_history_view(token)
    elif selected_page == "⚙️ Settings":
        render_settings_view(token)


if __name__ == "__main__":
    main()
