import re, html
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import numpy as np
from config import config as c


def _map(series, fn, dtype=None):
    bad = []

    def read(v):
        if pd.isna(v):
            return np.nan
        try:
            return fn(str(v))
        except (ValueError, KeyError, AttributeError, TypeError):
            bad.append(v)
            return np.nan

    out = series.map(read)
    if bad:
        raise ValueError(
            f"{series.name}: unrecognised values {sorted(set(map(str,bad)))}"
        )
    return out.astype(dtype) if dtype else out


def remove_duplicate_records(dataframe):
    return dataframe.drop_duplicates().reset_index(drop=True)


def refuse_missing_values(dataframe, required_columns):
    for col in required_columns:
        n = int(dataframe[col].isna().sum())
        if n:
            raise ValueError(f"{col}: {n} rows missing")
    return dataframe.copy()


def refuse_repeated_references(dataframe, reference_columns):
    dup = dataframe.duplicated(reference_columns, keep=False)
    if dup.any():
        raise ValueError(
            f'{reference_columns}: repeated {dataframe.loc[dup,reference_columns].to_dict("records")}'
        )
    return dataframe.copy()


def remove_rows_missing_target(dataframe, target_column):
    return dataframe.dropna(subset=[target_column]).reset_index(drop=True)


def normalize_category_values(dataframe, value_mappings):
    f = dataframe.copy()
    for col, mapping in value_mappings.items():
        f[col] = _map(f[col], lambda v: mapping[v.lower()])
    return f


def normalize_name_spacing(dataframe, name_columns):
    f = dataframe.copy()
    for col in name_columns:
        f[col] = _map(
            f[col], lambda v: re.sub(c.WHITESPACE_RUN_PATTERN, " ", v).strip()
        )
    return f


def convert_identifiers(identifiers, notation_pattern, canonical_format):
    return _map(
        identifiers,
        lambda v: re.fullmatch(notation_pattern, v).expand(canonical_format),
    )


def _number(dataframe, patterns, dtype):
    f = dataframe.copy()
    for col, p in patterns.items():
        f[col] = _map(f[col], lambda v: float(re.fullmatch(p, v).group(1)), dtype)
    return f


def convert_whole_numbers(dataframe, number_patterns):
    return _number(dataframe, number_patterns, "Int64")


def convert_decimal_numbers(dataframe, number_patterns):
    return _number(dataframe, number_patterns, "float64")


def convert_durations_to_whole_weeks(durations):
    def read(v):
        m = re.fullmatch(c.TREATMENT_DURATION_PATTERN, v)
        if not m:
            raise ValueError(v)
        return (
            int(m[c.TREATMENT_WEEKS_PART])
            if m[c.TREATMENT_WEEKS_PART]
            else int(m[c.TREATMENT_DAYS_PART]) // c.DAYS_PER_WEEK
        )

    return _map(durations, read, "Int64")


def convert_asa_classes(asa_classes):
    return _map(
        asa_classes,
        lambda v: c.ASA_CLASS_NUMBERS[re.fullmatch(c.ASA_CLASS_PATTERN, v).group(1)],
        "Int64",
    )


def convert_measurements(measurements, notations, units):
    def read(v):
        for p in notations.values():
            m = re.fullmatch(p, v)
            if m:
                n = sum(
                    Decimal(x) * Decimal(units[k])
                    for k, x in m.groupdict().items()
                    if x is not None
                )
                if n <= 0:
                    raise ValueError(v)
                return float(n.quantize(c.MEASUREMENT_STEP, rounding=ROUND_HALF_UP))
        raise ValueError(v)

    return _map(measurements, read)


def convert_condition_lists(condition_lists):
    def read(v):
        if v.lower() in c.NO_OTHER_CONDITIONS_SPELLINGS:
            return c.NO_OTHER_CONDITIONS
        return c.CONDITION_SEPARATOR.join(
            sorted(
                set(
                    c.CONDITION_MAPPING[x.lower()]
                    for x in re.split(c.CONDITION_LIST_SEPARATOR_PATTERN, v)
                )
            )
        )

    return _map(condition_lists, read)


def treat_values_below_minimum_as_missing(dataframe, minimum_values):
    f = dataframe.copy()
    for col, n in minimum_values.items():
        f[col] = f[col].mask(f[col] < n)
    return f


def treat_values_above_maximum_as_missing(dataframe, maximum_values):
    f = dataframe.copy()
    for col, n in maximum_values.items():
        f[col] = f[col].mask(f[col] > n)
    return f


def keep_latest_submission_of_each_request(dataframe):
    cols = [c.REQUEST_REFERENCE_COLUMN, c.SUBMISSION_SEQUENCE_COLUMN]
    refuse_missing_values(dataframe, cols)
    refuse_repeated_references(dataframe, cols)
    idx = dataframe.groupby(cols[0])[cols[1]].idxmax()
    return dataframe.loc[dataframe.index.isin(idx)].reset_index(drop=True)


def convert_markup_to_plain_text(texts):
    return _map(
        texts,
        lambda v: re.sub(
            c.WHITESPACE_RUN_PATTERN,
            " ",
            re.sub(c.MARKUP_PATTERN, " ", html.unescape(v)),
        ).strip(),
    )


def clean_clinical_text(texts):
    return convert_markup_to_plain_text(texts).map(
        lambda v: v.lower() if isinstance(v, str) and v.isupper() else v
    )
