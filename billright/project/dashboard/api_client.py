"""Every request the dashboard sends to the service passes through this module."""
import threading
import time

import requests
import streamlit as st

from config import config


def _show_failure(reply):
    try:
        detail = reply.json().get("detail", reply.text)
    except ValueError:
        detail = f"{reply.status_code}: {reply.text}"
    if not isinstance(detail, str):
        detail = str(detail)
    st.error(detail)
    st.stop()


def _show_invalid_response():
    """Stop the page cleanly when a successful HTTP response has no usable JSON body."""
    st.error("The service returned an invalid or empty response. Please try again.")
    st.stop()


def _show_slow_page_notice(placeholder):
    """Reassure the user when page data is still loading after the normal wait time."""
    with placeholder.container(border=True):
        st.subheader("Still loading your page")
        st.write("This is taking longer than expected, but the request is still being processed.")
        st.caption("Please keep this page open. The result will appear automatically when it is ready.")


def call_service(method, path, query, payload, waiting_message):
    """Make one call to the service, carrying the signed-in person's token whenever there is one."""
    headers = {}
    token = st.session_state.get("session_token")
    if token:
        headers[config.SESSION_TOKEN_HEADER] = token
    outcome = {}

    def send():
        try:
            outcome["reply"] = requests.request(
                method, config.API_BASE_URL + path, params=query, json=payload, headers=headers,
                timeout=config.API_REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as error:
            outcome["error"] = error

    worker = threading.Thread(target=send, daemon=True)
    started = time.monotonic()
    worker.start()
    progress = st.empty()
    slow_page_notice = st.empty()
    page_started = st.session_state.get(config.PAGE_LOAD_STARTED_AT_KEY, started)
    slow_notice_shown = False

    def wait_for_reply():
        nonlocal slow_notice_shown
        while worker.is_alive():
            if waiting_message:
                progress.caption(f"{waiting_message} ({int(time.monotonic() - started)} s)")
            if (not slow_notice_shown and
                    time.monotonic() - page_started >= config.SLOW_PAGE_NOTICE_SECONDS):
                _show_slow_page_notice(slow_page_notice)
                slow_notice_shown = True
            time.sleep(0.5)

    if waiting_message:
        with st.spinner(waiting_message):
            wait_for_reply()
    else:
        wait_for_reply()
    worker.join()
    progress.empty()
    slow_page_notice.empty()
    if "error" in outcome:
        st.error(f"The service at {config.API_BASE_URL} did not answer: {outcome['error']}")
        st.stop()
    reply = outcome["reply"]
    if reply.status_code >= 400:
        _show_failure(reply)
    try:
        response_data = reply.json()
    except ValueError:
        _show_invalid_response()
    # Every successful endpoint in this dashboard returns a populated object or a list.
    # An empty list is valid (for example, a queue with no matching disputes).
    if response_data is None or response_data == "" or response_data == {}:
        _show_invalid_response()
    return response_data
