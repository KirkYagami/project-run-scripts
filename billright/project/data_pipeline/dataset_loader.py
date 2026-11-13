"""Reads tables from disk and writes them back.

This is the only place in the data preparation section that touches CSV files.
"""
import os

import pandas as pd


def load_raw_dataset(file_path, null_tokens):
    """Read one CSV as text, trim every value and turn "missing" tokens into NaN."""
    dataframe = pd.read_csv(file_path, dtype=str, keep_default_na=False, na_filter=False)
    tokens = {token.strip().lower() for token in null_tokens}
    cleaned_columns = {}
    for column in dataframe.columns:
        trimmed = dataframe[column].astype(str).str.strip()
        is_missing = trimmed.str.lower().isin(tokens)
        cleaned_columns[column] = trimmed.mask(is_missing, pd.NA)
    return pd.DataFrame(cleaned_columns, index=dataframe.index)


def load_processed_dataset(file_path):
    """Read a table the pipeline has already cleaned, typing columns from contents."""
    return pd.read_csv(file_path)


def save_processed_dataset(dataframe, file_path):
    """Write a cleaned table, creating its folder and adding no index column."""
    folder = os.path.dirname(file_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    dataframe.to_csv(file_path, index=False)
