"""Cleans the machine breakdown risk dataset.

Owns the two problems only this dataset has: temperatures recorded in
Fahrenheit, and vibration readings spiking far above what the sensor could see.
"""

import numpy as np

from config import config
from data_pipeline import common_cleaning as cc
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset

CATEGORY_MAPPINGS = {
    "machine_type": config.MACHINE_TYPE_MAPPING,
    "factory_name": config.FACTORY_NAME_MAPPING,
    "importance": config.IMPORTANCE_MAPPING,
    "usage_pattern": config.USAGE_PATTERN_MAPPING,
}


def correct_temperature_units(dataframe, temperature_columns):
    """Convert readings above the Fahrenheit detection limit to Celsius."""
    cleaned = dataframe.copy()
    for column_name in temperature_columns:
        values = cleaned[column_name]
        is_fahrenheit = values > config.FAHRENHEIT_DETECTION_LIMIT
        celsius = ((values - 32.0) * 5.0 / 9.0).round(1)
        cleaned[column_name] = values.where(~is_fahrenheit, celsius)
    return cleaned


def suppress_sensor_spikes(dataframe, vibration_columns):
    """Empty vibration readings above Q3 + k * IQR of their own column."""
    cleaned = dataframe.copy()
    for column_name in vibration_columns:
        values = cleaned[column_name]
        lower_quartile, upper_quartile = values.quantile(0.25), values.quantile(0.75)
        spike_limit = upper_quartile + config.OUTLIER_IQR_MULTIPLIER * (upper_quartile - lower_quartile)
        cleaned[column_name] = values.where(~(values > spike_limit), np.nan)
    return cleaned


def clean_breakdown_dataset(input_path, output_path):
    """Clean one raw breakdown file (train or eval, identically) and save it."""
    frame = load_raw_dataset(input_path, config.NULL_TOKEN_LIST)

    # Row-by-row repairs: after these, two rows that differ only in spelling,
    # padding or units are identical and can be recognised as duplicates.
    frame = cc.strip_text_whitespace(frame)
    frame = cc.replace_missing_tokens(frame, config.NULL_TOKEN_LIST)
    frame = cc.standardize_machine_code(frame)
    for column_name, value_mapping in CATEGORY_MAPPINGS.items():
        frame = cc.normalize_category_column(frame, column_name, value_mapping)
    frame = cc.parse_mixed_format_dates(frame, config.BREAKDOWN_DATE_COLUMNS)
    frame = cc.convert_text_to_numeric(frame, config.BREAKDOWN_NUMERIC_COLUMNS)
    frame = correct_temperature_units(frame, config.TEMPERATURE_COLUMNS)
    frame = cc.remove_out_of_range_measurements(frame, config.BREAKDOWN_RANGE_LIMITS)
    frame = cc.remove_duplicate_records(frame)

    # Column-wide repairs, which depend on the spread of the surviving rows.
    frame = suppress_sensor_spikes(frame, config.VIBRATION_COLUMNS)
    frame = cc.remove_rows_missing_target(frame, config.BREAKDOWN_TARGET_COLUMN)
    frame[config.BREAKDOWN_TARGET_COLUMN] = frame[config.BREAKDOWN_TARGET_COLUMN].astype(int)
    frame = cc.resolve_missing_measurements(frame, config.BREAKDOWN_NUMERIC_COLUMNS)
    frame = cc.resolve_missing_categories(frame, config.BREAKDOWN_CATEGORY_COLUMNS)
    frame = cc.resolve_remaining_gaps(frame, config.BREAKDOWN_DATE_COLUMNS)
    frame = cc.remove_duplicate_records(frame)

    save_processed_dataset(frame, output_path)
    return frame
