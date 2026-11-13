"""Produces the downtime estimator: hours a machine will be out of service for a repair job.

Every candidate learns log(hours) and answers exp(prediction), so the estimate
is always above zero hours and the long tail of very long repairs does not
dominate the fit.
"""

import time

import numpy as np
from sklearn.base import clone
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
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
from modeling.model_evaluation import compare_candidate_scores, evaluate_regression_model
from modeling.model_registry import save_feature_schema, save_model_artifact

PRIMARY_METRIC = "r2"

TUNING_GRIDS = {
    Ridge: {"model__regressor__alpha": [0.1, 1.0, 10.0]},
    RandomForestRegressor: {"model__regressor__max_depth": [None, 16], "model__regressor__min_samples_leaf": [1, 5]},
    HistGradientBoostingRegressor: {"model__regressor__learning_rate": [0.05, 0.1], "model__regressor__max_leaf_nodes": [15, 31]},
}


def build_candidate_regressors(numeric_columns, categorical_columns, random_seed):
    """A simple linear baseline and two tree ensembles, each with its own preprocessing."""
    estimators = {
        "ridge_baseline": Ridge(),
        "random_forest": RandomForestRegressor(n_estimators=300, n_jobs=-1, random_state=random_seed),
        "hist_gradient_boosting": HistGradientBoostingRegressor(random_state=random_seed),
    }
    return {
        name: Pipeline([
            ("preprocess", build_preprocessing_pipeline(numeric_columns, categorical_columns)),
            ("model", TransformedTargetRegressor(regressor=estimator, func=np.log, inverse_func=np.exp)),
        ])
        for name, estimator in estimators.items()
    }


def train_candidate_regressors(candidate_models, feature_frame, target_series):
    """Fit every candidate on the same rows, logging each one's training time."""
    trained_models = {}
    for name, candidate in candidate_models.items():
        started = time.perf_counter()
        trained_models[name] = candidate.fit(feature_frame, target_series)
        print("    trained " + name + " in " + str(round(time.perf_counter() - started, 1)) + " seconds")
    return trained_models


def select_best_regressor(trained_models, evaluation_scores, primary_metric):
    """Return (name, model) with the highest primary_metric, even if every score is negative."""
    best_name = max(evaluation_scores, key=lambda name: evaluation_scores[name][primary_metric])
    return best_name, trained_models[best_name]


def tune_selected_regressor(selected_model, feature_frame, target_series):
    """Cross-validate a small grid for the winner's own family and return the refitted best."""
    family = type(selected_model.named_steps["model"].regressor)
    search = GridSearchCV(
        clone(selected_model), TUNING_GRIDS[family], scoring=PRIMARY_METRIC, cv=3, n_jobs=-1)
    search.fit(feature_frame, target_series)
    print("    best settings: " + str(search.best_params_))
    return search.best_estimator_


def train_downtime_model(train_path, model_output_path):
    """Compare, select, tune, then refit the winner on all of train_path and save it."""
    training_data = load_processed_dataset(train_path)
    model_ready = select_model_features(training_data, config.DOWNTIME_IDENTIFIER_COLUMNS)
    feature_frame, target_series = split_features_and_target(model_ready, config.DOWNTIME_TARGET_COLUMN)
    numeric_columns, categorical_columns = identify_column_types(feature_frame)

    learn_x, check_x, learn_y, check_y = train_test_split(
        feature_frame, target_series,
        test_size=config.VALIDATION_SPLIT_RATIO,
        random_state=config.RANDOM_SEED,
    )

    candidates = build_candidate_regressors(numeric_columns, categorical_columns, config.RANDOM_SEED)
    trained = train_candidate_regressors(candidates, learn_x, learn_y)
    scores = {name: evaluate_regression_model(model, check_x, check_y) for name, model in trained.items()}
    print(compare_candidate_scores(scores, PRIMARY_METRIC).round(4).to_string())

    best_name, best_model = select_best_regressor(trained, scores, PRIMARY_METRIC)
    print("    best candidate: " + best_name)
    tuned_model = tune_selected_regressor(best_model, learn_x, learn_y)

    final_model = clone(tuned_model).fit(feature_frame, target_series)
    save_model_artifact(final_model, model_output_path)
    save_feature_schema(list(feature_frame.columns), config.DOWNTIME_SCHEMA_FILE)
    return final_model
