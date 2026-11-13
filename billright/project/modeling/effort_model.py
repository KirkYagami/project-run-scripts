"""The model that estimates how many analyst hours resolving a dispute will take."""
from sklearn.ensemble import HistGradientBoostingRegressor

from config import config
from data_pipeline.feature_builder import build_model_pipeline
from modeling.model_evaluation import evaluate_regressor


def train_effort_model(train_features, train_target, held_out_features, held_out_target):
    """Estimate the hours a dispute needs before the work starts."""
    estimator = HistGradientBoostingRegressor(
        max_iter=300, learning_rate=0.06, max_leaf_nodes=31, l2_regularization=1.0,
        random_state=config.RANDOM_SEED)
    model = build_model_pipeline(estimator, config.EFFORT_NUMERIC_FEATURES,
                                 config.EFFORT_CATEGORICAL_FEATURES)
    model.fit(train_features, train_target)
    model.feature_names_fitted = list(train_features.columns)
    scores = evaluate_regressor(model, train_features, train_target, held_out_features,
                                held_out_target)
    return model, scores
