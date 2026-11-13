"""Searches the indexed manuals and returns what they say, word for word, with sources."""

from config import config
from knowledge.procedure_retrieval import (
    format_retrieved_context,
    open_vector_collection,
    retrieve_relevant_chunks,
)
from knowledge.vector_index import create_embedding_vectors, load_embedding_model


def open_manual_search(store_path, collection_name):
    """Open the built collection and its embedding model once, as one search handle."""
    return {
        "collection": open_vector_collection(store_path, collection_name),
        "embedding_model": load_embedding_model(config.EMBEDDING_MODEL_NAME, config.EMBEDDING_DEVICE),
    }


def _search_manuals(manual_search, question_text):
    query_vector = create_embedding_vectors(manual_search["embedding_model"], [question_text])[0]
    chunks = retrieve_relevant_chunks(manual_search["collection"], query_vector, config.RETRIEVAL_RESULT_COUNT)
    source_documents = []
    for chunk in chunks:
        if chunk["document_name"] not in source_documents:
            source_documents.append(chunk["document_name"])
    return {
        "question_text": question_text,
        "context_text": format_retrieved_context(chunks),
        "source_documents": source_documents,
        "chunk_count": len(chunks),
    }


def lookup_repair_procedure(manual_search, machine_type, problem_type):
    """The manual passages for repairing this problem type on this machine type."""
    question_text = (
        "What is the repair procedure for " + problem_type + " on a " + machine_type
        + ", including the permit required, the parts needed and the torque values?"
    )
    return _search_manuals(manual_search, question_text)


def lookup_safety_requirement(manual_search, machine_type):
    """The permit, isolation and tight space rules for working on this machine type."""
    question_text = (
        "What lockout tagout permit, isolation steps and tight space rules apply before "
        "working on a " + machine_type + "?"
    )
    return _search_manuals(manual_search, question_text)
