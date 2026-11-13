from sklearn.ensemble import RandomForestClassifier
from config import config as c
from data_pipeline.feature_builder import build_model_pipeline
from .model_evaluation import evaluate_classifier


def train_approval_model(
    train_features, train_target, held_out_features, held_out_target
):
    model = build_model_pipeline(
        RandomForestClassifier(
            n_estimators=c.APPROVAL_FOREST_TREES,
            min_samples_leaf=c.APPROVAL_FOREST_LEAF_MINIMUM,
            max_features=c.APPROVAL_FOREST_FEATURE_SHARE,
            random_state=c.RANDOM_SEED,
            n_jobs=-1,
        ),
        c.APPROVAL_NUMERIC_FEATURES,
        c.APPROVAL_CATEGORICAL_FEATURES,
    )
    model.fit(train_features, train_target)
    return model, evaluate_classifier(
        model, train_features, train_target, held_out_features, held_out_target
    )
