"""Scores a fitted model on rows it did not learn from, and on the rows it did.

No function here fits anything.
"""
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

_PLACES = 4


def _round(value):
    return round(float(value), _PLACES)


def evaluate_classifier(model, train_features, train_target, held_out_features, held_out_target):
    """Say how well the rebill model ranks disputes it has never seen."""
    held_out_probability = model.predict_proba(held_out_features)[:, 1]
    train_probability = model.predict_proba(train_features)[:, 1]
    held_out_prediction = (held_out_probability >= 0.5).astype(int)
    held_out_roc_auc = roc_auc_score(held_out_target, held_out_probability)
    train_roc_auc = roc_auc_score(train_target, train_probability)
    return {
        "held_out_roc_auc": _round(held_out_roc_auc),
        "train_roc_auc": _round(train_roc_auc),
        "generalisation_gap": _round(train_roc_auc - held_out_roc_auc),
        "accuracy": _round(accuracy_score(held_out_target, held_out_prediction)),
        "precision": _round(precision_score(held_out_target, held_out_prediction, zero_division=0)),
        "recall": _round(recall_score(held_out_target, held_out_prediction, zero_division=0)),
        "f1": _round(f1_score(held_out_target, held_out_prediction, zero_division=0)),
        "mean_predicted_probability": _round(np.mean(held_out_probability)),
        "positive_share": _round(np.mean(np.asarray(held_out_target))),
    }


def evaluate_regressor(model, train_features, train_target, held_out_features, held_out_target):
    """Say how well the effort model estimates hours it has never seen."""
    held_out_prediction = model.predict(held_out_features)
    train_prediction = model.predict(train_features)
    held_out_r2 = r2_score(held_out_target, held_out_prediction)
    train_r2 = r2_score(train_target, train_prediction)
    average_guess = np.full(len(held_out_target), float(np.mean(np.asarray(train_target))))
    return {
        "held_out_r2": _round(held_out_r2),
        "train_r2": _round(train_r2),
        "generalisation_gap": _round(train_r2 - held_out_r2),
        "mean_absolute_error": _round(mean_absolute_error(held_out_target, held_out_prediction)),
        "average_estimate_mean_absolute_error": _round(
            mean_absolute_error(held_out_target, average_guess)),
        "lowest_prediction": _round(np.min(held_out_prediction)),
    }


def evaluate_text_classifier(model, train_text, train_target, held_out_text, held_out_target):
    """Say how well the cause model names every category, the rare ones included."""
    held_out_prediction = model.predict(held_out_text)
    train_prediction = model.predict(train_text)
    held_out_macro_f1 = f1_score(held_out_target, held_out_prediction, average="macro")
    train_macro_f1 = f1_score(train_target, train_prediction, average="macro")
    categories = sorted(set(held_out_target))
    per_class = f1_score(held_out_target, held_out_prediction, labels=categories, average=None)
    return {
        "held_out_macro_f1": _round(held_out_macro_f1),
        "train_macro_f1": _round(train_macro_f1),
        "generalisation_gap": _round(train_macro_f1 - held_out_macro_f1),
        "accuracy": _round(accuracy_score(held_out_target, held_out_prediction)),
        "weighted_f1": _round(f1_score(held_out_target, held_out_prediction, average="weighted")),
        "per_class_f1": {category: _round(score) for category, score in zip(categories, per_class)},
    }
