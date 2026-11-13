import sklearn
from sklearn.model_selection import train_test_split
from config import config as c
from knowledge.policy_reading import read_medical_policy
from data_pipeline.dataset_loader import load_processed_dataset
from data_pipeline.feature_builder import add_criteria_counts, build_feature_frame
from modeling.approval_model import train_approval_model
from modeling.stay_model import train_stay_model
from modeling.evidence_model import train_evidence_model
from modeling.model_registry import *


def main():
    policies = {k: read_medical_policy(k) for k in c.SERVICE_POLICY_DOCUMENTS}
    results = {}
    schemas = {}
    for name, trainfile, evalfile, nums, cats, target, fn in [
        (
            "approval",
            c.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE,
            c.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE,
            c.APPROVAL_NUMERIC_FEATURES,
            c.APPROVAL_CATEGORICAL_FEATURES,
            c.HISTORY_TARGET_COLUMN,
            train_approval_model,
        ),
        (
            "stay",
            c.CLEAN_SURGICAL_STAYS_TRAIN_FILE,
            c.CLEAN_SURGICAL_STAYS_EVAL_FILE,
            c.STAY_NUMERIC_FEATURES,
            c.STAY_CATEGORICAL_FEATURES,
            c.STAY_TARGET_COLUMN,
            train_stay_model,
        ),
    ]:
        train = load_processed_dataset(trainfile)
        held = load_processed_dataset(evalfile)
        if name == "approval":
            train = add_criteria_counts(train, policies)
            held = add_criteria_counts(held, policies)
        X = build_feature_frame(train, nums, cats)
        E = build_feature_frame(held, nums, cats)
        y = train[target]
        z = held[target]
        if name == "approval":
            unknown = set(y) | set(z)
            unknown -= set(c.APPROVAL_TARGET_ENCODING)
            if unknown:
                raise ValueError(f"{target}: unknown {unknown}")
            y = y.map(c.APPROVAL_TARGET_ENCODING)
            z = z.map(c.APPROVAL_TARGET_ENCODING)
        model, scores = fn(X, y, E, z)
        results[name] = (model, scores, len(X), len(E))
        schemas[name] = list(X.columns)
        print(name, scores, flush=True)
    f = load_processed_dataset(c.CLEAN_CLINICAL_NOTE_SENTENCES_FILE)
    a, b, y, z = train_test_split(
        f[c.SENTENCE_TEXT_COLUMN],
        f[c.SENTENCE_TARGET_COLUMN],
        test_size=c.SENTENCE_HELD_OUT_SHARE,
        stratify=f[c.SENTENCE_TARGET_COLUMN],
        random_state=c.RANDOM_SEED,
    )
    model, scores = train_evidence_model(a, y, b, z)
    results["evidence"] = (model, scores, len(a), len(b))
    print("evidence", scores, flush=True)
    limits = {
        "approval": ("held_out_roc_auc", c.MINIMUM_APPROVAL_ROC_AUC),
        "stay": ("held_out_r2", c.MINIMUM_STAY_R2),
        "evidence": ("held_out_macro_f1", c.MINIMUM_EVIDENCE_MACRO_F1),
    }
    short = [
        f"{n}: {results[n][1][key]} < {limit}"
        for n, (key, limit) in limits.items()
        if results[n][1][key] < limit
    ]
    if short:
        raise ValueError("; ".join(short))
    metrics = {}
    for name, (model, scores, nt, ne) in results.items():
        save_model(model, getattr(c, name.upper() + "_MODEL_FILE"))
        if name in schemas:
            save_feature_schema(
                schemas[name], getattr(c, name.upper() + "_SCHEMA_FILE")
            )
        metrics[name] = dict(
            algorithm=type(model[-1]).__name__,
            training_rows=nt,
            held_out_rows=ne,
            scores=scores,
            minimum_required=limits[name][1],
            scikit_learn_version=sklearn.__version__,
        )
    save_metrics(metrics)
    print("every model reaches the minimum; metrics:", c.MODEL_METRICS_FILE)


if __name__ == "__main__":
    main()
