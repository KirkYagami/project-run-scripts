"""Produces the breakdown risk model: P(breakdown within 30 days) for one machine week."""

import time

from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline

from config import config
from data_pipeline.dataset_loader import load_processed_dataset
from data_pipeline.feature_builder import (
    build_preprocessing_pipeline,
    identify_column_types,
    select_model_features,
    split_features_and_target,
)
from modeling.model_evaluation import compare_candidate_scores, evaluate_classification_model
from modeling.model_registry import save_feature_schema, save_model_artifact

PRIMARY_METRIC = "roc_auc"

# Small grids per family, prefixed for the "model" step of the pipeline.
TUNING_GRIDS = {
    LogisticRegression: {"model__C": [0.1, 1.0, 10.0]},
    RandomForestClassifier: {"model__max_depth": [None, 14], "model__min_samples_leaf": [1, 5]},
    HistGradientBoostingClassifier: {"model__learning_rate": [0.05, 0.1], "model__max_leaf_nodes": [15, 31]},
}


def build_candidate_classifiers(numeric_columns, categorical_columns, random_seed):
    """Three families, each wrapped with its own preprocessing and weighted for the minority class."""
    estimators = {
        "logistic_regression": LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=random_seed),
        "random_forest": RandomForestClassifier(
            n_estimators=300, class_weight="balanced", n_jobs=-1, random_state=random_seed),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            class_weight="balanced", random_state=random_seed),
    }
    return {
        name: Pipeline([
            ("preprocess", build_preprocessing_pipeline(numeric_columns, categorical_columns)),
            ("model", estimator),
        ])
        for name, estimator in estimators.items()
    }


def train_candidate_classifiers(candidate_models, feature_frame, target_series):
    """Fit every candidate on the same rows, logging each one's training time."""
    trained_models = {}
    for name, candidate in candidate_models.items():
        started = time.perf_counter()
        trained_models[name] = candidate.fit(feature_frame, target_series)
        print("    trained " + name + " in " + str(round(time.perf_counter() - started, 1)) + " seconds")
    return trained_models


def select_best_classifier(trained_models, evaluation_scores, primary_metric):
    """Return (name, model) of the candidate with the highest primary_metric."""
    best_name = max(evaluation_scores, key=lambda name: evaluation_scores[name][primary_metric])
    return best_name, trained_models[best_name]


def tune_selected_classifier(selected_model, feature_frame, target_series):
    """Cross-validate a small grid for the winner's own family and return the refitted best."""
    family = type(selected_model.named_steps["model"])
    search = GridSearchCV(
        clone(selected_model), TUNING_GRIDS[family], scoring=PRIMARY_METRIC, cv=3, n_jobs=-1)
    search.fit(feature_frame, target_series)
    print("    best settings: " + str(search.best_params_))
    return search.best_estimator_


def train_breakdown_model(train_path, model_output_path):
    """Compare, select, tune, then refit the winner on all of train_path and save it."""
    training_data = load_processed_dataset(train_path)
    model_ready = select_model_features(training_data, config.BREAKDOWN_IDENTIFIER_COLUMNS)
    feature_frame, target_series = split_features_and_target(model_ready, config.BREAKDOWN_TARGET_COLUMN)
    numeric_columns, categorical_columns = identify_column_types(feature_frame)

    learn_x, check_x, learn_y, check_y = train_test_split(
        feature_frame, target_series,
        test_size=config.VALIDATION_SPLIT_RATIO,
        random_state=config.RANDOM_SEED,
        stratify=target_series,
    )

    candidates = build_candidate_classifiers(numeric_columns, categorical_columns, config.RANDOM_SEED)
    trained = train_candidate_classifiers(candidates, learn_x, learn_y)
    scores = {name: evaluate_classification_model(model, check_x, check_y) for name, model in trained.items()}
    print(compare_candidate_scores(scores, PRIMARY_METRIC).round(4).to_string())

    best_name, best_model = select_best_classifier(trained, scores, PRIMARY_METRIC)
    print("    best candidate: " + best_name)
    tuned_model = tune_selected_classifier(best_model, learn_x, learn_y)

    final_model = clone(tuned_model).fit(feature_frame, target_series)
    save_model_artifact(final_model, model_output_path)
    save_feature_schema(list(feature_frame.columns), config.BREAKDOWN_SCHEMA_FILE)
    return final_model
