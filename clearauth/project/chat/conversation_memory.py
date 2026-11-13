from config import config as c
from persistence.models import ChatTurn
from persistence.repository import fetch_chat_turns


def recall_conversation(session, username, question_text):
    turns = fetch_chat_turns(
        session, ChatTurn.username == username, c.CHAT_HISTORY_TURN_LIMIT
    )
    history = (
        "\n\n".join(
            "QUESTION: "
            + t["question_text"]
            + "\nANSWER: "
            + (
                c.CHAT_RECORD_ANSWER_IN_HISTORY
                if t["question_type"] in c.CHAT_RECORD_TYPES
                else t["answer_text"]
            )
            for t in reversed(turns)
        )
        if turns
        else "This is the first question."
    )
    return dict(
        history_text=history,
        search_text=(turns[0]["question_text"] + "\n" if turns else "") + question_text,
    )
