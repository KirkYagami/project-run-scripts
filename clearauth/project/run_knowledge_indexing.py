from config import config as c
from knowledge.pdf_extraction import extract_text_from_directory
from knowledge.chunk_splitting import split_documents_into_sections, build_chunk_records
from knowledge.vector_index import build_vector_index, open_vector_index
from tools.retrieval_tools import read_documentation_to_send


def main():
    docs = extract_text_from_directory(c.DOCS_DIRECTORY)
    sections = split_documents_into_sections(docs)
    chunks = build_chunk_records(sections)
    print("documents read:", len(docs), "sections found:", len(sections), flush=True)
    print(
        "chunks stored:",
        build_vector_index(chunks, c.VECTOR_STORE_DIRECTORY),
        flush=True,
    )
    col = open_vector_index(c.VECTOR_STORE_DIRECTORY)
    for code, name in c.SERVICE_POLICY_DOCUMENTS.items():
        print(code, name, read_documentation_to_send(col, code), flush=True)


if __name__ == "__main__":
    main()
