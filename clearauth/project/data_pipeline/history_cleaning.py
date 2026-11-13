from config import config as c
from .request_cleaning import clean_request_records
from .common_cleaning import *


def clean_history_dataset(frame):
    return remove_rows_missing_target(
        treat_values_below_minimum_as_missing(
            clean_request_records(
                frame, c.HISTORY_VALUE_MAPPINGS, c.HISTORY_WHOLE_NUMBER_PATTERNS
            ),
            c.HISTORY_MINIMUM_VALUES,
        ),
        c.HISTORY_TARGET_COLUMN,
    )
