import re, json
from pathlib import Path
import pandas as pd
from config import config as c
from .common_cleaning import *


def _missing(f):
    return {k: int(v) for k, v in f.isna().sum().items() if v}


def profile_dataset(raw_frame, clean_frame, target_column):
    first = raw_frame.drop_duplicates()
    return dict(
        rows_received=len(raw_frame),
        rows_kept=len(clean_frame),
        rows_removed=len(raw_frame) - len(clean_frame),
        duplicate_rows=len(raw_frame) - len(first),
        rows_missing_target=int(first[target_column].isna().sum()),
        columns=len(clean_frame.columns),
        missing_cells_as_received=_missing(raw_frame),
        missing_cells_after_cleaning=_missing(clean_frame),
    )


def _count(s, p):
    return int((s.notna() & ~s.astype(str).str.fullmatch(p)).sum())


def _base(raw, mappings, patterns):
    f = raw.drop_duplicates()
    return dict(
        numbers_not_written_as_plain_numbers={
            k: _count(f[k], c.PLAIN_NUMBER_PATTERN) for k in patterns
        },
        member_numbers_not_written_canonically=_count(
            f[c.MEMBER_NUMBER_COLUMN], c.CANONICAL_MEMBER_NUMBER_PATTERN
        ),
        category_values_not_written_canonically={
            k: int((f[k].notna() & ~f[k].isin(set(m.values()))).sum())
            for k, m in mappings.items()
        },
    )


def _shares(f, target):
    return {
        k: round(float(v), c.TARGET_SHARE_DECIMALS)
        for k, v in f[target].value_counts(normalize=True).items()
    }


def profile_history_details(raw_frame, clean_frame):
    f = raw_frame.drop_duplicates().copy()
    out = _base(
        f,
        c.HISTORY_VALUE_MAPPINGS,
        {
            **c.HISTORY_WHOLE_NUMBER_PATTERNS,
            **c.REQUEST_DECIMAL_NUMBER_PATTERNS,
            c.TREATMENT_WEEKS_COLUMN: "",
            c.ASA_CLASS_COLUMN: "",
            c.HEIGHT_COLUMN: "",
            c.WEIGHT_COLUMN: "",
        },
    )
    refs = convert_identifiers(
        f[c.REQUEST_REFERENCE_COLUMN],
        c.REQUEST_REFERENCE_PATTERN,
        c.CANONICAL_REQUEST_REFERENCE_FORMAT,
    )
    seq = pd.to_numeric(f[c.SUBMISSION_SEQUENCE_COLUMN])
    latest = seq.groupby(refs).transform("max")
    out["answered_earlier_submissions_removed"] = int(
        ((seq < latest) & f[c.HISTORY_TARGET_COLUMN].notna()).sum()
    )
    out["treatment_durations_written_in_days"] = int(
        f[c.TREATMENT_WEEKS_COLUMN].str.endswith(" days").sum()
    )
    for label, col, notations in [
        ("heights", c.HEIGHT_COLUMN, c.HEIGHT_NOTATIONS),
        ("weights", c.WEIGHT_COLUMN, c.WEIGHT_NOTATIONS),
    ]:
        out[label + "_by_notation_as_written"] = {
            name: int(f[col].str.fullmatch(p).sum()) for name, p in notations.items()
        }
    out["request_references_not_written_canonically"] = _count(
        f[c.REQUEST_REFERENCE_COLUMN], c.CANONICAL_REQUEST_REFERENCE_PATTERN
    )
    out["diagnosis_codes_not_written_canonically"] = _count(
        f[c.DIAGNOSIS_CODE_COLUMN], c.CANONICAL_DIAGNOSIS_CODE_PATTERN
    )
    canonical = convert_condition_lists(f[c.OTHER_CONDITIONS_COLUMN])
    out["condition_lists_not_written_canonically"] = int(
        (
            f[c.OTHER_CONDITIONS_COLUMN].notna()
            & (f[c.OTHER_CONDITIONS_COLUMN] != canonical)
        ).sum()
    )
    numeric = convert_decimal_numbers(
        convert_whole_numbers(f, c.HISTORY_WHOLE_NUMBER_PATTERNS),
        c.REQUEST_DECIMAL_NUMBER_PATTERNS,
    )
    out["values_above_maximum_as_received"] = {
        k: int((numeric[k] > v).sum()) for k, v in c.REQUEST_MAXIMUM_VALUES.items()
    }
    out["values_below_minimum_as_received"] = {
        k: int((numeric[k] < v).sum()) for k, v in c.HISTORY_MINIMUM_VALUES.items()
    }
    out["target_shares"] = _shares(clean_frame, c.HISTORY_TARGET_COLUMN)
    return out


def profile_stay_details(raw_frame, clean_frame):
    f = raw_frame.drop_duplicates()
    out = _base(
        f,
        c.STAY_VALUE_MAPPINGS,
        {
            **c.STAY_WHOLE_NUMBER_PATTERNS,
            **c.STAY_DECIMAL_NUMBER_PATTERNS,
            c.ASA_CLASS_COLUMN: "",
        },
    )
    f = convert_decimal_numbers(
        convert_whole_numbers(f, c.STAY_WHOLE_NUMBER_PATTERNS),
        c.STAY_DECIMAL_NUMBER_PATTERNS,
    )
    out["values_below_minimum_as_received"] = {
        k: int((f[k] < v).sum()) for k, v in c.STAY_MINIMUM_VALUES.items()
    }
    out["values_above_maximum_as_received"] = {
        k: int((f[k] > v).sum()) for k, v in c.STAY_MAXIMUM_VALUES.items()
    }
    out["rows_with_impossible_target"] = out["values_below_minimum_as_received"][
        c.STAY_TARGET_COLUMN
    ]
    out["median_length_of_stay_days"] = float(
        clean_frame[c.STAY_TARGET_COLUMN].median()
    )
    return out


def profile_sentence_details(raw_frame, clean_frame):
    f = raw_frame.drop_duplicates()
    t = f[c.SENTENCE_TEXT_COLUMN]
    plain = convert_markup_to_plain_text(t)
    return dict(
        sentences_with_markup=int(t.str.contains(c.MARKUP_PATTERN, regex=True).sum()),
        sentences_with_encoding_artifacts=int(
            t.str.contains(c.ENCODING_ARTIFACT_PATTERN, regex=True).sum()
        ),
        sentences_in_capitals=int(t.str.isupper().sum()),
        sentence_lengths_disagreeing_with_plain_text_as_received=int(
            (pd.to_numeric(f[c.SENTENCE_LENGTH_COLUMN]) != plain.str.len()).sum()
        ),
        rows_with_too_few_words=int(
            (
                f[c.SENTENCE_TARGET_COLUMN].notna()
                & plain.str.split().str.len().lt(c.MINIMUM_SENTENCE_WORDS)
            ).sum()
        ),
        shortest_sentence_words=int(
            clean_frame[c.SENTENCE_TEXT_COLUMN].str.split().str.len().min()
        ),
        request_references_not_written_canonically=_count(
            f[c.REQUEST_REFERENCE_COLUMN], c.CANONICAL_REQUEST_REFERENCE_PATTERN
        ),
        category_values_not_written_canonically={
            k: int((f[k].notna() & ~f[k].isin(set(m.values()))).sum())
            for k, m in c.SENTENCE_VALUE_MAPPINGS.items()
        },
        target_shares=_shares(clean_frame, c.SENTENCE_TARGET_COLUMN),
    )


def write_quality_report(profiles):
    for name, p in profiles.items():
        reasons = sum(
            p.get(k, 0)
            for k in [
                "duplicate_rows",
                "rows_missing_target",
                "answered_earlier_submissions_removed",
                "rows_with_impossible_target",
                "rows_with_too_few_words",
            ]
        )
        if reasons != p["rows_removed"]:
            raise ValueError(f"{name}: removal counts disagree")
    Path(c.DATA_QUALITY_REPORT_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(c.DATA_QUALITY_REPORT_FILE).write_text(
        json.dumps(profiles, indent=c.JSON_INDENT, sort_keys=True)
    )
