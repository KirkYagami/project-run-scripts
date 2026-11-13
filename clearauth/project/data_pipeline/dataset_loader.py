from pathlib import Path
import pandas as pd
from config import config as c


def load_raw_dataset(file_path):
    f = pd.read_csv(file_path, dtype=str, keep_default_na=False).apply(
        lambda col: col.str.strip()
    )
    return f.apply(lambda col: col.mask(col.str.lower().isin(c.NULL_TOKENS)))


def save_processed_dataset(dataframe, file_path):
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(file_path, index=False)


def load_processed_dataset(file_path):
    return pd.read_csv(
        file_path, keep_default_na=False, na_values=[""], low_memory=False
    )
