"""Measures how dirty each raw extract was and what cleaning did to it.

Every figure is measured from the tables themselves.
"""
import json
import os
import re

import pandas as pd

from config import config
from data_pipeline.common_cleaning import (
    convert_counts_with_units,
    convert_durations_to_hours,
    convert_energy_to_kwh,
    convert_markup_to_plain_text,
    convert_money_amounts,
    convert_whole_numbers,
    normalize_category_values,
    parse_price_year_dates,
)


# ----------------------------------------------------------------- helpers
def _non_empty(series):
    return series.dropna()


def _count_matching(series, pattern, flags=0):
    return int(sum(1 for value in _non_empty(series) if re.search(pattern, str(value), flags)))


def _count_not_matching(series, pattern):
    return int(sum(1 for value in _non_empty(series) if not re.match(pattern, str(value))))


def _missing_by_column(frame):
    counts = frame.isna().sum()
    return {column: int(count) for column, count in counts.items() if count > 0}


def _shares(series):
    total = len(series)
    if total == 0:
        return {}
    return {str(value): round(int(count) / total, 4)
            for value, count in series.value_counts().items()}


def _first_copies(frame):
    return frame[~frame.duplicated(keep="first")]


def _day_first_rows(frame):
    return pd.Series([False] * len(frame), index=frame.index, dtype="boolean")


def _month_first_rows(raw_frame):
    folded = normalize_category_values(
        raw_frame, {config.BILLING_SYSTEM_COLUMN: config.BILLING_SYSTEM_MAPPING})
    return folded[config.BILLING_SYSTEM_COLUMN].map(
        config.MONTH_FIRST_BY_BILLING_SYSTEM).astype("boolean")


def _word_count(text):
    return len(str(text).split())


# ------------------------------------------------------------ general profile
def profile_dataset(raw_frame, clean_frame, target_column):
    """Account for every row an extract arrived with."""
    rows_received = int(len(raw_frame))
    rows_kept = int(len(clean_frame))
    first_copies = _first_copies(raw_frame)
    return {
        "rows_received": rows_received,
        "rows_kept": rows_kept,
        "rows_removed": rows_received - rows_kept,
        "duplicate_rows": int(raw_frame.duplicated(keep="first").sum()),
        "rows_missing_target": int(first_copies[target_column].isna().sum()),
        "columns": int(clean_frame.shape[1]),
        "missing_cells_as_received": _missing_by_column(raw_frame),
        "missing_cells_after_cleaning": _missing_by_column(clean_frame),
    }


# ---------------------------------------------------------- disputes details
def _day_numbers(frame, month_first_rows):
    return parse_price_year_dates(frame, config.DISPUTE_DATE_COLUMNS, month_first_rows)


def _bills_ending_before_start(day_numbers):
    ended_early = day_numbers[config.BILL_END_COLUMN] < day_numbers[config.BILL_START_COLUMN]
    return int(ended_early.fillna(False).sum())


def _days_billed_disagreeing(day_numbers, days_billed):
    expected = day_numbers[config.BILL_END_COLUMN] - day_numbers[config.BILL_START_COLUMN] + 1
    disagree = (days_billed != expected)
    return int(disagree.fillna(False).sum())


def profile_dispute_details(raw_frame, clean_frame):
    """Show the defects peculiar to the disputes extracts, as received and after cleaning."""
    date_columns = config.DISPUTE_DATE_COLUMNS
    month_first = _month_first_rows(raw_frame)

    not_standard = sum(_count_not_matching(raw_frame[column], config.STANDARD_DATE_PATTERN)
                       for column in date_columns)
    numeric_on_month_first_rows = 0
    for column in date_columns:
        for value, writes_month_first in zip(raw_frame[column], month_first):
            if (isinstance(value, str) and bool(writes_month_first is True or writes_month_first == True)  # noqa: E712
                    and re.match(config.NUMERIC_DATE_PATTERN, value.lower())):
                numeric_on_month_first_rows += 1

    raw_days = _day_numbers(raw_frame, month_first)
    impossible = 0
    for column in date_columns:
        impossible += int((raw_frame[column].notna() & raw_days[column].isna()).sum())

    money_and_energy = config.DISPUTE_MONEY_COLUMNS + config.DISPUTE_ENERGY_COLUMNS
    not_plain_numbers = {column: _count_not_matching(raw_frame[column], config.PLAIN_NUMBER_PATTERN)
                         for column in money_and_energy}
    credits = {column: _count_matching(raw_frame[column].astype("object").str.lower()
                                       .where(raw_frame[column].notna()),
                                       config.CREDIT_NOTATION_PATTERN)
               for column in config.DISPUTE_MONEY_COLUMNS}

    converted = convert_whole_numbers(raw_frame, [config.DAYS_BILLED_COLUMN]
                                      + list(config.DISPUTE_RANGE_LIMITS))
    out_of_range = {}
    for column, (lowest, highest) in config.DISPUTE_RANGE_LIMITS.items():
        values = converted[column]
        out_of_range[column] = int(((values < lowest) | (values > highest)).fillna(False).sum())

    raw_energy = convert_energy_to_kwh(raw_frame, config.DISPUTE_ENERGY_COLUMNS)
    clean_days = _day_numbers(clean_frame, _day_first_rows(clean_frame))
    clean_energy = clean_frame[config.BILLED_UNITS_COLUMN]

    return {
        "dates_not_in_standard_form": int(not_standard),
        "dates_written_month_first": int(numeric_on_month_first_rows),
        "dates_impossible_in_the_calendar": int(impossible),
        "values_not_written_as_plain_numbers": not_plain_numbers,
        "money_written_as_credits": credits,
        "out_of_range_by_column": out_of_range,
        "target_shares": _shares(clean_frame[config.DISPUTE_TARGET_COLUMN]),
        "bills_ending_before_they_start_as_received": _bills_ending_before_start(raw_days),
        "bills_ending_before_they_start_after_cleaning": _bills_ending_before_start(clean_days),
        "days_billed_disagreeing_with_dates_as_received": _days_billed_disagreeing(
            raw_days, converted[config.DAYS_BILLED_COLUMN]),
        "days_billed_disagreeing_with_dates_after_cleaning": _days_billed_disagreeing(
            clean_days, clean_frame[config.DAYS_BILLED_COLUMN]),
        "usage_written_negative_as_received": int(
            (raw_energy[config.BILLED_UNITS_COLUMN] < 0).fillna(False).sum()),
        "usage_written_negative_after_cleaning": int((clean_energy < 0).fillna(False).sum()),
    }


# ------------------------------------------------------------ effort details
def profile_effort_details(raw_frame, clean_frame):
    """Show the defects peculiar to the effort extracts."""
    unit_columns = list(config.EFFORT_DURATION_COLUMNS) + list(
        config.EFFORT_COUNT_WITH_UNIT_PATTERNS)
    not_plain_numbers = {column: _count_not_matching(raw_frame[column], config.PLAIN_NUMBER_PATTERN)
                         for column in unit_columns}

    converted = convert_durations_to_hours(raw_frame, config.EFFORT_DURATION_COLUMNS)
    converted = convert_counts_with_units(converted, config.EFFORT_COUNT_WITH_UNIT_PATTERNS)
    converted = convert_whole_numbers(converted, ["analyst_open_disputes_count"])
    out_of_range = {}
    for column, (lowest, highest) in config.EFFORT_RANGE_LIMITS.items():
        values = converted[column]
        out_of_range[column] = int(((values < lowest) | (values > highest)).fillna(False).sum())

    lowest_hours, highest_hours = config.EFFORT_RANGE_LIMITS[config.EFFORT_TARGET_COLUMN]
    first_copy_hours = convert_durations_to_hours(
        _first_copies(raw_frame), config.EFFORT_DURATION_COLUMNS)[config.EFFORT_TARGET_COLUMN]
    impossible_hours = ((first_copy_hours < lowest_hours) | (first_copy_hours > highest_hours))

    return {
        "dates_not_in_standard_form": sum(
            _count_not_matching(raw_frame[column], config.STANDARD_DATE_PATTERN)
            for column in config.EFFORT_DATE_COLUMNS),
        "values_not_written_as_plain_numbers": not_plain_numbers,
        "out_of_range_by_column": out_of_range,
        "median_resolution_hours": float(clean_frame[config.EFFORT_TARGET_COLUMN].median()),
        "rows_with_impossible_target": int(impossible_hours.fillna(False).sum()),
    }


# ------------------------------------------------------------- note details
def profile_note_details(raw_frame, clean_frame):
    """Show the defects peculiar to free-text notes."""
    raw_text = raw_frame[config.NOTE_TEXT_COLUMN]
    plain = convert_markup_to_plain_text(raw_frame, [config.NOTE_TEXT_COLUMN])
    plain_text = plain[config.NOTE_TEXT_COLUMN]

    raw_lengths = pd.to_numeric(raw_frame[config.NOTE_LENGTH_COLUMN], errors="coerce")
    plain_lengths = plain_text.str.len()
    raw_disagree = (raw_lengths != plain_lengths) & plain_text.notna()

    clean_lengths = pd.to_numeric(clean_frame[config.NOTE_LENGTH_COLUMN], errors="coerce")
    clean_disagree = clean_lengths != clean_frame[config.NOTE_TEXT_COLUMN].str.len()

    first_copy_mask = ~raw_frame.duplicated(keep="first")
    carries_answer = raw_frame[config.NOTE_TARGET_COLUMN].notna()
    too_few_words = plain_text.map(lambda text: isinstance(text, str)
                                   and _word_count(text) < config.MINIMUM_NOTE_WORDS)

    shortest = (int(clean_frame[config.NOTE_TEXT_COLUMN].map(_word_count).min())
                if len(clean_frame) else 0)

    return {
        "timestamps_not_in_standard_form": _count_not_matching(
            raw_frame[config.NOTE_TIMESTAMP_COLUMN], config.STANDARD_TIMESTAMP_PATTERN),
        "notes_with_markup": _count_matching(raw_text, config.MARKUP_PATTERN),
        "notes_with_encoding_artifacts": _count_matching(raw_text,
                                                         config.ENCODING_ARTIFACT_PATTERN),
        "notes_in_capitals": int(sum(1 for text in plain_text
                                     if isinstance(text, str) and text.isupper())),
        "shortest_note_words": shortest,
        "target_shares": _shares(clean_frame[config.NOTE_TARGET_COLUMN]),
        "note_lengths_disagreeing_with_plain_text_as_received": int(raw_disagree.sum()),
        "note_lengths_disagreeing_with_plain_text_after_cleaning": int(clean_disagree.sum()),
        "rows_with_too_few_words": int((first_copy_mask & carries_answer & too_few_words).sum()),
    }


# ------------------------------------------------------------------- report
def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Cannot write {type(value).__name__} as JSON")


def write_quality_report(profiles, file_path):
    """Leave a record a reviewer can read: indented JSON with sorted keys."""
    folder = os.path.dirname(file_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as report_file:
        json.dump(profiles, report_file, indent=2, sort_keys=True, default=_json_default)
        report_file.write("\n")
