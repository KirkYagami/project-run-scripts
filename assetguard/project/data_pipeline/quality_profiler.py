"""Measures how dirty a raw table is, before any cleaning touches it.

It only counts; it never repairs. Every value it produces is a plain Python
type so the report can be written as JSON.
"""

import json
import re

import pandas as pd

from config import config


def count_missing_values(dataframe):
    """Empty cells per column, for columns with at least one."""
    missing = dataframe.isna().sum()
    return {name: int(count) for name, count in missing.items() if count > 0}


def count_duplicate_records(dataframe):
    """Rows that repeat an earlier row across every column."""
    return int(dataframe.duplicated(keep="first").sum())


def count_out_of_range_values(dataframe, range_limits):
    """Readings outside their column's limits, read from raw text."""
    counts = {}
    for column_name, (lowest, highest) in range_limits.items():
        if column_name not in dataframe.columns:
            continue
        text = dataframe[column_name].astype("string")
        text = text.str.replace(config.UNIT_SUFFIX_PATTERN, "", regex=True, flags=re.IGNORECASE)
        text = text.str.replace(config.THOUSANDS_AND_PERCENT_PATTERN, "", regex=True)
        values = pd.to_numeric(text.str.strip(), errors="coerce")
        offending = int(((values < lowest) | (values > highest)).sum())
        if offending > 0:
            counts[column_name] = offending
    return counts


def build_quality_report(dataframe, dataset_name, range_limits):
    """One record describing the quality of a single raw dataset."""
    return {
        "dataset_name": dataset_name,
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "duplicate_rows": count_duplicate_records(dataframe),
        "missing_values": count_missing_values(dataframe),
        "out_of_range_values": count_out_of_range_values(dataframe, range_limits),
    }


def save_quality_report(report_records, output_path):
    """Write all records to one readable JSON file and return its path."""
    with open(output_path, "w", encoding="utf-8") as report_file:
        json.dump(report_records, report_file, indent=2, ensure_ascii=False)
    return output_path
