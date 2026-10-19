"""
Load the UCI Heart Disease (Cleveland) dataset.

Source: UCI ML Repository, file `processed.cleveland.data`
  - no header row, 14 columns, missing values written as "?"
  - raw label `num` is 0-4 (0 = no disease, 1-4 = disease)
  - binarised here: target = 1 if num > 0 else 0   (1 = disease)

Order of sources: local file first, then the UCI URL. There is deliberately
no third-party fallback, so wrong-labelled data can never be used silently.

Usage (from repo root):
    python src/download_data.py
    python src/download_data.py --src "heart+disease/processed.cleveland.data"
"""
from __future__ import annotations

import argparse
import hashlib
import io
import urllib.request
from pathlib import Path

import pandas as pd
ROOT = Path(__file__).resolve().parent.parent   # repo root = parent of src/

COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num",
]
UCI_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "heart-disease/processed.cleveland.data"
)


def read_raw(text_or_path) -> pd.DataFrame:
    return pd.read_csv(text_or_path, header=None, names=COLUMNS, na_values="?")


def load(src: str) -> pd.DataFrame:
    p = Path(src)
    if p.exists():
        print(f"[data] reading local file: {p.resolve()}")
        return read_raw(p)
    print(f"[data] local file not found, trying UCI: {UCI_URL}")
    with urllib.request.urlopen(UCI_URL, timeout=30) as r:
        return read_raw(io.StringIO(r.read().decode("utf-8")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "heart+disease" / "processed.cleveland.data"))
    ap.add_argument("--out", default=str(ROOT / "data" / "heart_raw.csv"))
    args = ap.parse_args()

    df = load(args.src)
    df["target"] = (df["num"] > 0).astype(int)   # 1 = disease
    df = df.drop(columns=["num"])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    print(f"[data] rows: {len(df)}")
    print(f"[data] missing values per column:\n{df.isna().sum()[df.isna().sum() > 0].to_string()}")
    print(f"[data] target balance (1 = disease):\n{df['target'].value_counts().to_string()}")
    print(f"[data] wrote {out.resolve()}  sha256={hashlib.sha256(out.read_bytes()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()