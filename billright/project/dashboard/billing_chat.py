"""The billing chat page."""
import streamlit as st

from config import config
from dashboard.api_client import call_service


def render_billing_chat_page():
    """Let anyone at the desk or in the contact centre ask the billing assistant a question."""
    st.header(config.PAGE_CHAT)
    st.caption("Ask about tariffs, billing rules, customer advice or a dispute's status. "
               f"The assistant remembers the last {config.CHAT_HISTORY_TURN_LIMIT} exchanges.")
    if st.session_state.get("role") not in config.CHAT_FIGURE_ROLES:
        st.info("You hear a dispute's status and never a figure. " + config.CHAT_AMOUNTS_IN_WRITING_MESSAGE)
    turns = call_service("GET", "/chat/turns", {"turn_limit": config.CHAT_PAGE_TURN_LIMIT}, None, None)
    for turn in reversed(turns):                     # oldest at the top
        with st.chat_message("user"):
            st.write(turn["question_text"])
        with st.chat_message("assistant"):
            st.badge(turn["question_type"], color=config.CHAT_TYPE_BADGE_COLOURS.get(turn["question_type"], "gray"))
            if turn["was_refused"]:
                st.caption("Refused")
            st.write(turn["answer_text"])
            if turn["source_documents"]:
                st.caption("Sources: " + turn["source_documents"])
    question = st.chat_input("Ask a question")
    if question is not None:
        if len(question.strip()) < config.CHAT_QUESTION_MINIMUM_CHARACTERS:
            st.warning(f"A question needs at least {config.CHAT_QUESTION_MINIMUM_CHARACTERS} characters.")
        else:
            call_service("POST", "/chat/ask", None, {"question": question},
                         "Searching the documents in one language model call")
            st.rerun()
