"""Recalls the last few exchanges of a person's own conversation."""
from config import config
from persistence import repository
from persistence.models import ChatTurn


def recall_conversation(session, username, question_text):
    """Give the assistant the last few exchanges of this person's own conversation."""
    turns = repository.fetch_chat_turns(session, ChatTurn.username == username,
                                        config.CHAT_HISTORY_TURN_LIMIT)
    turns = list(reversed(turns))           # oldest first
    if not turns:
        history_text = "This is the first question of the conversation."
        earlier = []
    else:
        parts = []
        for turn in turns:
            answered = (config.CHAT_STATUS_ANSWER_IN_HISTORY
                        if turn["question_type"] == config.CHAT_TYPE_DISPUTE_STATUS
                        else turn["answer_text"])
            parts.append(f"Asked: {turn['question_text']}\nAnswered: {answered}")
        history_text = "\n\n".join(parts)
        earlier = [turn["question_text"] for turn in turns]
    return {"history_text": history_text, "search_text": " ".join(earlier + [question_text])}
