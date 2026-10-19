"""
Preprocessing definitions shared across EDA, training and serving.

Having a single source of truth for the feature schema and the sklearn
preprocessing pipeline is what guarantees train/serve consistency: the API
loads the *same* fitted ColumnTransformer that training produced, so a request
is transformed identically to a training row.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "target"

# Clinically continuous / ordinal-numeric features -> impute (median) + scale.
NUMERIC_FEATURES: List[str] = [
    "age",       # years
    "trestbps",  # resting blood pressure (mm Hg)
    "chol",      # serum cholesterol (mg/dl)
    "thalach",   # max heart rate achieved
    "oldpeak",   # ST depression induced by exercise
    "ca",        #  number of major vessels (0-3), NaN for 4 rows
]

# Genuinely categorical features -> impute (most frequent) + one-hot encode.
CATEGORICAL_FEATURES: List[str] = [
    "sex",      # 0 = female, 1 = male
    "cp",       # chest pain type (1-4; 4 = asymptomatic)
    "fbs",      # fasting blood sugar > 120 mg/dl (0/1)
    "restecg",  # resting ECG (0-2)
    "exang",    # exercise-induced angina (0/1)
    "slope",    # slope of peak exercise ST segment (1-3)
    "thal",     # thal: 3 = normal, 6 = fixed defect, 7 = reversible defect
]

ALL_FEATURES: List[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass
class FeatureSchema:
    """Lightweight schema object persisted alongside the model."""

    target: str = TARGET
    numeric: List[str] = field(default_factory=lambda: list(NUMERIC_FEATURES))
    categorical: List[str] = field(default_factory=lambda: list(CATEGORICAL_FEATURES))

    @property
    def all_features(self) -> List[str]:
        return self.numeric + self.categorical


def load_raw(path: str) -> pd.DataFrame:
    """Load the raw CSV, coercing '?' / blanks to NaN for honest imputation."""
    df = pd.read_csv(path, na_values=["?", "", " "])
    return df


def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deterministic cleaning that is safe to do before the train/test split
    (no information leakage): drop exact duplicate rows and coerce dtypes.
    Value-based imputation is deferred to the pipeline so it is fit on the
    training fold only.
    """
    df = df.copy()
    df = df.drop_duplicates().reset_index(drop=True)
    for col in ALL_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if TARGET in df.columns:
        df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce").astype("Int64")
    return df


def build_preprocessor() -> ColumnTransformer:
    """
    ColumnTransformer:
      - numeric     : median imputation -> standard scaling
      - categorical : most-frequent imputation -> one-hot (dense, ignore unknown)
    """
    numeric_pipe = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    pre = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, NUMERIC_FEATURES),
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return pre


def split_X_y(df: pd.DataFrame):
    X = df[ALL_FEATURES].copy()
    y = df[TARGET].astype(int).copy()
    return X, y
