import requests
import streamlit as st
from config import config as c


def call_service(method, path, query=None, payload=None, waiting_message=None):
    headers = (
        {c.SESSION_TOKEN_HEADER: st.session_state["user"]["session_token"]}
        if st.session_state.get("user")
        else {}
    )

    def perform():
        return requests.request(
            method,
            c.API_BASE_URL + path,
            params=query,
            json=payload,
            headers=headers,
            timeout=c.API_REQUEST_TIMEOUT_SECONDS,
        )

    try:
        if waiting_message:
            with st.spinner(waiting_message, show_time=True):
                reply = perform()
        else:
            reply = perform()
    except requests.RequestException as error:
        st.error(f"Service unavailable at {c.API_BASE_URL}: {error}")
        st.stop()
    if reply.status_code == 401 and st.session_state.get("user"):
        st.session_state.clear()
        st.session_state["session_ended"] = True
        st.rerun()
    if reply.status_code >= 400:
        try:
            detail = reply.json().get("detail", reply.text)
        except ValueError:
            detail = f"{reply.status_code}: {reply.text}"
        st.error(detail)
        st.stop()
    return reply.json()
