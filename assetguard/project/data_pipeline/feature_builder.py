"""Turns a cleaned table into model inputs.

Used identically at training time and at scoring time, which is what keeps a
live prediction consistent with what the model learned.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def select_model_features(dataframe, excluded_columns):
    """Drop identifier columns, keeping every other column in its original order."""
    present = [name for name in excluded_columns if name in dataframe.columns]
    return dataframe.drop(columns=present)


def split_features_and_target(dataframe, target_column):
    """Return (inputs, answer), aligned row for row."""
    return dataframe.drop(columns=[target_column]), dataframe[target_column]


def identify_column_types(feature_frame):
    """Return (numeric column names, categorical column names) by actual dtype."""
    numeric_columns = []
    categorical_columns = []
    for column_name in feature_frame.columns:
        if pd.api.types.is_numeric_dtype(feature_frame[column_name]):
            numeric_columns.append(column_name)
        else:
            categorical_columns.append(column_name)
    return numeric_columns, categorical_columns


def build_preprocessing_pipeline(numeric_columns, categorical_columns):
    """One unfitted step: impute and scale numbers, impute and one-hot encode categories."""
    numeric_branch = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_branch = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numeric", numeric_branch, list(numeric_columns)),
        ("categorical", categorical_branch, list(categorical_columns)),
    ])
