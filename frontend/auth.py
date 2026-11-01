"""Streamlit session management, authentication state, and login/registration UI."""

import re
from typing import Any, Dict, Optional
import streamlit as st
from frontend.api_client import api_client
from frontend.config import APP_TITLE, APP_SUBTITLE


def init_session_state() -> None:
    """Ensure all required session state variables are initialized."""
    defaults = {
        "token": None,
        "refresh_token": None,
        "user": None,
        "username": None,
        "email": None,
        "is_admin": False,
        "theme": "dark",
        "current_conversation_id": None,
        "chat_messages": [],
        "navigation_page": "📊 Dashboard",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def is_authenticated() -> bool:
    """Return True if a valid user session is active."""
    return bool(st.session_state.get("token"))


def is_admin() -> bool:
    """Return True if the current user has administrative rights."""
    user = st.session_state.get("user") or {}
    return bool(user.get("is_admin") or user.get("role") == "admin" or st.session_state.get("is_admin"))


def get_current_token() -> Optional[str]:
    """Retrieve the current JWT access token."""
    return st.session_state.get("token")


def get_current_user() -> Dict[str, Any]:
    """Retrieve the current user metadata dict."""
    return st.session_state.get("user") or {}


def set_authenticated_session(token_data: Dict[str, Any]) -> None:
    """Store JWT tokens and user metadata in session state."""
    st.session_state["token"] = token_data.get("access_token")
    st.session_state["refresh_token"] = token_data.get("refresh_token")
    st.session_state["username"] = token_data.get("username")
    st.session_state["email"] = token_data.get("email")

    # Fetch full user profile to get roles and timestamps
    profile_res = api_client.get_me(token_data.get("access_token"))
    if profile_res.get("success"):
        u = profile_res["data"]
        st.session_state["user"] = u
        st.session_state["is_admin"] = bool(u.get("is_admin") or u.get("role") == "admin")
    else:
        st.session_state["user"] = {
            "id": token_data.get("user_id"),
            "username": token_data.get("username"),
            "email": token_data.get("email"),
            "is_admin": False,
            "role": "user"
        }
        st.session_state["is_admin"] = False


def logout() -> None:
    """Clear user session and reset navigation."""
    st.session_state["token"] = None
    st.session_state["refresh_token"] = None
    st.session_state["user"] = None
    st.session_state["username"] = None
    st.session_state["email"] = None
    st.session_state["is_admin"] = False
    st.session_state["current_conversation_id"] = None
    st.session_state["chat_messages"] = []
    st.session_state["navigation_page"] = "📊 Dashboard"
    st.rerun()


def render_auth_form() -> None:
    """Render a polished, modern login and registration interface."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%); border-radius: 14px; margin-bottom: 1rem; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);">
                    <span style="font-size: 1.8rem;">🧠</span>
                </div>
                <h2 style="margin: 0; font-weight: 700; color: #F8FAFC;">{APP_TITLE}</h2>
                <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.9rem;">{APP_SUBTITLE}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        auth_tab = st.radio(
            "Auth Option",
            ["🔑 Sign In", "✨ Create Account"],
            horizontal=True,
            label_visibility="collapsed"
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        if auth_tab == "🔑 Sign In":
            with st.form("login_form", clear_on_submit=False):
                username_or_email = st.text_input("Username or Email", placeholder="e.g. alice@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if submit:
                    if not username_or_email or not password:
                        st.error("Please enter both username/email and password.")
                    else:
                        with st.spinner("Authenticating credentials..."):
                            res = api_client.login(username_or_email, password)
                            if res.get("success"):
                                set_authenticated_session(res["data"])
                                st.success("Login successful! Welcome back.")
                                st.rerun()
                            else:
                                st.error(res.get("error", "Incorrect username or password."))

        else:
            with st.form("register_form", clear_on_submit=False):
                new_username = st.text_input("Username", placeholder="e.g. john_doe")
                new_email = st.text_input("Email Address", placeholder="e.g. john@example.com")
                new_password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")

                if submit:
                    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                    if not new_username or len(new_username.strip()) < 3:
                        st.error("Username must be at least 3 characters long.")
                    elif not new_email or not re.match(email_pattern, new_email.strip()):
                        st.error("Please enter a valid email address.")
                    elif not new_password or len(new_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        with st.spinner("Creating your account..."):
                            reg_res = api_client.register(new_username, new_email, new_password)
                            if reg_res.get("success"):
                                # Automatic login upon successful registration
                                log_res = api_client.login(new_username, new_password)
                                if log_res.get("success"):
                                    set_authenticated_session(log_res["data"])
                                    st.success("Account created successfully! Logging in...")
                                    st.rerun()
                                else:
                                    st.success("Account created! Please sign in using the Sign In tab.")
                            else:
                                st.error(reg_res.get("error", "Registration failed."))


def require_auth(admin_only: bool = False) -> Optional[Dict[str, Any]]:
    """
    Enforce authentication guard for pages.
    Renders login screen if unauthenticated or error if admin_only check fails.
    """
    init_session_state()

    if not is_authenticated():
        render_auth_form()
        st.stop()
        return None

    if admin_only and not is_admin():
        st.error("🛡️ **Access Denied**: Administrative privileges are required to view this page.")
        st.info("Please log in with an administrator account to view system analytics and controls.")
        st.stop()
        return None

    return get_current_user()


__all__ = [
    "init_session_state",
    "is_authenticated",
    "is_admin",
    "get_current_token",
    "get_current_user",
    "set_authenticated_session",
    "logout",
    "render_auth_form",
    "require_auth",
]
