import requests
import streamlit as st
from config import config as c
from dashboard.sign_in import render_sign_in_page
from dashboard.review_queue import render_review_queue_page
from dashboard.request_detail import render_request_detail_page
from dashboard.decision_queue import render_decision_queue_page
from dashboard.audit_trail import render_audit_trail_page
from dashboard.authorisation_chat import render_authorisation_chat_page
from dashboard.api_client import call_service

PAGE_RENDERERS = {
    c.PAGE_QUEUE: render_review_queue_page,
    c.PAGE_DETAIL: render_request_detail_page,
    c.PAGE_DECISION: render_decision_queue_page,
    c.PAGE_AUDIT: render_audit_trail_page,
    c.PAGE_CHAT: render_authorisation_chat_page,
}
PAGE_ICONS = {
    c.PAGE_QUEUE: ":material/list_alt:",
    c.PAGE_DETAIL: ":material/description:",
    c.PAGE_DECISION: ":material/fact_check:",
    c.PAGE_AUDIT: ":material/history:",
    c.PAGE_CHAT: ":material/chat:",
}
PAGE_URL_PATHS = {name: name.lower().replace(" ", "-") for name in PAGE_RENDERERS}


def main():
    st.set_page_config(
        page_title=c.DASHBOARD_TITLE,
        page_icon=":material/health_and_safety:",
        layout="wide",
    )
    try:
        requests.get(c.API_BASE_URL + "/openapi.json", timeout=3).raise_for_status()
    except requests.RequestException:
        st.error(
            f"Service not answering at {c.API_BASE_URL}. Start it with python run_api_service.py."
        )
        return
    if not st.session_state.get("user"):
        render_sign_in_page()
        return
    user = st.session_state["user"]
    with st.sidebar:
        st.title(c.DASHBOARD_TITLE)
        st.write(user["display_name"])
        st.caption(user["role"])
        if st.button("Sign out"):
            call_service("POST", "/auth/signout")
            st.session_state.clear()
            st.rerun()
    pages = [
        st.Page(
            PAGE_RENDERERS[name],
            title=name,
            icon=PAGE_ICONS[name],
            url_path=PAGE_URL_PATHS[name],
        )
        for name in user["pages"]
    ]
    st.navigation(pages).run()


if __name__ == "__main__":
    main()
