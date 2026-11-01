"""Chat History Multi-Page view."""

import streamlit as st
from frontend.auth import require_auth, init_session_state
from frontend.components.sidebar import render_sidebar
from frontend.components.history_ui import render_history_view
from frontend.config import inject_custom_css

st.set_page_config(
    page_title="Chat History - AI Knowledge Assistant",
    page_icon="🕒",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_css()
init_session_state()
user = require_auth()
render_sidebar()
token = st.session_state.get("token")
render_history_view(token)
