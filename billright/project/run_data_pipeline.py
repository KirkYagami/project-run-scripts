"""Cleans all five raw extracts and writes the evidence that each one needed cleaning."""
import os

from config import config
from data_pipeline.contact_note_cleaning import clean_contact_note_dataset
from data_pipeline.dataset_loader import load_raw_dataset
from data_pipeline.dispute_cleaning import clean_dispute_dataset
from data_pipeline.effort_cleaning import clean_effort_dataset
from data_pipeline.quality_profiler import (
    profile_dataset,
    profile_dispute_details,
    profile_effort_details,
    profile_note_details,
    write_quality_report,
)

DATASET_JOBS = [
    (config.RAW_DISPUTES_TRAIN_FILE, config.CLEAN_DISPUTES_TRAIN_FILE, clean_dispute_dataset,
     config.DISPUTE_TARGET_COLUMN, profile_dispute_details),
    (config.RAW_DISPUTES_EVAL_FILE, config.CLEAN_DISPUTES_EVAL_FILE, clean_dispute_dataset,
     config.DISPUTE_TARGET_COLUMN, profile_dispute_details),
    (config.RAW_EFFORT_TRAIN_FILE, config.CLEAN_EFFORT_TRAIN_FILE, clean_effort_dataset,
     config.EFFORT_TARGET_COLUMN, profile_effort_details),
    (config.RAW_EFFORT_EVAL_FILE, config.CLEAN_EFFORT_EVAL_FILE, clean_effort_dataset,
     config.EFFORT_TARGET_COLUMN, profile_effort_details),
    (config.RAW_CONTACT_NOTES_FILE, config.CLEAN_CONTACT_NOTES_FILE, clean_contact_note_dataset,
     config.NOTE_TARGET_COLUMN, profile_note_details),
]


def main():
    """Clean every extract, profile it, and write the quality report."""
    profiles = {}
    for raw_file, clean_file, cleaning_function, target_column, detail_profiler in DATASET_JOBS:
        raw_frame = load_raw_dataset(raw_file, config.NULL_TOKENS)
        clean_frame = cleaning_function(raw_file, clean_file)
        profile = profile_dataset(raw_frame, clean_frame, target_column)
        profile.update(detail_profiler(raw_frame, clean_frame))
        name = os.path.splitext(os.path.basename(raw_file))[0]
        profiles[name] = profile
        print(f"{name:<40}{profile['rows_received']:>8} received -> "
              f"{profile['rows_kept']:>10} kept   ({profile['rows_removed']} removed)")
    write_quality_report(profiles, config.DATA_QUALITY_REPORT_FILE)
    print(f"\nquality report written to {config.DATA_QUALITY_REPORT_FILE}")


if __name__ == "__main__":
    main()
