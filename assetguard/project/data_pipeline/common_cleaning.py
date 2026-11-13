"""Repair steps shared by more than one dataset.

Each function fixes exactly one kind of problem and returns a new table; the
table passed in is never modified.
"""

import re

import numpy as np
import pandas as pd

from config import config

MACHINE_CODE_SHAPE = re.compile(r"^([A-Z]{3})([A-Z]{3})(\d{4})$")

# Every written date format found in the raw files. All numeric formats put the
# year first, so the day and month can never be swapped.
DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%d-%b-%Y", "%d %B %Y", "%d %b %Y", "%d-%B-%Y"]


def _text_columns(dataframe):
    return [name for name in dataframe.columns if pd.api.types.is_string_dtype(dataframe[name])]


def strip_text_whitespace(dataframe):
    """Remove leading and trailing spaces from every text value."""
    cleaned = dataframe.copy()
    for column_name in _text_columns(cleaned):
        cleaned[column_name] = cleaned[column_name].str.strip()
    return cleaned


def replace_missing_tokens(dataframe, null_tokens):
    """Empty any cell whose whole content is a missing-value token."""
    tokens = {token.strip() for token in null_tokens}
    cleaned = dataframe.copy()
    for column_name in _text_columns(cleaned):
        is_token = cleaned[column_name].str.strip().isin(tokens)
        cleaned[column_name] = cleaned[column_name].where(~is_token, np.nan)
    return cleaned


def remove_duplicate_records(dataframe):
    """Drop rows identical to an earlier row and renumber the rest."""
    return dataframe.drop_duplicates(keep="first").reset_index(drop=True)


def _standard_machine_code(raw_code):
    if pd.isna(raw_code):
        return raw_code
    letters_and_digits = re.sub(r"[^A-Za-z0-9]", "", str(raw_code)).upper()
    match = MACHINE_CODE_SHAPE.match(letters_and_digits)
    if match:
        return "-".join(match.groups())
    return letters_and_digits


def standardize_machine_code(dataframe):
    """Rewrite every machine tag as AAA-AAA-9999, rebuilt from its three parts."""
    cleaned = dataframe.copy()
    cleaned["machine_code"] = cleaned["machine_code"].map(_standard_machine_code)
    return cleaned


def _lookup_key(value):
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def normalize_category_column(dataframe, column_name, value_mapping):
    """Map every spelling of a category onto its correct value; unknown spellings become empty."""
    cleaned = dataframe.copy()
    cleaned[column_name] = cleaned[column_name].map(
        lambda value: value if pd.isna(value) else value_mapping.get(_lookup_key(value), np.nan)
    )
    return cleaned


def normalize_problem_type_column(dataframe, valid_problem_types):
    """Match problem type labels regardless of underscores, padding and case."""
    by_key = {label.lower(): label for label in valid_problem_types}
    cleaned = dataframe.copy()
    cleaned["problem_type"] = cleaned["problem_type"].map(
        lambda value: value if pd.isna(value) else by_key.get(_lookup_key(str(value).replace("_", " ")), np.nan)
    )
    return cleaned


def parse_mixed_format_dates(dataframe, date_columns):
    """Read each date in whichever of the known formats it was written in."""
    cleaned = dataframe.copy()
    for column_name in date_columns:
        if column_name not in cleaned.columns:
            continue
        text = cleaned[column_name]
        parsed = pd.Series(pd.NaT, index=text.index, dtype="datetime64[ns]")
        for date_format in DATE_FORMATS:
            attempt = pd.to_datetime(text, format=date_format, errors="coerce")
            parsed = parsed.fillna(attempt)
        cleaned[column_name] = parsed
    return cleaned


def convert_text_to_numeric(dataframe, numeric_columns):
    """Strip units, thousands separators and percent signs, then read the number."""
    cleaned = dataframe.copy()
    for column_name in numeric_columns:
        if column_name not in cleaned.columns:
            continue
        if pd.api.types.is_numeric_dtype(cleaned[column_name]):
            continue
        text = cleaned[column_name].astype("string")
        text = text.str.replace(config.UNIT_SUFFIX_PATTERN, "", regex=True, flags=re.IGNORECASE)
        text = text.str.replace(config.THOUSANDS_AND_PERCENT_PATTERN, "", regex=True)
        cleaned[column_name] = pd.to_numeric(text.str.strip(), errors="coerce")
    return cleaned


def normalize_boolean_columns(dataframe, boolean_columns):
    """Turn every way of writing yes/no into 1 or 0."""
    true_tokens = {token.lower() for token in config.BOOLEAN_TRUE_TOKENS}
    cleaned = dataframe.copy()
    for column_name in boolean_columns:
        if column_name not in cleaned.columns:
            continue
        is_true = cleaned[column_name].astype("string").str.strip().str.lower().isin(true_tokens)
        cleaned[column_name] = is_true.fillna(False).astype(int)
    return cleaned


def remove_out_of_range_measurements(dataframe, range_limits):
    """Empty readings outside their column's limits; the row itself survives."""
    cleaned = dataframe.copy()
    for column_name, (lowest, highest) in range_limits.items():
        if column_name not in cleaned.columns:
            continue
        values = cleaned[column_name]
        outside = values.notna() & ((values < lowest) | (values > highest))
        cleaned[column_name] = values.where(~outside, np.nan)
    return cleaned


def remove_rows_missing_target(dataframe, target_column):
    """Drop rows with no recorded answer and renumber the rest."""
    return dataframe.dropna(subset=[target_column]).reset_index(drop=True)


def resolve_missing_measurements(dataframe, numeric_columns):
    """Fill gaps in each measurement column with that column's median."""
    cleaned = dataframe.copy()
    for column_name in numeric_columns:
        if column_name not in cleaned.columns:
            continue
        cleaned[column_name] = cleaned[column_name].fillna(cleaned[column_name].median())
    return cleaned


def resolve_missing_categories(dataframe, category_columns):
    """Fill gaps in each category column with the configured 'Unknown' value."""
    cleaned = dataframe.copy()
    for column_name in category_columns:
        if column_name not in cleaned.columns:
            continue
        cleaned[column_name] = cleaned[column_name].fillna(config.UNKNOWN_CATEGORY_VALUE)
    return cleaned


def resolve_remaining_gaps(dataframe, date_columns):
    """Fill whatever the measurement and category steps did not cover.

    Not one of the specified steps: the cleaned files must hold no empty cell, and
    identifier text and unreadable dates are neither measurements nor categories.
    Dates take the column's middle date, matching the median rule for measurements;
    any other text takes the configured 'Unknown' value.
    """
    cleaned = dataframe.copy()
    for column_name in date_columns:
        if column_name in cleaned.columns:
            cleaned[column_name] = cleaned[column_name].fillna(cleaned[column_name].median())
    return resolve_missing_categories(cleaned, _text_columns(cleaned))
