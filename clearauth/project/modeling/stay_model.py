from sklearn.ensemble import RandomForestRegressor
from config import config as c
from data_pipeline.feature_builder import build_model_pipeline
from .model_evaluation import evaluate_regressor


def train_stay_model(train_features, train_target, held_out_features, held_out_target):
    model = build_model_pipeline(
        RandomForestRegressor(
            n_estimators=c.STAY_FOREST_TREES,
            min_samples_leaf=c.STAY_FOREST_LEAF_MINIMUM,
            random_state=c.RANDOM_SEED,
            n_jobs=-1,
        ),
        c.STAY_NUMERIC_FEATURES,
        c.STAY_CATEGORICAL_FEATURES,
    )
    model.fit(train_features, train_target)
    return model, evaluate_regressor(
        model, train_features, train_target, held_out_features, held_out_target
    )
