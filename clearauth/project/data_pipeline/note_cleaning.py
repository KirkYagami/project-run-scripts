from config import config as c
from .common_cleaning import *


def clean_note_records(
    frame, value_mappings, whole_number_patterns, id_column, text_column
):
    f = remove_duplicate_records(frame)
    f[c.REQUEST_REFERENCE_COLUMN] = convert_identifiers(
        f[c.REQUEST_REFERENCE_COLUMN],
        c.REQUEST_REFERENCE_PATTERN,
        c.CANONICAL_REQUEST_REFERENCE_FORMAT,
    )
    refuse_missing_values(f, [id_column, c.REQUEST_REFERENCE_COLUMN])
    refuse_repeated_references(f, [id_column])
    f = convert_whole_numbers(
        normalize_category_values(f, value_mappings), whole_number_patterns
    )
    f[text_column] = clean_clinical_text(f[text_column])
    return f
