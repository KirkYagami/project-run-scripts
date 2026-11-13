"""Embeds passages, stores them in a persistent Chroma collection and searches them."""
import os
import shutil

import chromadb
from chromadb.utils import embedding_functions

from config import config

_INSERT_BATCH_SIZE = 500


def _build_embedding_function():
    """The embedding function every build and every open of the store shares."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.EMBEDDING_MODEL_NAME, device=config.EMBEDDING_DEVICE)


def build_vector_index(chunk_records, store_path, collection_name):
    """Build the searchable knowledge base from scratch."""
    if os.path.exists(store_path):
        shutil.rmtree(store_path)
    os.makedirs(store_path, exist_ok=True)

    client = chromadb.PersistentClient(path=store_path)
    collection = client.create_collection(
        name=collection_name,
        embedding_function=_build_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    for start in range(0, len(chunk_records), _INSERT_BATCH_SIZE):
        batch = chunk_records[start:start + _INSERT_BATCH_SIZE]
        collection.add(
            ids=[record["chunk_id"] for record in batch],
            documents=[record["chunk_text"] for record in batch],
            metadatas=[{"document_name": record["document_name"]} for record in batch],
        )
    return int(collection.count())


def open_vector_index(store_path, collection_name):
    """Open the store indexing built, with the embedding model it was built with."""
    client = chromadb.PersistentClient(path=store_path)
    return client.get_collection(name=collection_name,
                                 embedding_function=_build_embedding_function())


def _passages_of(collection, document_name):
    stored = collection.get(where={"document_name": document_name})
    pairs = sorted(zip(stored["ids"], stored["documents"]))
    if not pairs:
        raise ValueError(f"The knowledge base holds no passages of {document_name}")
    return pairs


def read_document_chunks(collection, document_name):
    """Every passage stored for one document, in passage order."""
    return [text for _, text in _passages_of(collection, document_name)]


def search_document(collection, question, document_name, result_count):
    """The passages of one document closest in meaning to a question, closest first."""
    available = len(_passages_of(collection, document_name))
    found = collection.query(query_texts=[question],
                             n_results=min(result_count, available),
                             where={"document_name": document_name})
    return list(found["documents"][0])


def search_documents(collection, query_texts, result_count, document_filter):
    """Search by meaning across the documents the filter allows, one list per question."""
    found = collection.query(query_texts=list(query_texts), n_results=result_count,
                             where={"document_name": document_filter},
                             include=["documents", "metadatas", "distances"])
    results = []
    for question_index in range(len(query_texts)):
        passages = []
        for chunk_id, text, metadata, distance in zip(found["ids"][question_index],
                                                      found["documents"][question_index],
                                                      found["metadatas"][question_index],
                                                      found["distances"][question_index]):
            passages.append({
                "chunk_id": chunk_id,
                "chunk_text": text,
                "document_name": metadata["document_name"],
                "distance": float(distance),
            })
        results.append(passages)
    return results
