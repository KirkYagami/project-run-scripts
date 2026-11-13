from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from config import config as c
from .model_evaluation import evaluate_text_classifier


def train_evidence_model(train_text, train_target, held_out_text, held_out_target):
    model = Pipeline(
        [
            ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            (
                c.MODEL_STEP_NAME,
                LogisticRegression(
                    max_iter=c.EVIDENCE_MODEL_MAXIMUM_ITERATIONS,
                    random_state=c.RANDOM_SEED,
                ),
            ),
        ]
    )
    model.fit(train_text, train_target)
    return model, evaluate_text_classifier(
        model, train_text, train_target, held_out_text, held_out_target
    )
