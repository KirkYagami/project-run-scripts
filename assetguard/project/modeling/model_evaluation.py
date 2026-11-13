"""Scores every candidate the same way and lays the results side by side.

All scores are plain floats so they can be written straight to JSON. Every
score here is "higher is better" except the error scores in hours, so callers
rank regressors by r2.
"""

import json

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


def evaluate_classification_model(trained_model, feature_frame, target_series):
    """Accuracy, precision, recall, F1 and ROC AUC for one breakdown classifier."""
    probabilities = trained_model.predict_proba(feature_frame)[:, 1]
    predicted = (probabilities >= 0.5).astype(int)
    if target_series.nunique() > 1:
        roc_auc = roc_auc_score(target_series, probabilities)
    else:
        # ROC AUC is undefined with only one outcome present; report chance level
        # rather than failing the whole scoring run.
        roc_auc = 0.5
    return {
        "accuracy": float(accuracy_score(target_series, predicted)),
        "precision": float(precision_score(target_series, predicted, zero_division=0)),
        "recall": float(recall_score(target_series, predicted, zero_division=0)),
        "f1": float(f1_score(target_series, predicted, zero_division=0)),
        "roc_auc": float(roc_auc),
    }


def evaluate_regression_model(trained_model, feature_frame, target_series):
    """MAE and RMSE in hours, and R squared, for one downtime estimator."""
    predicted = trained_model.predict(feature_frame)
    return {
        "mae_hours": float(mean_absolute_error(target_series, predicted)),
        "rmse_hours": float(np.sqrt(mean_squared_error(target_series, predicted))),
        "r2": float(r2_score(target_series, predicted)),
    }


def evaluate_text_classifier(trained_model, document_matrix, label_series):
    """Accuracy plus macro F1 (every problem type weighted equally) and weighted F1."""
    predicted = trained_model.predict(document_matrix)
    return {
        "accuracy": float(accuracy_score(label_series, predicted)),
        "macro_f1": float(f1_score(label_series, predicted, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(label_series, predicted, average="weighted", zero_division=0)),
    }


def compare_candidate_scores(evaluation_scores, primary_metric):
    """One row per candidate, strongest on primary_metric first."""
    rows = [{"candidate": name, **scores} for name, scores in evaluation_scores.items()]
    table = pd.DataFrame(rows)
    return table.sort_values(primary_metric, ascending=False).reset_index(drop=True)


def save_evaluation_report(report_records, output_path):
    """Write the nested score dictionary as readable JSON and return its path."""
    with open(output_path, "w", encoding="utf-8") as report_file:
        json.dump(report_records, report_file, indent=2)
    return output_path
