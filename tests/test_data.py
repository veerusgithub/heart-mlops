"""Tests on the bundled UCI Cleveland file and the download/label logic."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from download_data import COLUMNS, read_raw  # noqa: E402

RAW = ROOT / "heart+disease" / "processed.cleveland.data"

pytestmark = pytest.mark.skipif(not RAW.exists(), reason="UCI file not bundled")


def test_columns_follow_uci_documentation_order():
    assert COLUMNS == ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
                       "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num"]


def test_cleveland_shape_and_missing_markers():
    df = read_raw(RAW)
    assert df.shape == (303, 14)
    assert df["ca"].isna().sum() == 4      # '?' -> NaN
    assert df["thal"].isna().sum() == 2


def test_binarised_target_matches_published_counts():
    df = read_raw(RAW)
    target = (df["num"] > 0).astype(int)
    assert target.value_counts().to_dict() == {0: 164, 1: 139}


def test_raw_uci_code_ranges():
    df = read_raw(RAW)
    assert set(df["cp"].unique()) == {1.0, 2.0, 3.0, 4.0}
    assert set(df["thal"].dropna().unique()) == {3.0, 6.0, 7.0}
    assert set(df["slope"].unique()) == {1.0, 2.0, 3.0}
    assert set(df["num"].unique()) == {0, 1, 2, 3, 4}
