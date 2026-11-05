"""Authentication UI component for Streamlit."""

import streamlit as st
from frontend.services.api_client import api_client


def render_auth_view():
    """Render Login and Registration views."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-weight: 800; font-size: 2.2rem; background: linear-gradient(90deg, #10B981 0%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; display: inline-block;">AI Knowledge Assistant</h1>
            <p style="color: #64748B; font-size: 1.1rem;">Enterprise-grade Retrieval-Augmented Generation (RAG) platform</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])

        with tab_login:
            st.markdown("### Welcome Back")
            st.markdown("<p style='color: #64748B; font-size: 0.9rem;'>Sign in to access your knowledge base and conversations.</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                login_id = st.text_input("Username or Email", placeholder="e.g. alex@example.com")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

                if submitted:
                    if not login_id or not password:
                        st.error("Please enter both username/email and password.")
                    else:
                        with st.spinner("Authenticating..."):
                            res = api_client.login(login_id, password)
                            if res.get("success"):
                                data = res["data"]
                                st.session_state["token"] = data["access_token"]
                                st.session_state["user_id"] = data["user_id"]
                                st.session_state["username"] = data["username"]
                                st.session_state["email"] = data["email"]
                                st.success(f"Welcome back, {data['username']}!")
                                st.rerun()
                            else:
                                st.error(res.get("error", "Invalid credentials."))

        with tab_register:
            st.markdown("### Create an Account")
            st.markdown("<p style='color: #64748B; font-size: 0.9rem;'>Get started with your private, secure AI document assistant.</p>", unsafe_allow_html=True)
            with st.form("register_form"):
                new_username = st.text_input("Username", placeholder="e.g. alex_smith")
                new_email = st.text_input("Email Address", placeholder="e.g. alex@example.com")
                new_password = st.text_input("Password (min 6 chars)", type="password", placeholder="Create a secure password")
                new_password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

                if reg_submitted:
                    if not new_username or not new_email or not new_password:
                        st.error("All fields are required.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif new_password != new_password_confirm:
                        st.error("Passwords do not match.")
                    else:
                        with st.spinner("Creating account..."):
                            res = api_client.register(new_username, new_email, new_password)
                            if res.get("success"):
                                st.success("Account created successfully! Please sign in using the Sign In tab.")
                            else:
                                st.error(res.get("error", "Registration failed."))
