from config import config as c
from .common_cleaning import *


def clean_request_records(frame, value_mappings, whole_number_patterns):
    f = normalize_name_spacing(
        normalize_category_values(remove_duplicate_records(frame), value_mappings),
        c.REQUEST_NAME_COLUMNS,
    )
    for col, p, fmt in [
        (
            c.REQUEST_REFERENCE_COLUMN,
            c.REQUEST_REFERENCE_PATTERN,
            c.CANONICAL_REQUEST_REFERENCE_FORMAT,
        ),
        (
            c.MEMBER_NUMBER_COLUMN,
            c.MEMBER_NUMBER_PATTERN,
            c.CANONICAL_MEMBER_NUMBER_FORMAT,
        ),
        (
            c.DIAGNOSIS_CODE_COLUMN,
            c.DIAGNOSIS_CODE_PATTERN,
            c.CANONICAL_DIAGNOSIS_CODE_FORMAT,
        ),
    ]:
        f[col] = convert_identifiers(f[col], p, fmt)
    f = convert_decimal_numbers(
        convert_whole_numbers(f, whole_number_patterns),
        c.REQUEST_DECIMAL_NUMBER_PATTERNS,
    )
    f[c.TREATMENT_WEEKS_COLUMN] = convert_durations_to_whole_weeks(
        f[c.TREATMENT_WEEKS_COLUMN]
    )
    f[c.ASA_CLASS_COLUMN] = convert_asa_classes(f[c.ASA_CLASS_COLUMN])
    f[c.HEIGHT_COLUMN] = convert_measurements(
        f[c.HEIGHT_COLUMN], c.HEIGHT_NOTATIONS, c.CENTIMETRES_PER_HEIGHT_UNIT
    )
    f[c.WEIGHT_COLUMN] = convert_measurements(
        f[c.WEIGHT_COLUMN], c.WEIGHT_NOTATIONS, c.KILOGRAMS_PER_WEIGHT_UNIT
    )
    f[c.OTHER_CONDITIONS_COLUMN] = convert_condition_lists(f[c.OTHER_CONDITIONS_COLUMN])
    return keep_latest_submission_of_each_request(
        treat_values_above_maximum_as_missing(f, c.REQUEST_MAXIMUM_VALUES)
    )
