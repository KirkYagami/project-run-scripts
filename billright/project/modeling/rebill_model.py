"""The model that predicts whether a dispute ends in a corrected bill."""
from sklearn.ensemble import HistGradientBoostingClassifier

from config import config
from data_pipeline.feature_builder import build_model_pipeline
from modeling.model_evaluation import evaluate_classifier


def train_rebill_model(train_features, train_target, held_out_features, held_out_target):
    """Give every open dispute a probability of ending in a corrected bill."""
    estimator = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_leaf_nodes=31, l2_regularization=1.0,
        random_state=config.RANDOM_SEED)
    model = build_model_pipeline(estimator, config.REBILL_NUMERIC_FEATURES,
                                 config.REBILL_CATEGORICAL_FEATURES)
    model.fit(train_features, train_target)
    model.feature_names_fitted = list(train_features.columns)
    scores = evaluate_classifier(model, train_features, train_target, held_out_features,
                                 held_out_target)
    return model, scores
