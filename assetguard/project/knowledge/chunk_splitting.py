"""Cuts documents into short overlapping pieces, each labelled with its source."""

import re


def _window_end(text, start, chunk_size):
    """Where a window starting at start should stop: a sentence end if one falls in
    the second half of the window, otherwise the last word boundary."""
    hard_end = start + chunk_size
    if hard_end >= len(text):
        return len(text)
    window = text[start:hard_end]
    sentence_end = window.rfind(". ")
    if sentence_end >= chunk_size // 2:
        return start + sentence_end + 1
    word_end = window.rfind(" ")
    return start + word_end if word_end > 0 else hard_end


def _next_word_start(text, position):
    """The first position at or after position that starts a word."""
    if position <= 0 or text[position - 1] == " ":
        return max(position, 0)
    next_space = text.find(" ", position)
    return len(text) if next_space == -1 else next_space + 1


def split_text_into_chunks(document_text, chunk_size, chunk_overlap):
    """Windows of at most chunk_size characters that each step back about
    chunk_overlap characters into the previous one.

    Windows end on a sentence or word boundary and start on a word boundary, so no
    chunk opens or closes halfway through a word. Whitespace is collapsed first, so
    the windows are measured on the stored text.
    """
    text = re.sub(r"\s+", " ", document_text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = _window_end(text, start, chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        next_start = _next_word_start(text, end - chunk_overlap)
        start = next_start if next_start > start else end
    return chunks


def build_chunk_records(document_entries, chunk_size, chunk_overlap):
    """Split every document and label each piece with its document and position."""
    chunk_records = []
    for document_entry in document_entries:
        document_name = document_entry["document_name"]
        chunks = split_text_into_chunks(document_entry["document_text"], chunk_size, chunk_overlap)
        for chunk_position, chunk_text in enumerate(chunks):
            chunk_records.append({
                "chunk_id": document_name + "::" + str(chunk_position),
                "chunk_text": chunk_text,
                "document_name": document_name,
                "chunk_position": chunk_position,
            })
    return chunk_records
