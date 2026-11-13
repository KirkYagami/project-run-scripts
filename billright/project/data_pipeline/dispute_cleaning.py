"""The whole cleaning run for one billing disputes extract."""
import pandas as pd

from config import config
from data_pipeline.common_cleaning import (
    convert_energy_to_kwh,
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


def build_month_first_rows(dataframe):
    """One nullable boolean per row: is this row's billing system month first?"""
    return dataframe[config.BILLING_SYSTEM_COLUMN].map(
        config.MONTH_FIRST_BY_BILLING_SYSTEM).astype("boolean")


def _swap_reversed_bills(dataframe):
    """Swap the two dates of a bill whose last day precedes its first."""
    result = dataframe.copy()
    start = result[config.BILL_START_COLUMN]
    end = result[config.BILL_END_COLUMN]
    reversed_rows = (end < start).fillna(False).astype(bool)
    result[config.BILL_START_COLUMN] = start.mask(reversed_rows, end)
    result[config.BILL_END_COLUMN] = end.mask(reversed_rows, start)
    return result


def _recount_days_billed(dataframe):
    """days_billed is the first date to the last, both included, where both are known."""
    result = dataframe.copy()
    counted = result[config.BILL_END_COLUMN] - result[config.BILL_START_COLUMN] + 1
    result[config.DAYS_BILLED_COLUMN] = counted.where(counted.notna(),
                                                      result[config.DAYS_BILLED_COLUMN])
    return result.astype({config.DAYS_BILLED_COLUMN: "Int64"})


def _register_usage(opening, closing, digits):
    """Usage of one register, allowing for a register that passed its last digit."""
    if pd.isna(opening) or pd.isna(closing) or pd.isna(digits):
        return pd.NA
    usage = int(closing) - int(opening)
    if closing < opening:
        usage += config.REGISTER_NUMBER_BASE ** int(digits)
    return usage


def _remeasure_negative_usage(dataframe):
    """Measure a negative usage again from the bill's own verified-by-register reads."""
    result = dataframe.copy()
    units = result[config.BILLED_UNITS_COLUMN]
    negative_rows = (units < 0).fillna(False).astype(bool)
    remeasured = {}
    for position in result.index[negative_rows]:
        row = result.loc[position]
        digits = row[config.REGISTER_DIGITS_COLUMN]
        day_usage = _register_usage(row[config.OPENING_READ_COLUMN],
                                    row[config.CLOSING_READ_COLUMN], digits)
        total = day_usage
        if row[config.METER_TYPE_COLUMN] == config.TWO_RATE_METER_TYPE:
            night_usage = _register_usage(row[config.NIGHT_OPENING_READ_COLUMN],
                                          row[config.NIGHT_CLOSING_READ_COLUMN], digits)
            total = pd.NA if pd.isna(day_usage) or pd.isna(night_usage) else day_usage + night_usage
        remeasured[position] = total
    if remeasured:
        units = units.astype("object")
        for position, usage in remeasured.items():
            units.loc[position] = usage
        result[config.BILLED_UNITS_COLUMN] = pd.Series(units, index=result.index).astype("Int64")
    return result


def clean_dispute_dataset(input_file_path, output_file_path):
    """Produce a disputes table the rebill model can be fitted on and scored against."""
    table = load_raw_dataset(input_file_path, config.NULL_TOKENS)
    table = remove_duplicate_records(table)
    table = remove_rows_missing_target(table, config.DISPUTE_TARGET_COLUMN)
    table = normalize_category_values(table, config.DISPUTE_VALUE_MAPPINGS)
    table = parse_price_year_dates(table, config.DISPUTE_DATE_COLUMNS,
                                   build_month_first_rows(table))
    table = convert_money_amounts(table, config.DISPUTE_MONEY_COLUMNS)
    table = convert_energy_to_kwh(table, config.DISPUTE_ENERGY_COLUMNS)
    table = convert_whole_numbers(table, config.DISPUTE_WHOLE_NUMBER_COLUMNS)
    table = treat_out_of_range_as_missing(table, config.DISPUTE_RANGE_LIMITS)
    table = _swap_reversed_bills(table)
    table = _recount_days_billed(table)
    table = _remeasure_negative_usage(table)
    table = format_price_year_dates(table, config.DISPUTE_DATE_COLUMNS)
    save_processed_dataset(table, output_file_path)
    return table
