"""Settles what kind of question was asked and answers it from the documents the chat may read."""
import re

from agentic.agents import call_language_model, parse_labelled_response
from config import config
from knowledge.vector_index import read_document_chunks, search_documents

_LABELS = ["QUESTION TYPE", "DISPUTE REFERENCE", "ANSWER"]


def _first_line(text):
    return text.splitlines()[0].strip(config.RESPONSE_DECORATION_CHARACTERS + ".").strip()


def answer_from_documents(collection, question_text, conversation):
    """Answer a question from the documents the chat may read in one model call, or refuse."""
    allowed = {"$nin": list(config.CHAT_EXCLUDED_DOCUMENTS)}
    found = search_documents(collection, [question_text, conversation["search_text"]],
                             config.CHAT_RETRIEVAL_RESULT_COUNT, allowed)
    passages, seen = [], set()
    for passage in sorted((item for group in found for item in group), key=lambda item: item["distance"]):
        if passage["chunk_id"] not in seen:
            seen.add(passage["chunk_id"])
            passages.append(passage)
    closest = min((passage["distance"] for passage in passages), default=2.0)

    schedules = {}
    for tariff, document in config.TARIFF_DOCUMENT_BY_TARIFF.items():
        schedules[tariff] = " ".join(read_document_chunks(collection, document))

    passage_text = "\n\n".join(f"[{passage['document_name']}] {passage['chunk_text']}" for passage in passages)
    schedule_text = "\n\n".join(f"{tariff} schedule ({config.TARIFF_DOCUMENT_BY_TARIFF[tariff]}): {text}"
                                for tariff, text in schedules.items())
    prompt = (
        f"You are the billing assistant for {config.ORGANISATION_NAME}. Answer only from the passages and "
        "schedules below, and from nothing else.\n\n"
        f"THE KINDS OF QUESTION: {', '.join(config.CHAT_TYPE_OPTIONS)}.\n"
        f"You know nothing about any individual dispute; a question about one is {config.CHAT_TYPE_DISPUTE_STATUS}.\n\n"
        f"THE CONVERSATION SO FAR\n{conversation['history_text']}\n\n"
        f"PASSAGES\n{passage_text}\n\nTHE FIVE TARIFF SCHEDULES\n{schedule_text}\n\n"
        f"THE QUESTION\n{question_text}\n\n"
        "Quote a price only from that tariff's own schedule. Write money as GBP and a figure with no "
        "currency symbol. For a question you may answer, give two to five full sentences drawn only from "
        "what you are given. Where a field does not apply write none in it; an empty field is refused. "
        "Reply in exactly this layout:\n" + "\n".join(f"{label}: <your text>" for label in _LABELS))
    reply = call_language_model(prompt, config.AGENT_NAME_BILLING_ASSISTANT)
    fields = parse_labelled_response(reply["response_text"], _LABELS, config.AGENT_NAME_BILLING_ASSISTANT)

    question_type = _first_line(fields["QUESTION TYPE"]).upper()
    if question_type not in config.CHAT_TYPE_OPTIONS:
        raise ValueError(f"The billing assistant named the question type '{question_type}', which is not "
                         f"one of {config.CHAT_TYPE_OPTIONS}.")
    reference = re.search(config.DISPUTE_REFERENCE_PATTERN, fields["DISPUTE REFERENCE"].upper())
    dispute_reference = reference.group(0) if reference else None

    answered = (question_type in config.CHAT_ANSWERED_TYPES and closest <= config.CHAT_MAX_RELEVANCE_DISTANCE)
    if answered:
        sources = []
        for passage in passages:
            if passage["document_name"] not in sources:
                sources.append(passage["document_name"])
        if question_type == config.CHAT_TYPE_TARIFF:
            for document in config.TARIFF_DOCUMENT_BY_TARIFF.values():
                if document not in sources:
                    sources.append(document)
        return {"question_type": question_type, "dispute_reference": dispute_reference,
                "answer": fields["ANSWER"], "source_documents": sources,
                "closest_distance": float(closest), "was_refused": False}
    if question_type == config.CHAT_TYPE_DISPUTE_STATUS:
        return {"question_type": question_type, "dispute_reference": dispute_reference,
                "answer": fields["ANSWER"], "source_documents": [],
                "closest_distance": float(closest), "was_refused": False}
    return {"question_type": config.CHAT_TYPE_OUT_OF_SCOPE, "dispute_reference": dispute_reference,
            "answer": config.CHAT_REFUSAL_MESSAGE, "source_documents": [],
            "closest_distance": float(closest), "was_refused": True}
