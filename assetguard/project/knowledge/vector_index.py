"""Builds the searchable knowledge store: every chunk beside an embedding of its meaning."""

from functools import lru_cache

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import config
from knowledge.chunk_splitting import build_chunk_records
from knowledge.pdf_extraction import extract_text_from_directory

# Chroma refuses very large single inserts, so chunks are added in batches.
ADD_BATCH_SIZE = 1000


@lru_cache(maxsize=None)
def load_embedding_model(model_name, device_name):
    """Load the sentence embedding model once per process (downloads are cached on disk)."""
    return SentenceTransformer(model_name, device=device_name)


def create_embedding_vectors(embedding_model, text_list):
    """Embed every text in one call; returns plain lists of floats in input order."""
    vectors = embedding_model.encode(list(text_list), show_progress_bar=False)
    return vectors.tolist()


def open_store_client(store_path):
    """A persistent Chroma client with telemetry switched off."""
    return chromadb.PersistentClient(path=store_path, settings=Settings(anonymized_telemetry=False))


def create_vector_collection(store_path, collection_name):
    """Replace any collection of this name with a new, empty cosine-distance collection."""
    client = open_store_client(store_path)
    existing = [collection.name for collection in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(collection_name)
    return client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})


def add_chunks_to_collection(collection, chunk_records, chunk_vectors):
    """Store each chunk with its own vector and its source details; return the stored count."""
    for start in range(0, len(chunk_records), ADD_BATCH_SIZE):
        batch = chunk_records[start:start + ADD_BATCH_SIZE]
        collection.add(
            ids=[record["chunk_id"] for record in batch],
            documents=[record["chunk_text"] for record in batch],
            embeddings=chunk_vectors[start:start + ADD_BATCH_SIZE],
            metadatas=[
                {"document_name": record["document_name"], "chunk_position": record["chunk_position"]}
                for record in batch
            ],
        )
    return collection.count()


def chunk_embedding_text(chunk_record):
    """The text a chunk is embedded from: its document's title, then the chunk itself.

    The six machine manuals share near-identical torque tables and procedures, and a
    chunk from the middle of one rarely names its machine. Prefixing the title lets a
    question about a water pump reach the water pump manual. The stored and returned
    chunk text is unchanged.
    """
    document_title = chunk_record["document_name"].rsplit(".", 1)[0].replace("-", " ")
    return document_title + ": " + chunk_record["chunk_text"]


def build_knowledge_index(docs_directory, store_path):
    """Read, chunk, embed and store the whole corpus; return the number of chunks stored."""
    document_entries = extract_text_from_directory(docs_directory)
    print("    documents read: " + str(len(document_entries)))
    chunk_records = build_chunk_records(
        document_entries, config.CHUNK_SIZE_CHARACTERS, config.CHUNK_OVERLAP_CHARACTERS)
    print("    chunks created: " + str(len(chunk_records)))

    embedding_model = load_embedding_model(config.EMBEDDING_MODEL_NAME, config.EMBEDDING_DEVICE)
    chunk_vectors = create_embedding_vectors(embedding_model, [chunk_embedding_text(record) for record in chunk_records])
    collection = create_vector_collection(store_path, config.VECTOR_COLLECTION_NAME)
    return add_chunks_to_collection(collection, chunk_records, chunk_vectors)
