from pathlib import Path
import json, joblib
from config import config as c


def save_model(model, file_path):
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, file_path, compress=c.MODEL_FILE_COMPRESSION)


def save_feature_schema(feature_names, file_path):
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    Path(file_path).write_text(json.dumps(list(feature_names), indent=c.JSON_INDENT))


def load_model(file_path):
    return joblib.load(file_path)


def load_feature_schema(file_path):
    return json.loads(Path(file_path).read_text())


def save_metrics(metrics):
    Path(c.MODEL_METRICS_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(c.MODEL_METRICS_FILE).write_text(
        json.dumps(metrics, indent=c.JSON_INDENT, sort_keys=True)
    )
