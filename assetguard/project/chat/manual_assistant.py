"""Answers one question from the Meridian manuals for exactly one language model call.

The search costs nothing; the single call both settles what kind of question it
is and answers it. The grounding check then decides, without trusting the
model, whether a manual answer sits close enough to the question to be shown.
"""

import re

from agentic.agents import LABEL_DECORATION, call_language_model, parse_labelled_response
from config import config
from knowledge.procedure_retrieval import format_retrieved_context, retrieve_relevant_chunks
from knowledge.vector_index import create_embedding_vectors

LABEL_QUESTION_TYPE = "QUESTION TYPE"
LABEL_MACHINE_ID = "MACHINE ID"
LABEL_SOURCE = "SOURCE"
LABEL_ANSWER = "ANSWER"
NONE_VALUE = "NONE"

MANUAL_ANSWER_TYPES = [config.CHAT_TYPE_PROCEDURE, config.CHAT_TYPE_SAFETY, config.CHAT_TYPE_PARTS]

QUESTION_TYPE_GUIDE = {
    config.CHAT_TYPE_PROCEDURE: "how a repair, inspection, alignment or other maintenance task is carried "
                                "out, including torque values, tolerances and step order",
    config.CHAT_TYPE_SAFETY: "which permit, lockout, isolation, tight space rule or other safety "
                             "requirement applies",
    config.CHAT_TYPE_PARTS: "which part, kit, consumable or part code to order or fit",
    config.CHAT_TYPE_MACHINE_STATUS: "the current condition, risk or readings of one particular "
                                     "machine named by its code (for example PMP-CHE-0067)",
    config.CHAT_TYPE_OUT_OF_SCOPE: "anything the passages below do not cover, or anything not about "
                                   "Meridian machines, maintenance or safety",
}


def retrieve_manual_context(manual_search, search_text):
    """The closest passages laid out with their sources, and how close the closest one came."""
    collection = manual_search["collection"]
    if collection.count() == 0:
        # Nothing indexed yet: report a distance past the limit so the caller refuses.
        return {
            "context_text": "",
            "source_documents": [],
            "closest_distance": config.CHAT_MAX_RELEVANCE_DISTANCE + 1.0,
            "chunk_count": 0,
        }

    query_vector = create_embedding_vectors(manual_search["embedding_model"], [search_text])[0]
    chunks = retrieve_relevant_chunks(collection, query_vector, config.RETRIEVAL_RESULT_COUNT)
    source_documents = []
    for chunk in chunks:
        if chunk["document_name"] not in source_documents:
            source_documents.append(chunk["document_name"])
    return {
        "context_text": format_retrieved_context(chunks),
        "source_documents": source_documents,
        "closest_distance": min(chunk["distance"] for chunk in chunks),
        "chunk_count": len(chunks),
    }


def _answer_text(response_text):
    """Everything after the ANSWER label, so an answer may run over several lines."""
    lines = response_text.splitlines()
    for position, line in enumerate(lines):
        cleaned = re.sub(LABEL_DECORATION, "", line).replace("**", "")
        match = re.match(r"^\s*" + LABEL_ANSWER + r"\s*:\s*(.*)$", cleaned, flags=re.IGNORECASE)
        if match:
            return "\n".join([match.group(1)] + lines[position + 1:]).strip()
    return ""


def answer_manual_question(question_text, history_text, manual_context):
    """One call: classify the question, name its machine, and answer it from the passages."""
    type_lines = "\n".join(
        "- " + type_name + ": " + description for type_name, description in QUESTION_TYPE_GUIDE.items())
    prompt_text = (
        "You are the manual assistant for maintenance technicians at Meridian Heavy Industries. "
        "You may use ONLY the manual passages below. If they do not answer the question, say so; "
        "never answer from general engineering knowledge, because an instruction that is not in a "
        "Meridian document must never reach a technician.\n\n"
        "First decide which ONE of these kinds the new question is:\n" + type_lines + "\n\n"
        "Use the conversation so far only to understand what a follow up question refers to.\n\n"
        "Conversation so far:\n" + history_text + "\n\n"
        "New question:\n" + question_text + "\n\n"
        "Manual passages:\n" + (manual_context["context_text"] or "(no passages were found)") + "\n\n"
        "Reply with exactly these labelled lines, in this order, and nothing before them:\n"
        + LABEL_QUESTION_TYPE + ": <one of " + ", ".join(config.CHAT_TYPE_OPTIONS) + ">\n"
        + LABEL_MACHINE_ID + ": <the machine code the question is about, in capitals, or "
        + NONE_VALUE + ">\n"
        + LABEL_SOURCE + ": <the document name the answer came from, or " + NONE_VALUE + ">\n"
        + LABEL_ANSWER + ": <the answer, quoting values and codes exactly; it may run over several "
        "lines>\n\n"
        "For " + config.CHAT_TYPE_MACHINE_STATUS + " and " + config.CHAT_TYPE_OUT_OF_SCOPE
        + " leave " + LABEL_ANSWER + " empty: those are not answered from the manuals."
    )
    reply = call_language_model(prompt_text, config.AGENT_NAME_MANUAL_ASSISTANT)
    result = parse_labelled_response(reply["response_text"], [LABEL_QUESTION_TYPE, LABEL_MACHINE_ID, LABEL_SOURCE])
    result[LABEL_ANSWER] = _answer_text(reply["response_text"])
    result["call_record"] = reply["call_record"]
    return result


def check_answer_is_grounded(question_type, closest_distance):
    """True unless a manual answered kind has no passage within the relevance limit."""
    if question_type not in MANUAL_ANSWER_TYPES:
        return True
    return closest_distance <= config.CHAT_MAX_RELEVANCE_DISTANCE
