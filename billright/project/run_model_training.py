"""Trains all three models in one run and says plainly whether each reached its minimum."""
import sklearn
from sklearn.model_selection import train_test_split

from config import config
from data_pipeline.dataset_loader import load_processed_dataset
from data_pipeline.feature_builder import build_feature_frame
from modeling.cause_model import train_cause_model
from modeling.effort_model import train_effort_model
from modeling.model_registry import save_feature_schema, save_metrics, save_model
from modeling.rebill_model import train_rebill_model


def _record(algorithm, train_rows, held_out_rows, scores, headline, minimum):
    return {
        "algorithm": algorithm,
        "training_rows": int(train_rows),
        "held_out_rows": int(held_out_rows),
        "scores": scores,
        "headline_score": headline,
        "minimum_required": minimum,
        "minimum_met": bool(scores[headline] >= minimum),
        "scikit_learn_version": sklearn.__version__,
    }


def _say(name, scores, held_out_key, train_key, minimum):
    held_out, train = scores[held_out_key], scores[train_key]
    print(f"  {name:<8} held-out {held_out:.4f}  training {train:.4f}  gap {train - held_out:.4f}"
          f"  (minimum {minimum})")


def main():
    """Train, save and score the three models."""
    metrics = {}

    print("rebill model: will the dispute end in a corrected bill?")
    train_frame = load_processed_dataset(config.CLEAN_DISPUTES_TRAIN_FILE)
    held_out_frame = load_processed_dataset(config.CLEAN_DISPUTES_EVAL_FILE)
    train_features = build_feature_frame(train_frame, config.REBILL_NUMERIC_FEATURES,
                                         config.REBILL_CATEGORICAL_FEATURES)
    held_out_features = build_feature_frame(held_out_frame, config.REBILL_NUMERIC_FEATURES,
                                            config.REBILL_CATEGORICAL_FEATURES)
    train_target = train_frame[config.DISPUTE_TARGET_COLUMN].map(config.DISPUTE_TARGET_ENCODING).astype(int)
    held_out_target = held_out_frame[config.DISPUTE_TARGET_COLUMN].map(config.DISPUTE_TARGET_ENCODING).astype(int)
    rebill_model, rebill_scores = train_rebill_model(train_features, train_target,
                                                     held_out_features, held_out_target)
    save_model(rebill_model, config.REBILL_MODEL_FILE)
    save_feature_schema(list(train_features.columns), config.REBILL_SCHEMA_FILE)
    metrics["rebill"] = _record("HistGradientBoostingClassifier", len(train_features),
                                len(held_out_features), rebill_scores, "held_out_roc_auc",
                                config.MINIMUM_REBILL_ROC_AUC)
    _say("rebill", rebill_scores, "held_out_roc_auc", "train_roc_auc", config.MINIMUM_REBILL_ROC_AUC)

    print("effort model: how many analyst hours will it take?")
    train_frame = load_processed_dataset(config.CLEAN_EFFORT_TRAIN_FILE)
    held_out_frame = load_processed_dataset(config.CLEAN_EFFORT_EVAL_FILE)
    train_features = build_feature_frame(train_frame, config.EFFORT_NUMERIC_FEATURES,
                                         config.EFFORT_CATEGORICAL_FEATURES)
    held_out_features = build_feature_frame(held_out_frame, config.EFFORT_NUMERIC_FEATURES,
                                            config.EFFORT_CATEGORICAL_FEATURES)
    effort_model, effort_scores = train_effort_model(
        train_features, train_frame[config.EFFORT_TARGET_COLUMN],
        held_out_features, held_out_frame[config.EFFORT_TARGET_COLUMN])
    save_model(effort_model, config.EFFORT_MODEL_FILE)
    save_feature_schema(list(train_features.columns), config.EFFORT_SCHEMA_FILE)
    metrics["effort"] = _record("HistGradientBoostingRegressor", len(train_features),
                                len(held_out_features), effort_scores, "held_out_r2",
                                config.MINIMUM_EFFORT_R2)
    _say("effort", effort_scores, "held_out_r2", "train_r2", config.MINIMUM_EFFORT_R2)

    print("cause model: which category does a note describe?")
    notes = load_processed_dataset(config.CLEAN_CONTACT_NOTES_FILE)
    train_notes, held_out_notes = train_test_split(
        notes, test_size=config.NOTE_HELD_OUT_SHARE, random_state=config.RANDOM_SEED,
        stratify=notes[config.NOTE_TARGET_COLUMN])
    cause_model, cause_scores = train_cause_model(
        train_notes[config.NOTE_TEXT_COLUMN], train_notes[config.NOTE_TARGET_COLUMN],
        held_out_notes[config.NOTE_TEXT_COLUMN], held_out_notes[config.NOTE_TARGET_COLUMN])
    save_model(cause_model, config.CAUSE_MODEL_FILE)
    metrics["cause"] = _record("TfidfVectorizer + LogisticRegression", len(train_notes),
                               len(held_out_notes), cause_scores, "held_out_macro_f1",
                               config.MINIMUM_CAUSE_MACRO_F1)
    _say("cause", cause_scores, "held_out_macro_f1", "train_macro_f1", config.MINIMUM_CAUSE_MACRO_F1)

    save_metrics(metrics, config.MODEL_METRICS_FILE)
    below = [name for name, record in metrics.items() if not record["minimum_met"]]
    print(f"\nmetrics written to {config.MODEL_METRICS_FILE}")
    if below:
        print("below the minimum: " + ", ".join(below))
    else:
        print("every model is above its minimum")


if __name__ == "__main__":
    main()
