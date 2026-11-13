"""Entry point 4: build the maintenance knowledge store and prove it answers real questions."""

import os

from config import config
from knowledge.procedure_retrieval import (
    format_retrieved_context,
    open_vector_collection,
    retrieve_relevant_chunks,
)
from knowledge.vector_index import build_knowledge_index, create_embedding_vectors, load_embedding_model

SAMPLE_QUESTIONS = [
    "water pump bearing replacement torque setting",
    "who approves a twelve hour shutdown of a critical machine",
    # Asked the way a person on the floor would ask it; the casebook answer turns
    # on a cause the question never names.
    "why do couplings keep failing after alignment",
]

if __name__ == "__main__":
    os.makedirs(config.DATABASE_DIRECTORY, exist_ok=True)

    print("Building the maintenance knowledge index")
    stored_count = build_knowledge_index(config.DOCS_DIRECTORY, config.VECTOR_STORE_DIRECTORY)
    print("    chunks stored: " + str(stored_count))
    print("    store location: " + config.VECTOR_STORE_DIRECTORY)

    embedding_model = load_embedding_model(config.EMBEDDING_MODEL_NAME, config.EMBEDDING_DEVICE)
    collection = open_vector_collection(config.VECTOR_STORE_DIRECTORY, config.VECTOR_COLLECTION_NAME)
    for question_text in SAMPLE_QUESTIONS:
        query_vector = create_embedding_vectors(embedding_model, [question_text])[0]
        matches = retrieve_relevant_chunks(collection, query_vector, config.RETRIEVAL_RESULT_COUNT)
        print("Question: " + question_text)
        for match in matches:
            print("    " + match["document_name"] + " distance " + str(match["distance"]))
        print("    joined passage: " + str(len(format_retrieved_context(matches))) + " characters")
