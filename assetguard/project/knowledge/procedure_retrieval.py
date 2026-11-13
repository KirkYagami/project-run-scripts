"""The read side of the knowledge base: find and lay out the passages closest to a question."""

from knowledge.vector_index import open_store_client


def open_vector_collection(store_path, collection_name):
    """Open an existing collection; raises if it was never built."""
    return open_store_client(store_path).get_collection(name=collection_name)


def retrieve_relevant_chunks(collection, query_vector, result_count):
    """The result_count closest passages to query_vector, closest first."""
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=result_count,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {
            "chunk_id": chunk_id,
            "chunk_text": chunk_text,
            "document_name": metadata["document_name"],
            "distance": round(float(distance), 4),
        }
        for chunk_id, chunk_text, metadata, distance in zip(
            results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]
        )
    ]


def format_retrieved_context(retrieved_chunks):
    """One block of text with every passage under its source document, in the given order."""
    return "\n\n---\n\n".join(
        "[Source: " + chunk["document_name"] + "]\n" + chunk["chunk_text"] for chunk in retrieved_chunks
    )
