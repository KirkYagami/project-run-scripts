"""Saves and loads the models, their feature schemas and their scores.

Nothing else in the project writes to output/models/.
"""
import json
import os

import joblib


def _make_folder(file_path):
    folder = os.path.dirname(file_path)
    if folder:
        os.makedirs(folder, exist_ok=True)


def save_model(model, file_path):
    """Put a fitted model on disk, whole, so loading it gives something that can score a row."""
    _make_folder(file_path)
    joblib.dump(model, file_path)


def save_feature_schema(feature_names, file_path):
    """Record exactly which inputs a model expects, in the order it was fitted on them."""
    _make_folder(file_path)
    with open(file_path, "w", encoding="utf-8") as schema_file:
        json.dump(list(feature_names), schema_file, indent=2)
        schema_file.write("\n")


def save_metrics(metrics, file_path):
    """Keep the evidence of how good each model was when it was saved."""
    _make_folder(file_path)
    with open(file_path, "w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, indent=2, sort_keys=True, default=_json_default)
        metrics_file.write("\n")


def load_model(file_path):
    """Bring a saved model back, ready to score."""
    return joblib.load(file_path)


def load_feature_schema(file_path):
    """Bring back the ordered list of inputs a model expects."""
    with open(file_path, encoding="utf-8") as schema_file:
        return json.load(schema_file)


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Cannot write {type(value).__name__} as JSON")
