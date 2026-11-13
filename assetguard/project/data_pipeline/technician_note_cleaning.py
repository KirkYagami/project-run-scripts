"""Cleans the free-text technician notes the problem type classifier learns from.

The notes were pasted out of a web system, so some carry markup and broken
characters, and the recorded note length no longer matches the text.
"""

import numpy as np

from config import config
from data_pipeline import common_cleaning as cc
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset


def remove_markup_artifacts(dataframe, text_column):
    """Replace markup with a space and drop broken character sequences."""
    cleaned = dataframe.copy()
    text = cleaned[text_column].str.replace(config.MARKUP_PATTERN, " ", regex=True)
    for artifact in config.ENCODING_ARTIFACT_LIST:
        text = text.str.replace(artifact, "", regex=False)
    cleaned[text_column] = text
    return cleaned


def normalize_note_whitespace(dataframe, text_column):
    """Collapse every run of whitespace to one space and trim the ends."""
    cleaned = dataframe.copy()
    cleaned[text_column] = cleaned[text_column].str.replace(r"\s+", " ", regex=True).str.strip()
    return cleaned


def drop_unusable_notes(dataframe, minimum_length):
    """Keep only notes with a label and at least minimum_length characters."""
    text = dataframe[config.NOTE_TEXT_COLUMN]
    usable = (
        text.notna()
        & dataframe[config.NOTE_TARGET_COLUMN].notna()
        & (text.str.len() >= minimum_length)
    )
    return dataframe[usable.fillna(False)].reset_index(drop=True)


def recompute_note_length(dataframe, text_column):
    """Set note_length_chars to the length of the cleaned note."""
    cleaned = dataframe.copy()
    cleaned["note_length_chars"] = cleaned[text_column].str.len().astype(int)
    return cleaned


def clean_technician_note_dataset(input_path, output_path):
    """Clean the raw notes file and save it."""
    frame = load_raw_dataset(input_path, config.NULL_TOKEN_LIST)

    frame = cc.strip_text_whitespace(frame)
    frame = cc.replace_missing_tokens(frame, config.NULL_TOKEN_LIST)
    frame = cc.standardize_machine_code(frame)
    frame = cc.normalize_category_column(frame, "machine_type", config.MACHINE_TYPE_MAPPING)
    frame = cc.normalize_category_column(frame, "factory_name", config.FACTORY_NAME_MAPPING)
    frame = cc.normalize_problem_type_column(frame, config.VALID_PROBLEM_TYPES)
    frame = cc.parse_mixed_format_dates(frame, config.NOTE_DATE_COLUMNS)

    frame = remove_markup_artifacts(frame, config.NOTE_TEXT_COLUMN)
    frame = normalize_note_whitespace(frame, config.NOTE_TEXT_COLUMN)
    # Markup removal can leave a note that was only markup as an empty string.
    frame[config.NOTE_TEXT_COLUMN] = frame[config.NOTE_TEXT_COLUMN].replace("", np.nan)
    frame = drop_unusable_notes(frame, config.MINIMUM_NOTE_LENGTH)

    # Two notes sharing an identifier are the same note recorded twice.
    frame = frame.drop_duplicates(subset=[config.NOTE_IDENTIFIER_COLUMN], keep="first")
    frame = recompute_note_length(frame, config.NOTE_TEXT_COLUMN)
    frame = cc.resolve_remaining_gaps(frame, config.NOTE_DATE_COLUMNS)
    frame = cc.remove_duplicate_records(frame)

    save_processed_dataset(frame, output_path)
    return frame
