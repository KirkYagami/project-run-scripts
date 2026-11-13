"""Entry point 3: train the two tabular models and the note model, score them, save the winners."""

import os

from config import config
from data_pipeline.dataset_loader import load_processed_dataset
from data_pipeline.feature_builder import select_model_features, split_features_and_target
from modeling.breakdown_model import train_breakdown_model
from modeling.downtime_model import train_downtime_model
from modeling.model_evaluation import (
    evaluate_classification_model,
    evaluate_regression_model,
    evaluate_text_classifier,
    save_evaluation_report,
)
from modeling.problem_type_model import train_problem_type_model


def rounded(scores):
    return {name: round(value, 4) for name, value in scores.items()}


if __name__ == "__main__":
    os.makedirs(config.MODEL_DIRECTORY, exist_ok=True)
    os.makedirs(config.OUTPUT_DIRECTORY, exist_ok=True)

    print("ML model 1 of 2 - breakdown risk classifier (tabular)")
    breakdown_model = train_breakdown_model(config.CLEAN_BREAKDOWN_TRAIN_FILE, config.BREAKDOWN_MODEL_FILE)
    holdout = select_model_features(
        load_processed_dataset(config.CLEAN_BREAKDOWN_EVAL_FILE), config.BREAKDOWN_IDENTIFIER_COLUMNS)
    holdout_x, holdout_y = split_features_and_target(holdout, config.BREAKDOWN_TARGET_COLUMN)
    breakdown_scores = evaluate_classification_model(breakdown_model, holdout_x, holdout_y)
    print("  hold-out scores: " + str(rounded(breakdown_scores)))
    print("  saved to: " + config.BREAKDOWN_MODEL_FILE)

    print("ML model 2 of 2 - downtime estimator (tabular)")
    downtime_model = train_downtime_model(config.CLEAN_DOWNTIME_TRAIN_FILE, config.DOWNTIME_MODEL_FILE)
    holdout = select_model_features(
        load_processed_dataset(config.CLEAN_DOWNTIME_EVAL_FILE), config.DOWNTIME_IDENTIFIER_COLUMNS)
    holdout_x, holdout_y = split_features_and_target(holdout, config.DOWNTIME_TARGET_COLUMN)
    downtime_scores = evaluate_regression_model(downtime_model, holdout_x, holdout_y)
    print("  hold-out scores: " + str(rounded(downtime_scores)))
    print("  saved to: " + config.DOWNTIME_MODEL_FILE)

    print("NLP model - problem type classifier (technician note text)")
    problem_type_model, text_vectorizer = train_problem_type_model(
        config.CLEAN_TECHNICIAN_NOTES_FILE, config.PROBLEM_TYPE_MODEL_FILE)
    # There is no separate note hold-out file, so these are training-set scores.
    notes = load_processed_dataset(config.CLEAN_TECHNICIAN_NOTES_FILE)
    problem_type_scores = evaluate_text_classifier(
        problem_type_model,
        text_vectorizer.transform(notes[config.NOTE_TEXT_COLUMN]),
        notes[config.NOTE_TARGET_COLUMN],
    )
    print("  training-set scores: " + str(rounded(problem_type_scores)))
    print("  saved to: " + config.PROBLEM_TYPE_MODEL_FILE)
    print("  vectorizer saved to: " + config.TEXT_VECTORIZER_FILE)

    metrics_path = save_evaluation_report(
        {
            "breakdown_model": breakdown_scores,
            "downtime_model": downtime_scores,
            "problem_type_model": problem_type_scores,
        },
        config.MODEL_METRICS_FILE,
    )
    print("Metrics written: " + metrics_path)
