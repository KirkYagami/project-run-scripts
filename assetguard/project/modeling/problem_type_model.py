"""Produces the problem type classifier that reads free-text technician notes.

The text converter is saved alongside the classifier, because a new note must
be converted exactly the way the training notes were.
"""

import time

from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.svm import LinearSVC

from config import config
from data_pipeline.dataset_loader import load_processed_dataset
from modeling.model_evaluation import compare_candidate_scores, evaluate_text_classifier
from modeling.model_registry import save_model_artifact

PRIMARY_METRIC = "macro_f1"


def build_text_vectorizer():
    """TF-IDF over words and two-word phrases, ignoring rare terms and English filler words."""
    return TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=5,
        stop_words="english",
        sublinear_tf=True,
    )


def build_candidate_text_classifiers(random_seed):
    """A linear probabilistic model, a margin-based model and a naive Bayes model."""
    return {
        "logistic_regression": LogisticRegression(max_iter=3000, random_state=random_seed),
        "linear_svm": LinearSVC(max_iter=5000, random_state=random_seed),
        "complement_naive_bayes": ComplementNB(),
    }


def train_candidate_text_classifiers(candidate_models, document_matrix, label_series):
    """Fit every classifier on the same converted notes, logging each one's training time."""
    trained_models = {}
    for name, candidate in candidate_models.items():
        started = time.perf_counter()
        trained_models[name] = candidate.fit(document_matrix, label_series)
        print("    trained " + name + " in " + str(round(time.perf_counter() - started, 1)) + " seconds")
    return trained_models


def select_best_text_classifier(trained_models, evaluation_scores, primary_metric):
    """Return (name, model) with the highest primary_metric."""
    best_name = max(evaluation_scores, key=lambda name: evaluation_scores[name][primary_metric])
    return best_name, trained_models[best_name]


def train_problem_type_model(notes_path, model_output_path):
    """Compare classifiers on held-back notes, then refit the winner and converter on every note."""
    notes = load_processed_dataset(notes_path)
    note_text = notes[config.NOTE_TEXT_COLUMN]
    labels = notes[config.NOTE_TARGET_COLUMN]

    learn_text, check_text, learn_labels, check_labels = train_test_split(
        note_text, labels,
        test_size=config.VALIDATION_SPLIT_RATIO,
        random_state=config.RANDOM_SEED,
        stratify=labels,
    )

    # The comparison vocabulary comes from the learning notes only.
    comparison_vectorizer = build_text_vectorizer()
    learn_matrix = comparison_vectorizer.fit_transform(learn_text)
    check_matrix = comparison_vectorizer.transform(check_text)

    candidates = build_candidate_text_classifiers(config.RANDOM_SEED)
    trained = train_candidate_text_classifiers(candidates, learn_matrix, learn_labels)
    scores = {name: evaluate_text_classifier(model, check_matrix, check_labels) for name, model in trained.items()}
    print(compare_candidate_scores(scores, PRIMARY_METRIC).round(4).to_string())

    best_name, best_model = select_best_text_classifier(trained, scores, PRIMARY_METRIC)
    print("    best candidate: " + best_name)

    final_vectorizer = build_text_vectorizer()
    full_matrix = final_vectorizer.fit_transform(note_text)
    print("    vocabulary size: " + str(len(final_vectorizer.vocabulary_)))
    final_model = clone(best_model).fit(full_matrix, labels)

    save_model_artifact(final_model, model_output_path)
    save_model_artifact(final_vectorizer, config.TEXT_VECTORIZER_FILE)
    return final_model, final_vectorizer
