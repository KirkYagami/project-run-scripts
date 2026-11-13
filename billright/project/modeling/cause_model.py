"""The NLP model that reads a contact note and names the dispute category it describes."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from config import config
from modeling.model_evaluation import evaluate_text_classifier


def train_cause_model(train_text, train_target, held_out_text, held_out_target):
    """Turn a note written in a hurry into one of the categories the desk works to."""
    model = Pipeline([
        ("words", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("classifier", LogisticRegression(C=5.0, max_iter=2000, random_state=config.RANDOM_SEED)),
    ])
    model.fit(train_text, train_target)
    scores = evaluate_text_classifier(model, train_text, train_target, held_out_text,
                                      held_out_target)
    return model, scores
