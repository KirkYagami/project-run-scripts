import re, hashlib
from config import config as c


def split_documents_into_sections(document_entries):
    out = []
    for doc in document_entries:
        name = doc["document_name"]
        t = doc["document_text"]
        headers = list(re.finditer(c.DOCUMENT_HEADER_PATTERN, t))
        if len(headers) != 1:
            raise ValueError(f"{name}: expected one header")
        t = re.sub(c.DOCUMENT_HEADER_PATTERN, "", t)
        headings = list(re.finditer(c.SECTION_HEADING_PATTERN, t))
        numbers = [int(x.group(1)) for x in headings]
        if not numbers or numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(f"{name}: section numbers {numbers}")
        starts = [0] + [m.start() for m in headings[1:]] + [len(t)]
        for a, b in zip(starts, starts[1:]):
            out.append(
                dict(
                    document_name=name,
                    section_text=re.sub(c.WHITESPACE_RUN_PATTERN, " ", t[a:b]).strip(),
                )
            )
    return out


def build_chunk_records(section_entries):
    out = []
    for i, section in enumerate(section_entries):
        sentences = re.split(c.SENTENCE_BOUNDARY_PATTERN, section["section_text"])
        start = 0
        part = 0
        while start < len(sentences):
            end = start
            chunks = []
            while (
                end < len(sentences)
                and len(" ".join(chunks + [sentences[end]])) <= c.CHUNK_SIZE_CHARACTERS
            ):
                chunks.append(sentences[end])
                end += 1
            if end == start:
                raise ValueError(
                    f"{section['document_name']}: sentence exceeds chunk size"
                )
            txt = " ".join(chunks)
            name = section["document_name"]
            out.append(
                dict(
                    chunk_id=hashlib.sha256(
                        f"{name}:{i}:{part}:{txt}".encode()
                    ).hexdigest(),
                    chunk_text=txt,
                    document_name=name,
                )
            )
            part += 1
            if end == len(sentences):
                break
            nxt = end
            overlap = 0
            while (
                nxt > start + 1
                and overlap + len(sentences[nxt - 1]) + (1 if overlap else 0)
                <= c.CHUNK_OVERLAP_CHARACTERS
            ):
                nxt -= 1
                overlap += len(sentences[nxt]) + (1 if overlap else 0)
            start = nxt
    return out
