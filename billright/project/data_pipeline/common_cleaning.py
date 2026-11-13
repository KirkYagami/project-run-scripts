"""Repairs shared by more than one cleaning run, or by a cleaning run and its profiler.

Every function takes a table and returns a repaired copy. None reads or writes a
file and none removes a column. A value in a notation a function does not
recognise is refused with a ValueError naming the column and the values.
"""
import html
import re

import pandas as pd

from config import config


# ----------------------------------------------------------------- helpers
def _is_empty(value):
    """True for NaN / None / pd.NA and for text that is blank."""
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and value.strip() == ""


def _as_text(value):
    return str(value).strip()


def _refuse(column, bad_values):
    unique_values = list(dict.fromkeys(bad_values))
    raise ValueError(f"Column '{column}' holds values in a notation that is not "
                     f"recognised: {unique_values}")


def _convert_column(dataframe, column, converter, dtype):
    """Apply converter to every non-empty value of a column, refusing the bad ones."""
    converted = []
    bad_values = []
    for value in dataframe[column]:
        if _is_empty(value):
            converted.append(pd.NA)
            continue
        result = converter(_as_text(value))
        if result is None:
            bad_values.append(_as_text(value))
            converted.append(pd.NA)
        else:
            converted.append(result)
    if bad_values:
        _refuse(column, bad_values)
    return pd.Series(converted, index=dataframe.index, dtype=dtype)


# ------------------------------------------------------------ record repairs
def remove_duplicate_records(dataframe):
    """Drop rows repeated in every column, keeping the first of each."""
    return dataframe.drop_duplicates(keep="first").reset_index(drop=True)


def normalize_category_values(dataframe, value_mappings):
    """Fold every spelling of a category onto its canonical value."""
    result = dataframe.copy()
    for column, mapping in value_mappings.items():
        if column not in result.columns:
            continue
        lowered_mapping = {key.strip().lower(): value for key, value in mapping.items()}
        folded = []
        bad_values = []
        for value in result[column]:
            if _is_empty(value):
                folded.append(value)
                continue
            canonical = lowered_mapping.get(_as_text(value).lower())
            if canonical is None:
                bad_values.append(_as_text(value))
                folded.append(value)
            else:
                folded.append(canonical)
        if bad_values:
            _refuse(column, bad_values)
        result[column] = pd.Series(folded, index=result.index, dtype="object")
    return result


# --------------------------------------------------------------------- dates
def _read_one_date(text, month_first):
    """Return a price-year day number, or None for a day the year lacks.

    Raises ValueError for a notation nobody recognises.
    """
    lowered = text.strip().lower()
    numeric = re.match(config.NUMERIC_DATE_PATTERN, lowered)
    if numeric:
        if month_first is None or pd.isna(month_first):
            raise ValueError(text)
        first_part, second_part = int(numeric.group(1)), int(numeric.group(2))
        day_of_month, month_number = ((second_part, first_part) if bool(month_first)
                                      else (first_part, second_part))
        month_name = config.MONTH_BY_NUMBER.get(month_number)
        if month_name is None:
            return None
    else:
        worded = re.match(config.WORDED_DATE_PATTERN, lowered)
        if not worded:
            raise ValueError(text)
        day_of_month = int(worded.group(1))
        month_name = config.MONTH_NAME_MAPPING.get(worded.group(2))
        if month_name is None:
            raise ValueError(text)
    return config.DAY_NUMBER_BY_PRICE_YEAR_DATE.get(f"{day_of_month:02d} {month_name}")


def parse_price_year_dates(dataframe, date_columns, month_first_rows):
    """Turn every notation a day and month arrive in into a price-year day number."""
    result = dataframe.copy()
    month_first_values = list(pd.Series(month_first_rows).astype("object"))
    for column in date_columns:
        numbers = []
        bad_values = []
        for position, value in enumerate(result[column]):
            if _is_empty(value):
                numbers.append(pd.NA)
                continue
            month_first = (month_first_values[position]
                           if position < len(month_first_values) else None)
            try:
                day_number = _read_one_date(_as_text(value), month_first)
            except ValueError:
                bad_values.append(_as_text(value))
                numbers.append(pd.NA)
                continue
            numbers.append(pd.NA if day_number is None else day_number)
        if bad_values:
            _refuse(column, bad_values)
        result[column] = pd.Series(numbers, index=result.index, dtype="Int64")
    return result


def format_price_year_dates(dataframe, date_columns):
    """Write day numbers back as DD Mon."""
    result = dataframe.copy()
    for column in date_columns:
        written = [pd.NA if _is_empty(value) else config.PRICE_YEAR_DATE_BY_DAY_NUMBER[int(value)]
                   for value in result[column]]
        result[column] = pd.Series(written, index=result.index, dtype="str")
    return result


# --------------------------------------------------------------------- money
def _money_to_pounds(text):
    lowered = text.lower()
    if not re.match(config.MONEY_NOTATION_PATTERN, lowered):
        return None
    is_credit = re.search(config.CREDIT_NOTATION_PATTERN, lowered) is not None
    digits_only = re.sub(config.MONEY_SYMBOL_PATTERN, "", lowered)
    amount = float(digits_only)
    return -abs(amount) if is_credit else amount


def convert_money_amounts(dataframe, money_columns):
    """Turn every money notation into floating-point pounds, credits negative."""
    result = dataframe.copy()
    for column in money_columns:
        result[column] = _convert_column(result, column, _money_to_pounds,
                                         "Float64").astype("float64")
    return result


# -------------------------------------------------------------------- energy
def _energy_to_kwh(text):
    lowered = text.lower()
    match = re.match(config.ENERGY_READING_PATTERN, lowered)
    if not match:
        return None
    amount = float(match.group(1).replace(config.DIGIT_GROUPING_SEPARATOR, ""))
    factor = config.ENERGY_UNIT_FACTORS[match.group(2) or "kwh"]
    kilowatt_hours = round(amount * factor, config.UNIT_CONVERSION_DECIMALS)
    if kilowatt_hours != int(kilowatt_hours):
        return None
    return int(kilowatt_hours)


def convert_energy_to_kwh(dataframe, energy_columns):
    """Put every quantity of energy into whole kWh."""
    result = dataframe.copy()
    for column in energy_columns:
        result[column] = _convert_column(result, column, _energy_to_kwh, "Int64")
    return result


# ----------------------------------------------------------------- durations
def _duration_to_hours(text):
    lowered = text.lower()
    match = re.match(config.HOURS_AND_MINUTES_PATTERN, lowered)
    if match:
        return int(match.group(1)) + int(match.group(2)) / config.MINUTES_PER_HOUR
    match = re.match(config.MINUTES_UNIT_PATTERN, lowered)
    if match:
        return float(match.group(1)) / config.MINUTES_PER_HOUR
    match = re.match(config.HOURS_UNIT_PATTERN, lowered)
    if match:
        return float(match.group(1))
    if re.match(config.PLAIN_NUMBER_PATTERN, lowered):
        return float(lowered)
    return None


def convert_durations_to_hours(dataframe, duration_columns):
    """Put every duration into hours."""
    result = dataframe.copy()
    for column in duration_columns:
        result[column] = _convert_column(result, column, _duration_to_hours,
                                         "Float64").astype("float64")
    return result


# -------------------------------------------------------------------- counts
def convert_counts_with_units(dataframe, count_patterns):
    """Turn counts written with their unit into whole numbers."""
    result = dataframe.copy()
    for column, pattern in count_patterns.items():
        def to_count(text, pattern=pattern):
            match = re.match(pattern, text.lower())
            return int(match.group(1)) if match else None
        result[column] = _convert_column(result, column, to_count, "Int64")
    return result


def _plain_whole_number(text):
    if not re.match(config.PLAIN_NUMBER_PATTERN, text):
        return None
    number = float(text)
    if number != int(number):
        return None
    return int(number)


def convert_whole_numbers(dataframe, whole_number_columns):
    """Give every count and read a whole-number type that can still hold a gap."""
    result = dataframe.copy()
    for column in whole_number_columns:
        result[column] = _convert_column(result, column, _plain_whole_number, "Int64")
    return result


# ---------------------------------------------------------------------- text
def _plain_text(value):
    if _is_empty(value):
        return value
    text = re.sub(config.MARKUP_PATTERN, " ", str(value))
    text = html.unescape(text)
    text = text.replace(config.NO_BREAK_SPACE, " ")
    text = re.sub(config.MARKUP_PATTERN, " ", text)
    return re.sub(config.WHITESPACE_RUN_PATTERN, " ", text).strip()


def convert_markup_to_plain_text(dataframe, text_columns):
    """Leave free text as the plain words a person wrote."""
    result = dataframe.copy()
    for column in text_columns:
        result[column] = pd.Series([_plain_text(value) for value in result[column]],
                                   index=result.index, dtype="str")
    return result


# -------------------------------------------------------------------- ranges
def treat_out_of_range_as_missing(dataframe, range_limits):
    """Empty every reading outside its column's inclusive range."""
    result = dataframe.copy()
    for column, (lowest, highest) in range_limits.items():
        if column not in result.columns:
            continue
        values = result[column]
        outside = ((values < lowest) | (values > highest)).fillna(False).astype(bool)
        result[column] = values.mask(outside)
    return result


def remove_rows_missing_target(dataframe, target_column):
    """Remove every row whose answer is empty."""
    keep = ~dataframe[target_column].map(_is_empty).astype(bool)
    return dataframe[keep].reset_index(drop=True)
