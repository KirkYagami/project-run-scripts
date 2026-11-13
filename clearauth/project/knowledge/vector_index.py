from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from functools import lru_cache
from config import config as c


@lru_cache(maxsize=1)
def _embedding():
    return SentenceTransformerEmbeddingFunction(
        model_name=c.EMBEDDING_MODEL_NAME, device=c.EMBEDDING_DEVICE
    )


def _client(path):
    return chromadb.PersistentClient(
        path=str(path), settings=Settings(anonymized_telemetry=False)
    )


def build_vector_index(chunk_records, store_path):
    p = Path(store_path)
    if p.is_file() or (
        p.exists() and any(p.iterdir()) and not (p / c.VECTOR_STORE_FILE_NAME).exists()
    ):
        raise ValueError(f"{store_path}: not a vector store")
    emb = _embedding()
    vectors = emb([r["chunk_text"] for r in chunk_records])
    client = _client(store_path)
    if c.VECTOR_COLLECTION_NAME in [x.name for x in client.list_collections()]:
        client.delete_collection(c.VECTOR_COLLECTION_NAME)
    col = client.create_collection(
        c.VECTOR_COLLECTION_NAME,
        embedding_function=emb,
        metadata={"hnsw:space": c.VECTOR_DISTANCE_METRIC},
    )
    for i in range(0, len(chunk_records), 100):
        batch = chunk_records[i : i + 100]
        col.add(
            ids=[r["chunk_id"] for r in batch],
            documents=[r["chunk_text"] for r in batch],
            metadatas=[{"document_name": r["document_name"]} for r in batch],
            embeddings=vectors[i : i + 100],
        )
    return col.count()


def open_vector_index(store_path):
    if not (Path(store_path) / c.VECTOR_STORE_FILE_NAME).is_file():
        raise ValueError(f"{store_path}: vector store missing")
    try:
        return _client(store_path).get_collection(
            c.VECTOR_COLLECTION_NAME, embedding_function=_embedding()
        )
    except Exception as e:
        raise ValueError(f"{store_path}: collection missing: {e}") from e


def find_section_passage(collection, question, document_name, section_heading):
    if not collection.count():
        raise ValueError(
            c.INDEX_HOLDS_NO_CHUNKS_MESSAGE.format(document_name=document_name)
        )
    r = collection.query(
        query_texts=[question], n_results=1, where={"document_name": document_name}
    )
    if not r["documents"][0]:
        raise ValueError(
            c.INDEX_HOLDS_NO_CHUNKS_MESSAGE.format(document_name=document_name)
        )
    t = r["documents"][0][0]
    if not t.startswith(section_heading):
        raise ValueError(
            c.PASSAGE_OF_ANOTHER_SECTION_MESSAGE.format(
                document_name=document_name,
                question=question,
                section_heading=section_heading,
            )
        )
    return t[len(section_heading) :].strip()


def search_documents(collection, query_texts):
    r = collection.query(
        query_texts=query_texts,
        n_results=c.CHAT_RETRIEVAL_RESULT_COUNT,
        where={"document_name": {"$nin": c.CHAT_EXCLUDED_DOCUMENTS}},
    )
    return [
        [
            dict(
                chunk_id=i,
                chunk_text=t,
                document_name=m["document_name"],
                distance=float(d),
            )
            for i, t, m, d in zip(ids, ts, ms, ds)
        ]
        for ids, ts, ms, ds in zip(
            r["ids"], r["documents"], r["metadatas"], r["distances"]
        )
    ]
