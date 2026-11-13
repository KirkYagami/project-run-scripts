"""The single place trained artefacts reach disk and are read back.

Each tabular model is saved together with its feature schema: the ordered list
of input columns it was trained on.
"""

import json

import joblib


def save_model_artifact(model_object, artifact_path):
    """Write a trained artefact (model or vectorizer) and return its path."""
    joblib.dump(model_object, artifact_path)
    return artifact_path


def load_model_artifact(artifact_path):
    """Restore an artefact written by save_model_artifact."""
    return joblib.load(artifact_path)


def save_feature_schema(feature_names, schema_path):
    """Write the ordered list of training columns as readable JSON."""
    with open(schema_path, "w", encoding="utf-8") as schema_file:
        json.dump(list(feature_names), schema_file, indent=2)
    return schema_path


def load_feature_schema(schema_path):
    """Read back the ordered list of training columns."""
    with open(schema_path, encoding="utf-8") as schema_file:
        return json.load(schema_file)
