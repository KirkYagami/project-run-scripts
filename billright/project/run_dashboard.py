"""The dashboard: signing in, the navigation and the five pages. Run with:
    streamlit run run_dashboard.py
"""
import time

import requests
import streamlit as st

from config import config
from dashboard.api_client import call_service
from dashboard.audit_trail import render_audit_trail_page
from dashboard.billing_chat import render_billing_chat_page
from dashboard.decision_queue import render_decision_queue_page
from dashboard.dispute_detail import render_dispute_detail_page
from dashboard.dispute_queue import render_dispute_queue_page

PAGE_RENDERERS = {
    config.PAGE_QUEUE: (render_dispute_queue_page, "📋"),
    config.PAGE_DISPUTE: (render_dispute_detail_page, "🔎"),
    config.PAGE_DECISION: (render_decision_queue_page, "⚖️"),
    config.PAGE_AUDIT: (render_audit_trail_page, "🧾"),
    config.PAGE_CHAT: (render_billing_chat_page, "💬"),
}


def _service_is_answering():
    try:
        requests.get(config.API_BASE_URL + "/docs", timeout=5)
        return True
    except requests.RequestException:
        return False


def main():
    """Draw the dashboard, with only the pages the signed-in person's role is offered."""
    st.set_page_config(page_title=config.DASHBOARD_TITLE, layout="wide")
    if not _service_is_answering():
        st.error(f"The service is not answering at {config.API_BASE_URL}. Start it with: "
                 f"python run_api_service.py")
        st.stop()

    if "session_token" not in st.session_state:
        st.title(config.DASHBOARD_TITLE)
        st.caption(config.DASHBOARD_SUBTITLE)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign in"):
            signed_in = call_service("POST", "/auth/signin", None,
                                     {"username": username, "password": password}, None)
            session_token = signed_in.get("session_token")
            # Do not create a logged-in frontend session without a token: protected
            # API calls would otherwise fail and leave the dashboard unusable.
            if not isinstance(session_token, str) or not session_token.strip():
                st.error("Login failed: the server did not issue a session token. Please try again.")
                st.stop()
            for key in ("username", "display_name", "role", "session_token", "pages"):
                st.session_state[key] = signed_in[key]
            st.rerun()
        return

    st.sidebar.title(config.DASHBOARD_TITLE)
    st.sidebar.write(f"{st.session_state['display_name']}")
    st.sidebar.caption(st.session_state["role"])
    if st.sidebar.button("Sign out"):
        call_service("POST", "/auth/signout", None, None, None)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    pages = st.session_state["pages"]
    page = st.sidebar.radio("Pages", pages, format_func=lambda name: f"{PAGE_RENDERERS[name][1]} {name}")
    st.session_state[config.PAGE_LOAD_STARTED_AT_KEY] = time.monotonic()
    try:
        PAGE_RENDERERS[page][0]()
    finally:
        st.session_state.pop(config.PAGE_LOAD_STARTED_AT_KEY, None)


if __name__ == "__main__":
    main()
