"""Turns a cleaned table into model inputs, and builds the preparation saved with each model."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def _as_number_column(series):
    """Floating point, with None, pd.NA and NaN all read as NaN."""
    values = series.astype("object")
    values = values.where(values.notna(), np.nan)
    return pd.to_numeric(values).astype("float64")


def _as_category_column(series):
    """Text, with every way of writing a gap read as NaN."""
    values = series.astype("object")
    return values.where(values.isna(), values.map(str)).where(values.notna(), np.nan)


def build_feature_frame(dataframe, numeric_columns, categorical_columns):
    """Give every model its inputs in one fixed shape, whatever the rows came from."""
    columns = {}
    for column in numeric_columns:
        columns[column] = _as_number_column(dataframe[column])
    for column in categorical_columns:
        columns[column] = _as_category_column(dataframe[column])
    return pd.DataFrame(columns, index=dataframe.index,
                        columns=list(numeric_columns) + list(categorical_columns))


def build_model_pipeline(estimator, numeric_columns, categorical_columns):
    """The one object that turns raw model inputs into a prediction, returned unfitted."""
    numeric_steps = Pipeline([
        ("fill_gaps", SimpleImputer(strategy="median", keep_empty_features=True)),
    ])
    categorical_steps = Pipeline([
        ("fill_gaps", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    preparation = ColumnTransformer([
        ("numbers", numeric_steps, list(numeric_columns)),
        ("categories", categorical_steps, list(categorical_columns)),
    ])
    return Pipeline([("prepare", preparation), ("model", estimator)])
