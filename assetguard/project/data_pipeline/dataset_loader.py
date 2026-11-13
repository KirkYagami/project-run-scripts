"""Reads tables from disk and writes them back.

The only module in data preparation that touches CSV files. Raw files are read
with every column as text so nothing is guessed; cleaned files are read with
their types inferred because cleaning has already made them trustworthy.
"""

import pandas as pd


def load_raw_dataset(file_path, null_tokens):
    """Load one raw CSV with every column as text and every missing token empty."""
    return pd.read_csv(
        file_path,
        dtype=str,
        na_values=null_tokens,
        keep_default_na=True,
    )


def load_processed_dataset(file_path):
    """Load a cleaned CSV, letting pandas type the columns from their contents."""
    return pd.read_csv(file_path)


def save_processed_dataset(dataframe, file_path):
    """Write a cleaned table without the row index and return where it went."""
    dataframe.to_csv(file_path, index=False)
    return file_path
