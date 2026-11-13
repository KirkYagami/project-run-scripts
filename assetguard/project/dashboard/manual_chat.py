"""The Manual chat page: a technician asks the Meridian manuals a question.

The conversation lives in this browser tab only and travels with every
question. The page settles nothing: the service classifies, searches and answers.
"""

import streamlit as st

from config import config

CONVERSATION_KEY = "manual_chat_conversation"
NEUTRAL_BADGE_COLOUR = "gray"

CHAT_TYPE_BADGE_COLOURS = {
    config.CHAT_TYPE_PROCEDURE: "blue",
    config.CHAT_TYPE_SAFETY: "orange",
    config.CHAT_TYPE_PARTS: "violet",
    config.CHAT_TYPE_MACHINE_STATUS: "green",
    config.CHAT_TYPE_OUT_OF_SCOPE: NEUTRAL_BADGE_COLOUR,
}


def render_one_exchange(past_turn):
    with st.chat_message("user"):
        st.text(past_turn["question"])
    with st.chat_message("assistant"):
        question_type = past_turn.get("question_type") or config.CHAT_TYPE_PROCEDURE
        st.badge(question_type, color=CHAT_TYPE_BADGE_COLOURS.get(question_type, NEUTRAL_BADGE_COLOUR))
        st.text(past_turn["answer"])
        supporting_line = "Passages searched: " + str(past_turn.get("chunks_searched") or 0)
        if past_turn.get("source_documents"):
            supporting_line += " · Sources: " + " · ".join(past_turn["source_documents"])
        st.caption(supporting_line)


def render_manual_chat_page(ask_handler):
    st.header(config.PAGE_CHAT)
    st.caption(
        "Answers come only from the Meridian machine manuals, safety rules and policies. The last "
        + str(config.CHAT_HISTORY_TURN_LIMIT) + " exchanges are remembered for follow up questions."
    )

    if CONVERSATION_KEY not in st.session_state:
        st.session_state[CONVERSATION_KEY] = []
    conversation = st.session_state[CONVERSATION_KEY]
    for past_turn in conversation:
        render_one_exchange(past_turn)

    question_text = st.chat_input("Ask about a procedure, a permit, a part or a machine code")
    if not question_text:
        return

    history = [
        {"question": past_turn["question"], "answer": past_turn["answer"]}
        for past_turn in conversation[-config.CHAT_HISTORY_TURN_LIMIT:]
    ] if config.CHAT_HISTORY_TURN_LIMIT > 0 else []
    with st.spinner("Searching the manuals. This makes one language model call..."):
        reply = ask_handler(question_text, history)
    conversation.append({
        "question": question_text,
        "answer": reply["answer"],
        "question_type": reply["question_type"],
        "source_documents": reply["source_documents"],
        "chunks_searched": reply["chunks_searched"],
    })
    st.rerun()
