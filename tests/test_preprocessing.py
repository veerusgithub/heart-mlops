"""Unit tests for data loading, cleaning, and the preprocessing pipeline."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preprocessing import (  # noqa: E402
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    basic_clean,
    build_preprocessor,
    split_X_y,
)


@pytest.fixture
def toy_df():
    return pd.DataFrame({
        "age": [63, 37, 41, 56, 63],        # last row duplicates row 0
        "sex": [1, 1, 0, 1, 1],
        "cp": [1, 2, 3, 4, 1],
        "trestbps": [145, 130, 130, 120, 145],
        "chol": [233, 250, 204, 236, 233],
        "fbs": [1, 0, 0, 0, 1],
        "restecg": [2, 2, 0, 1, 2],
        "thalach": [150, 187, 172, 178, 150],
        "exang": [0, 0, 0, 0, 0],
        "oldpeak": [2.3, 3.5, 1.4, 0.8, 2.3],
        "slope": [3, 3, 1, 2, 3],
        "ca": [0, 0, 0, 0, 0],
        "thal": [6, 3, 3, 7, 6],
        "target": [1, 1, 1, 1, 1],
    })


def test_basic_clean_drops_duplicates(toy_df):
    cleaned = basic_clean(toy_df)
    # one exact duplicate (row 4 == row 0) should be removed
    assert len(cleaned) == 4


def test_basic_clean_coerces_question_marks():
    # build the column as object dtype so a '?' token can be present,
    # mirroring a raw UCI row before numeric coercion
    data = {c: pd.Series([0], dtype="object") for c in ALL_FEATURES}
    data[TARGET] = pd.Series([1], dtype="object")
    df = pd.DataFrame(data)
    df.loc[0, "ca"] = "?"
    cleaned = basic_clean(df)
    assert pd.isna(cleaned.loc[0, "ca"])


def test_feature_partition_is_complete_and_disjoint():
    assert set(NUMERIC_FEATURES).isdisjoint(CATEGORICAL_FEATURES)
    assert set(ALL_FEATURES) == set(NUMERIC_FEATURES) | set(CATEGORICAL_FEATURES)
    assert len(ALL_FEATURES) == 13


def test_split_X_y_shapes(toy_df):
    X, y = split_X_y(basic_clean(toy_df))
    assert list(X.columns) == ALL_FEATURES
    assert len(X) == len(y)
    assert set(y.unique()).issubset({0, 1})


def test_preprocessor_handles_missing_values():
    """Pipeline must impute NaNs rather than crash."""
    pre = build_preprocessor()
    df = pd.DataFrame({c: np.random.randint(0, 3, size=20) for c in ALL_FEATURES})
    df = df.astype(float)
    df.loc[0, "chol"] = np.nan
    df.loc[1, "thal"] = np.nan
    out = pre.fit_transform(df)
    assert not np.isnan(out).any()
    assert out.shape[0] == 20


def test_preprocessor_output_is_numeric_and_scaled():
    pre = build_preprocessor()
    df = pd.DataFrame({c: np.random.randint(0, 4, size=50) for c in ALL_FEATURES}).astype(float)
    out = pre.fit_transform(df)
    # numeric block (first len(NUMERIC_FEATURES) cols) should be ~standardized
    num_block = out[:, :len(NUMERIC_FEATURES)]
    assert np.allclose(num_block.mean(axis=0), 0, atol=1e-6)


def test_onehot_expands_categoricals():
    pre = build_preprocessor()
    df = pd.DataFrame({c: np.random.randint(0, 4, size=40) for c in ALL_FEATURES}).astype(float)
    out = pre.fit_transform(df)
    # expanded width must exceed raw feature count due to one-hot encoding
    assert out.shape[1] > len(ALL_FEATURES)
