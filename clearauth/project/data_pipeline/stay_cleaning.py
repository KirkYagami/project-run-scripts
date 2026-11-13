from config import config as c
from .common_cleaning import *


def clean_stay_dataset(frame):
    f = remove_duplicate_records(frame)
    refuse_missing_values(f, [c.ADMISSION_REFERENCE_COLUMN])
    refuse_repeated_references(f, [c.ADMISSION_REFERENCE_COLUMN])
    f = normalize_name_spacing(
        normalize_category_values(f, c.STAY_VALUE_MAPPINGS), c.STAY_NAME_COLUMNS
    )
    f[c.MEMBER_NUMBER_COLUMN] = convert_identifiers(
        f[c.MEMBER_NUMBER_COLUMN],
        c.MEMBER_NUMBER_PATTERN,
        c.CANONICAL_MEMBER_NUMBER_FORMAT,
    )
    f = convert_decimal_numbers(
        convert_whole_numbers(f, c.STAY_WHOLE_NUMBER_PATTERNS),
        c.STAY_DECIMAL_NUMBER_PATTERNS,
    )
    f[c.ASA_CLASS_COLUMN] = convert_asa_classes(f[c.ASA_CLASS_COLUMN])
    return remove_rows_missing_target(
        treat_values_above_maximum_as_missing(
            treat_values_below_minimum_as_missing(f, c.STAY_MINIMUM_VALUES),
            c.STAY_MAXIMUM_VALUES,
        ),
        c.STAY_TARGET_COLUMN,
    )
