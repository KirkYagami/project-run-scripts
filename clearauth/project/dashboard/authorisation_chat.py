import streamlit as st
from config import config as c
from .api_client import call_service
from .components import badge


def render_authorisation_chat_page():
    st.title(c.PAGE_CHAT)
    st.caption(
        "Answers grounded in Brightwater policies and authorised review records."
    )
    turns = call_service(
        "GET", "/chat/turns", query={"turn_limit": c.CHAT_PAGE_TURN_LIMIT}
    )
    for turn in reversed(turns):
        with st.chat_message("user"):
            st.write(turn["question_text"])
        with st.chat_message("assistant"):
            badge(turn["question_type"], c.CHAT_TYPE_BADGE_COLOURS)
            st.write(turn["answer_text"])
            if turn["source_documents"]:
                st.caption("Sources: " + turn["source_documents"])
    question = st.chat_input(
        "Ask about a policy or request", max_chars=c.CHAT_QUESTION_MAXIMUM_CHARACTERS
    )
    if question:
        if len(question.strip()) < c.CHAT_QUESTION_MINIMUM_CHARACTERS:
            st.warning("Please enter a longer question.")
            return
        call_service(
            "POST",
            "/chat/ask",
            payload={"question": question.strip()},
            waiting_message="Reading the plan documents",
        )
        st.rerun()
