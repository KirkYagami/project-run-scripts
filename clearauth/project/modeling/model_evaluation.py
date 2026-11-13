import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    r2_score,
    mean_absolute_error,
)
from config import config as c


def _rounded(d):
    return {
        k: (_rounded(v) if isinstance(v, dict) else round(float(v), c.METRIC_DECIMALS))
        for k, v in d.items()
    }


def evaluate_classifier(
    model, train_features, train_target, held_out_features, held_out_target
):
    t = model.predict_proba(train_features)[:, 1]
    p = model.predict_proba(held_out_features)[:, 1]
    pred = model.predict(held_out_features)
    a = roc_auc_score(train_target, t)
    b = roc_auc_score(held_out_target, p)
    return _rounded(
        dict(
            train_roc_auc=a,
            held_out_roc_auc=b,
            accuracy=accuracy_score(held_out_target, pred),
            precision=precision_score(held_out_target, pred),
            recall=recall_score(held_out_target, pred),
            f1=f1_score(held_out_target, pred),
            mean_predicted_probability=p.mean(),
            positive_share=np.mean(held_out_target),
            generalisation_gap=a - b,
        )
    )


def evaluate_regressor(
    model, train_features, train_target, held_out_features, held_out_target
):
    p = model.predict(held_out_features)
    a = r2_score(train_target, model.predict(train_features))
    b = r2_score(held_out_target, p)
    return _rounded(
        dict(
            train_r2=a,
            held_out_r2=b,
            mean_absolute_error=mean_absolute_error(held_out_target, p),
            average_estimate_mean_absolute_error=mean_absolute_error(
                held_out_target, np.full(len(p), np.mean(train_target))
            ),
            lowest_prediction=p.min(),
            highest_prediction=p.max(),
            generalisation_gap=a - b,
        )
    )


def evaluate_text_classifier(
    model, train_text, train_target, held_out_text, held_out_target
):
    p = model.predict(held_out_text)
    a = f1_score(train_target, model.predict(train_text), average="macro")
    b = f1_score(held_out_target, p, average="macro")
    return _rounded(
        dict(
            train_macro_f1=a,
            held_out_macro_f1=b,
            accuracy=accuracy_score(held_out_target, p),
            weighted_f1=f1_score(held_out_target, p, average="weighted"),
            generalisation_gap=a - b,
            per_class_f1=dict(
                zip(
                    model.classes_,
                    f1_score(held_out_target, p, labels=model.classes_, average=None),
                )
            ),
        )
    )
