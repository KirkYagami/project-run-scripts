import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from config import config as c


def add_criteria_counts(dataframe, policies):
    from tools.screening_tools import screen_request

    out = dataframe.copy()
    rows = []
    for record in dataframe.to_dict("records"):
        code = record[c.SERVICE_CODE_COLUMN]
        if pd.isna(code):
            raise ValueError(c.NO_SERVICE_CODE_MESSAGE.format(**record))
        if code not in policies:
            raise ValueError(
                f"{record[c.REQUEST_REFERENCE_COLUMN]}: no policy for {code}"
            )
        s = screen_request(record, policies[code])
        rows.append([s[k] for k in c.CRITERIA_COUNT_COLUMNS])
    out[c.CRITERIA_COUNT_COLUMNS] = rows
    return out


def build_feature_frame(dataframe, numeric_columns, categorical_columns):
    f = dataframe[numeric_columns + categorical_columns].copy()
    for col in numeric_columns:
        f[col] = pd.to_numeric(f[col]).astype(float)
    for col in categorical_columns:
        f[col] = f[col].astype(object).where(f[col].notna(), np.nan)
    return f


def build_model_pipeline(estimator, numeric_columns, categorical_columns):
    pre = ColumnTransformer(
        [
            (
                "numbers",
                SimpleImputer(strategy=c.NUMBER_FILL_STRATEGY),
                numeric_columns,
            ),
            (
                "categories",
                Pipeline(
                    [
                        ("fill", SimpleImputer(strategy=c.CATEGORY_FILL_STRATEGY)),
                        ("encode", OneHotEncoder(handle_unknown="error")),
                    ]
                ),
                categorical_columns,
            ),
        ]
    )
    return Pipeline([("preparation", pre), (c.MODEL_STEP_NAME, estimator)])
