import streamlit as st
from config import config as c
from .api_client import call_service


def render_sign_in_page():
    st.title(c.DASHBOARD_TITLE)
    st.caption(c.DASHBOARD_SUBTITLE)
    if st.session_state.pop("session_ended", False):
        st.warning(c.SESSION_ENDED_MESSAGE)
    with st.form("signin"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in", type="primary")
    if submit:
        st.session_state["user"] = call_service(
            "POST",
            "/auth/signin",
            payload=dict(username=username.strip(), password=password),
        )
        st.rerun()
