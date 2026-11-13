"""Cleans the repair job downtime dataset.

Owns the problem only this dataset has: repair cost stored as decorated text
such as "INR 12,345". The yes/no flags and problem type label are fixed here too.
"""

import re

from config import config
from data_pipeline import common_cleaning as cc
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset

CATEGORY_MAPPINGS = {
    "machine_type": config.MACHINE_TYPE_MAPPING,
    "factory_name": config.FACTORY_NAME_MAPPING,
    "importance": config.IMPORTANCE_MAPPING,
    "usage_pattern": config.USAGE_PATTERN_MAPPING,
}

CURRENCY_DECORATION_PATTERN = r"INR|Rs\.?|₹|,"


def strip_currency_formatting(dataframe, currency_columns):
    """Remove the currency marker and thousands separators, leaving number text."""
    cleaned = dataframe.copy()
    for column_name in currency_columns:
        cleaned[column_name] = (
            cleaned[column_name]
            .str.replace(CURRENCY_DECORATION_PATTERN, "", regex=True, flags=re.IGNORECASE)
            .str.strip()
        )
    return cleaned


def clean_downtime_dataset(input_path, output_path):
    """Clean one raw downtime file (train or eval, identically) and save it."""
    frame = load_raw_dataset(input_path, config.NULL_TOKEN_LIST)

    frame = cc.strip_text_whitespace(frame)
    frame = cc.replace_missing_tokens(frame, config.NULL_TOKEN_LIST)
    frame = cc.standardize_machine_code(frame)
    for column_name, value_mapping in CATEGORY_MAPPINGS.items():
        frame = cc.normalize_category_column(frame, column_name, value_mapping)
    frame = cc.normalize_problem_type_column(frame, config.VALID_PROBLEM_TYPES)
    frame = strip_currency_formatting(frame, config.CURRENCY_COLUMNS)
    frame = cc.parse_mixed_format_dates(frame, config.DOWNTIME_DATE_COLUMNS)
    frame = cc.convert_text_to_numeric(frame, config.DOWNTIME_NUMERIC_COLUMNS)
    frame = cc.normalize_boolean_columns(frame, config.DOWNTIME_BOOLEAN_COLUMNS)
    frame = cc.remove_out_of_range_measurements(frame, config.DOWNTIME_RANGE_LIMITS)
    frame = cc.remove_duplicate_records(frame)

    frame = cc.remove_rows_missing_target(frame, config.DOWNTIME_TARGET_COLUMN)
    frame = cc.resolve_missing_measurements(frame, config.DOWNTIME_NUMERIC_COLUMNS)
    frame = cc.resolve_missing_categories(frame, config.DOWNTIME_CATEGORY_COLUMNS)
    frame = cc.resolve_remaining_gaps(frame, config.DOWNTIME_DATE_COLUMNS)
    frame = cc.remove_duplicate_records(frame)

    save_processed_dataset(frame, output_path)
    return frame
