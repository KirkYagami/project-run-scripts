from config import config as c
from .note_cleaning import clean_note_records
from .common_cleaning import remove_rows_missing_target


def clean_sentence_dataset(frame):
    f = clean_note_records(
        frame,
        c.SENTENCE_VALUE_MAPPINGS,
        c.SENTENCE_WHOLE_NUMBER_PATTERNS,
        c.SENTENCE_ID_COLUMN,
        c.SENTENCE_TEXT_COLUMN,
    )
    f[c.SENTENCE_LENGTH_COLUMN] = f[c.SENTENCE_TEXT_COLUMN].str.len()
    f = remove_rows_missing_target(f, c.SENTENCE_TARGET_COLUMN)
    return f[
        f[c.SENTENCE_TEXT_COLUMN].str.split().str.len().ge(c.MINIMUM_SENTENCE_WORDS)
    ].reset_index(drop=True)
