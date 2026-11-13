"""The short memory that lets a follow up question mean something on its own.

Nothing is stored here: the browser sends the conversation with every question,
and each function hands back something new built from what it was given.
"""


def trim_conversation_history(conversation_history, turn_limit):
    """The last turn_limit exchanges, oldest first, as a new list."""
    if turn_limit <= 0:
        return []
    return list(conversation_history[-turn_limit:])


def build_search_text(conversation_history, question_text):
    """Earlier questions then the new one, joined by single spaces. Answers are left out."""
    return " ".join([past_turn["question"] for past_turn in conversation_history] + [question_text])


def format_history_for_prompt(conversation_history):
    """The recent exchanges as readable text, or a line saying there are none yet."""
    if not conversation_history:
        return "This is the first question in the conversation."
    return "\n\n".join(
        "Exchange " + str(number) + "\nTECHNICIAN ASKED: " + past_turn["question"]
        + "\nASSISTANT ANSWERED: " + past_turn["answer"]
        for number, past_turn in enumerate(conversation_history, start=1)
    )
