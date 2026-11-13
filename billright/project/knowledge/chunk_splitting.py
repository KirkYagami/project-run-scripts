"""Cuts the documents into sections, and the sections into passages."""
import re

from config import config


def _clean_whitespace(text):
    text = re.sub(config.CONTROL_CHARACTER_PATTERN, " ", text)
    return re.sub(config.WHITESPACE_RUN_PATTERN, " ", text).strip()


def split_documents_into_sections(document_entries):
    """Split each document at its numbered headings, removing its header line."""
    sections = []
    for entry in document_entries:
        name = entry["document_name"]
        text = entry["document_text"]
        # Control characters could split a heading or the header line, so they
        # are replaced first, but line breaks are kept for the line-anchored pattern.
        text = re.sub(config.CONTROL_CHARACTER_PATTERN, " ", text)

        header_matches = list(re.finditer(config.DOCUMENT_HEADER_PATTERN, text))
        if len(header_matches) != 1:
            raise ValueError(f"{name} holds {len(header_matches)} header lines, not exactly one")
        header = header_matches[0]
        text = text[:header.start()] + "\n" + text[header.end():]

        headings = list(re.finditer(config.SECTION_HEADING_PATTERN, text))
        numbers = [int(heading.group(1)) for heading in headings]
        if not headings or numbers != list(range(1, len(headings) + 1)):
            raise ValueError(f"{name} has headings numbered {numbers}, "
                             f"not 1, 2, 3 and so on in order")

        starts = [heading.start() for heading in headings]
        boundaries = [0] + starts[1:] + [len(text)]
        for index in range(len(headings)):
            section_text = _clean_whitespace(text[boundaries[index]:boundaries[index + 1]])
            sections.append({"document_name": name, "section_text": section_text})
    return sections


def _split_sentences(section_text):
    return [sentence for sentence in re.split(config.SENTENCE_BOUNDARY_PATTERN, section_text)
            if sentence.strip()]


def _overlap_sentences(sentences, chunk_overlap):
    """The closing whole sentences of a passage, up to chunk_overlap characters."""
    carried = []
    length = 0
    for sentence in reversed(sentences):
        added = len(sentence) + (1 if carried else 0)
        if length + added > chunk_overlap:
            break
        carried.insert(0, sentence)
        length += added
    return carried


def _passages_of_section(section_text, chunk_size, chunk_overlap):
    sentences = _split_sentences(section_text)
    passages = []
    current = []
    new_in_current = 0
    for sentence in sentences:
        projected = len(" ".join(current + [sentence]))
        if current and new_in_current > 0 and projected > chunk_size:
            passages.append(" ".join(current))
            current = _overlap_sentences(current, chunk_overlap)
            # make room: drop carried sentences until the next sentence fits
            while current and len(" ".join(current + [sentence])) > chunk_size:
                current = current[1:]
            new_in_current = 0
        current.append(sentence)
        new_in_current += 1
    if current and new_in_current > 0:
        passages.append(" ".join(current))
    return passages


def build_chunk_records(section_entries, chunk_size, chunk_overlap):
    """Produce the passages the vector store holds."""
    records = []
    section_counts = {}
    for entry in section_entries:
        name = entry["document_name"]
        section_number = section_counts.get(name, 0) + 1
        section_counts[name] = section_number
        stem = name.rsplit(".", 1)[0]
        passages = _passages_of_section(entry["section_text"], chunk_size, chunk_overlap)
        for passage_number, passage in enumerate(passages, start=1):
            records.append({
                "chunk_id": f"{stem}-S{section_number:02d}-C{passage_number:02d}",
                "chunk_text": passage,
                "document_name": name,
            })
    return records
