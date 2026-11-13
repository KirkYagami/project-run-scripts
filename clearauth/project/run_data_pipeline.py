from pathlib import Path
from config import config as c
from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset
from data_pipeline.history_cleaning import clean_history_dataset
from data_pipeline.stay_cleaning import clean_stay_dataset
from data_pipeline.sentence_cleaning import clean_sentence_dataset
from data_pipeline.quality_profiler import *

DATASET_JOBS = [
    (
        c.RAW_AUTHORISATION_HISTORY_TRAIN_FILE,
        c.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE,
        clean_history_dataset,
        c.HISTORY_TARGET_COLUMN,
        profile_history_details,
    ),
    (
        c.RAW_AUTHORISATION_HISTORY_EVAL_FILE,
        c.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE,
        clean_history_dataset,
        c.HISTORY_TARGET_COLUMN,
        profile_history_details,
    ),
    (
        c.RAW_SURGICAL_STAYS_TRAIN_FILE,
        c.CLEAN_SURGICAL_STAYS_TRAIN_FILE,
        clean_stay_dataset,
        c.STAY_TARGET_COLUMN,
        profile_stay_details,
    ),
    (
        c.RAW_SURGICAL_STAYS_EVAL_FILE,
        c.CLEAN_SURGICAL_STAYS_EVAL_FILE,
        clean_stay_dataset,
        c.STAY_TARGET_COLUMN,
        profile_stay_details,
    ),
    (
        c.RAW_CLINICAL_NOTE_SENTENCES_FILE,
        c.CLEAN_CLINICAL_NOTE_SENTENCES_FILE,
        clean_sentence_dataset,
        c.SENTENCE_TARGET_COLUMN,
        profile_sentence_details,
    ),
]


def main():
    completed = []
    profiles = {}
    for raw, dest, clean, target, detail in DATASET_JOBS:
        f = load_raw_dataset(raw)
        g = clean(f)
        name = Path(raw).stem
        profiles[name] = profile_dataset(f, g, target) | detail(f, g)
        completed.append((dest, g))
        print(
            f"{name:<{c.DATASET_NAME_WIDTH}} {len(f):>{c.ROW_COUNT_WIDTH}} received -> {len(g)} kept ({len(f)-len(g)} removed)"
        )
    for dest, g in completed:
        save_processed_dataset(g, dest)
    write_quality_report(profiles)
    print("quality report written to", c.DATA_QUALITY_REPORT_FILE)


if __name__ == "__main__":
    main()
