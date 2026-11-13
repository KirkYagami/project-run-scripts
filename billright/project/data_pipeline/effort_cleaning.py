"""The whole cleaning run for one resolution effort extract."""
import pandas as pd

from config import config
from data_pipeline.common_cleaning import (
    convert_counts_with_units,
    convert_durations_to_hours,
    convert_money_amounts,
    convert_whole_numbers,
    format_price_year_dates,
    normalize_category_values,
    parse_price_year_dates,
    remove_duplicate_records,
    remove_rows_missing_target,
    treat_out_of_range_as_missing,
)
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset


def clean_effort_dataset(input_file_path, output_file_path):
    """Produce an effort table the effort model can be fitted on and scored against."""
    table = load_raw_dataset(input_file_path, config.NULL_TOKENS)
    table = remove_duplicate_records(table)
    table = normalize_category_values(table, config.EFFORT_VALUE_MAPPINGS)
    day_first_rows = pd.Series([False] * len(table), dtype="boolean")
    table = parse_price_year_dates(table, config.EFFORT_DATE_COLUMNS, day_first_rows)
    table = convert_money_amounts(table, config.EFFORT_MONEY_COLUMNS)
    table = convert_durations_to_hours(table, config.EFFORT_DURATION_COLUMNS)
    table = convert_counts_with_units(table, config.EFFORT_COUNT_WITH_UNIT_PATTERNS)
    table = convert_whole_numbers(table, config.EFFORT_WHOLE_NUMBER_COLUMNS)
    table = treat_out_of_range_as_missing(table, config.EFFORT_RANGE_LIMITS)
    table = remove_rows_missing_target(table, config.EFFORT_TARGET_COLUMN)
    table = format_price_year_dates(table, config.EFFORT_DATE_COLUMNS)
    save_processed_dataset(table, output_file_path)
    return table
