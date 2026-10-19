"""
Standalone batch/single inference using the saved model.

Examples
--------
    # single record from a JSON file
    python src/predict.py --model model_artifacts/model.joblib \
        --input samples/patient.json

    # score a CSV of many patients -> predictions CSV
    python src/predict.py --input data/heart_clean.csv --out predictions.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocessing import ALL_FEATURES  # noqa: E402


def load_records(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text())
        if isinstance(data, dict):
            data = [data]
        return pd.DataFrame(data)
    return pd.read_csv(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=str(Path(__file__).resolve().parent.parent / "model_artifacts" / "model.joblib"))
    ap.add_argument("--input", required=True, help="CSV or JSON of patient records")
    ap.add_argument("--out", default=None, help="optional output CSV path")
    args = ap.parse_args()

    model = joblib.load(args.model)
    df = load_records(args.input)
    X = df[ALL_FEATURES]

    preds = model.predict(X)
    probs = model.predict_proba(X)[:, 1]
    result = df.copy()
    result["prediction"] = preds
    result["label"] = ["Heart disease" if p == 1 else "No heart disease" for p in preds]
    result["probability_disease"] = probs.round(4)

    cols = ["prediction", "label", "probability_disease"]
    print(result[cols].to_string(index=True))

    if args.out:
        result.to_csv(args.out, index=False)
        print(f"\n[predict] wrote {args.out}")


if __name__ == "__main__":
    main()
