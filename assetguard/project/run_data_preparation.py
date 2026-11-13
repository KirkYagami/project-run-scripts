"""Entry point 2: measure how dirty each raw dataset is, then clean all five."""

import os

from config import config
from data_pipeline.breakdown_cleaning import clean_breakdown_dataset
from data_pipeline.dataset_loader import load_raw_dataset
from data_pipeline.downtime_cleaning import clean_downtime_dataset
from data_pipeline.quality_profiler import build_quality_report, save_quality_report
from data_pipeline.technician_note_cleaning import clean_technician_note_dataset

if __name__ == "__main__":
    os.makedirs(config.PROCESSED_DIRECTORY, exist_ok=True)
    os.makedirs(config.OUTPUT_DIRECTORY, exist_ok=True)

    raw_datasets = [
        ("machine_breakdown_train", config.RAW_BREAKDOWN_TRAIN_FILE, config.BREAKDOWN_RANGE_LIMITS),
        ("machine_breakdown_eval", config.RAW_BREAKDOWN_EVAL_FILE, config.BREAKDOWN_RANGE_LIMITS),
        ("repair_downtime_train", config.RAW_DOWNTIME_TRAIN_FILE, config.DOWNTIME_RANGE_LIMITS),
        ("repair_downtime_eval", config.RAW_DOWNTIME_EVAL_FILE, config.DOWNTIME_RANGE_LIMITS),
        ("technician_notes", config.RAW_TECHNICIAN_NOTES_FILE, config.TECHNICIAN_NOTE_RANGE_LIMITS),
    ]
    report_records = []
    for dataset_name, raw_path, range_limits in raw_datasets:
        raw_frame = load_raw_dataset(raw_path, config.NULL_TOKEN_LIST)
        report_records.append(build_quality_report(raw_frame, dataset_name, range_limits))
    report_path = save_quality_report(report_records, config.DATA_QUALITY_REPORT_FILE)
    print("Data quality report written: " + report_path)

    cleaned_datasets = [
        ("Cleaned breakdown risk train",
         clean_breakdown_dataset(config.RAW_BREAKDOWN_TRAIN_FILE, config.CLEAN_BREAKDOWN_TRAIN_FILE)),
        ("Cleaned breakdown risk eval",
         clean_breakdown_dataset(config.RAW_BREAKDOWN_EVAL_FILE, config.CLEAN_BREAKDOWN_EVAL_FILE)),
        ("Cleaned downtime train",
         clean_downtime_dataset(config.RAW_DOWNTIME_TRAIN_FILE, config.CLEAN_DOWNTIME_TRAIN_FILE)),
        ("Cleaned downtime eval",
         clean_downtime_dataset(config.RAW_DOWNTIME_EVAL_FILE, config.CLEAN_DOWNTIME_EVAL_FILE)),
        ("Cleaned technician notes",
         clean_technician_note_dataset(config.RAW_TECHNICIAN_NOTES_FILE, config.CLEAN_TECHNICIAN_NOTES_FILE)),
    ]
    for label, cleaned_frame in cleaned_datasets:
        print(label + ": " + str(cleaned_frame.shape))

    breakdown_rate = cleaned_datasets[0][1][config.BREAKDOWN_TARGET_COLUMN].mean()
    print("Breakdown rate in training data: " + str(round(float(breakdown_rate), 4)))
