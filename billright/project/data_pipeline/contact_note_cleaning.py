"""The whole cleaning run for the contact notes extract."""
import re

import pandas as pd

from config import config
from data_pipeline.common_cleaning import (
    convert_markup_to_plain_text,
    convert_whole_numbers,
    format_price_year_dates,
    normalize_category_values,
    parse_price_year_dates,
    remove_duplicate_records,
    remove_rows_missing_target,
)
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset


def _lower_capitalised_notes(table):
    """A note written in capitals throughout is kept in lower case."""
    result = table.copy()
    result[config.NOTE_TEXT_COLUMN] = result[config.NOTE_TEXT_COLUMN].map(
        lambda text: text.lower() if isinstance(text, str) and text.isupper() else text)
    return result


def _remove_short_notes(table):
    words = table[config.NOTE_TEXT_COLUMN].map(
        lambda text: len(str(text).split()) if isinstance(text, str) else 0)
    return table[words >= config.MINIMUM_NOTE_WORDS].reset_index(drop=True)


def _split_timestamps(table):
    """Split note_written_at into a date part and a time part, refusing what will not split."""
    result = table.copy()
    dates, times, bad_values = [], [], []
    for value in result[config.NOTE_TIMESTAMP_COLUMN]:
        if not isinstance(value, str):
            dates.append(pd.NA)
            times.append(pd.NA)
            continue
        match = re.match(config.TIMESTAMP_PARTS_PATTERN, value.strip())
        if match is None:
            bad_values.append(value)
            dates.append(pd.NA)
            times.append(pd.NA)
            continue
        dates.append(match.group(config.NOTE_DATE_PART))
        times.append(match.group(config.NOTE_TIME_PART))
    if bad_values:
        raise ValueError(f"Column '{config.NOTE_TIMESTAMP_COLUMN}' holds timestamps that "
                         f"cannot be split into a date and a time: "
                         f"{list(dict.fromkeys(bad_values))}")
    result[config.NOTE_DATE_PART] = pd.Series(dates, index=result.index, dtype="str")
    result[config.NOTE_TIME_PART] = pd.Series(times, index=result.index, dtype="str")
    return result


def _write_timestamps(table):
    result = table.copy()
    day_first_rows = pd.Series([False] * len(result), dtype="boolean")
    result = parse_price_year_dates(result, [config.NOTE_DATE_PART], day_first_rows)
    result = format_price_year_dates(result, [config.NOTE_DATE_PART])
    written = []
    for date_text, time_text in zip(result[config.NOTE_DATE_PART], result[config.NOTE_TIME_PART]):
        if pd.isna(date_text) or pd.isna(time_text):
            written.append(pd.NA)
        else:
            written.append(f"{date_text} {time_text}")
    result[config.NOTE_TIMESTAMP_COLUMN] = pd.Series(written, index=result.index, dtype="str")
    return result.drop(columns=[config.NOTE_DATE_PART, config.NOTE_TIME_PART])


def clean_contact_note_dataset(input_file_path, output_file_path):
    """Produce notes whose words do not depend on how the tool that stored them wrote them."""
    table = load_raw_dataset(input_file_path, config.NULL_TOKENS)
    table = remove_duplicate_records(table)
    table = remove_rows_missing_target(table, config.NOTE_TARGET_COLUMN)
    table = normalize_category_values(table, config.NOTE_VALUE_MAPPINGS)
    table = convert_markup_to_plain_text(table, [config.NOTE_TEXT_COLUMN])
    table = _lower_capitalised_notes(table)
    table = _remove_short_notes(table)
    table = convert_whole_numbers(table, [config.NOTE_SEQUENCE_COLUMN])
    table[config.NOTE_LENGTH_COLUMN] = table[config.NOTE_TEXT_COLUMN].str.len().astype("Int64")
    table = _split_timestamps(table)
    table = _write_timestamps(table)
    save_processed_dataset(table, output_file_path)
    return table
