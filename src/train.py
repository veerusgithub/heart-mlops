"""
Train, tune, evaluate and track heart-disease classifiers with MLflow.

Pipeline design
---------------
Each candidate is a single sklearn Pipeline = [preprocessor -> classifier],
so preprocessing is fit *inside* each CV fold (no leakage) and the fitted
object serialised at the end already contains the transforms. The API then
loads this one object and is guaranteed train/serve parity.

Models
------
  - Logistic Regression  (linear baseline, interpretable)
  - Random Forest        (non-linear, handles interactions)
Each is tuned with GridSearchCV (5-fold stratified, scoring = ROC-AUC).

Tracking
--------
Every run logs params, CV + hold-out metrics, ROC / confusion-matrix /
feature-importance plots and the fitted model to MLflow (local ./mlruns).
The best model is chosen by cross-validated ROC-AUC on the training split
(never by the hold-out set, which is kept as an unbiased final estimate)
and saved to model_artifacts/.

Usage
-----
    python src/train.py --data data/heart_raw.csv --test-size 0.2 --seed 42
"""
from __future__ import annotations

import argparse
import json
import platform
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline

import joblib

from preprocessing import (
    ALL_FEATURES,
    FeatureSchema,
    basic_clean,
    build_preprocessor,
    load_raw,
    split_X_y,
)

ROOT = Path(__file__).resolve().parent.parent  # repo root
FIG_DIR = ROOT / "reports" / "figures"
ART_DIR = ROOT / "model_artifacts"
SCORING = ["accuracy", "precision", "recall", "f1", "roc_auc"]


def model_space():
    """Return {name: (estimator, param_grid)} for tuning."""
    return {
        "logistic_regression": (
            LogisticRegression(max_iter=1000, class_weight="balanced"),
            {
                "clf__C": [0.01, 0.1, 1.0, 10.0],
                "clf__solver": ["lbfgs", "liblinear"],
            },
        ),
        "random_forest": (
            RandomForestClassifier(class_weight="balanced", random_state=42),
            {
                "clf__n_estimators": [200, 400],
                "clf__max_depth": [None, 5, 10],
                "clf__min_samples_leaf": [1, 2, 4],
                "clf__max_features": ["sqrt", "log2"],
            },
        ),
    }


def plot_roc(y_true, y_score, name, outpath):
    fpr, tpr, _ = roc_curve(y_true, y_score)
    auc = roc_auc_score(y_true, y_score)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#E4572E", lw=2.5, label=f"{name} (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], "--", color="gray", lw=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC Curve — {name}", fontweight="bold")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(outpath, dpi=130)
    plt.close(fig)


def plot_confusion(y_true, y_pred, name, outpath):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ConfusionMatrixDisplay(cm, display_labels=["No disease", "Disease"]).plot(
        ax=ax, cmap="Blues", colorbar=False, values_format="d")
    ax.set_title(f"Confusion Matrix — {name}", fontweight="bold")
    fig.tight_layout()
    fig.savefig(outpath, dpi=130)
    plt.close(fig)


def plot_feature_importance(pipe, name, outpath):
    """Works for RF (impurity) and LogReg (|coef|) on the expanded features."""
    pre = pipe.named_steps["pre"]
    clf = pipe.named_steps["clf"]
    try:
        feat_names = pre.get_feature_names_out()
    except Exception:
        feat_names = np.array(ALL_FEATURES)
    if hasattr(clf, "feature_importances_"):
        imp = clf.feature_importances_
        xlabel = "Impurity importance"
    elif hasattr(clf, "coef_"):
        imp = np.abs(clf.coef_).ravel()
        xlabel = "|coefficient|"
    else:
        return
    order = np.argsort(imp)[::-1][:15]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(len(order)), imp[order][::-1], color="#4C78A8")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([feat_names[i] for i in order][::-1], fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_title(f"Top Feature Importances — {name}", fontweight="bold")
    fig.tight_layout()
    fig.savefig(outpath, dpi=130)
    plt.close(fig)


def evaluate(y_true, y_pred, y_score) -> dict:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
        "roc_auc": roc_auc_score(y_true, y_score),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "data" / "heart_raw.csv"))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--experiment", default="heart-disease-classification")
    parser.add_argument("--tracking-uri", default=f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}")
    args = parser.parse_args()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment)

    df = basic_clean(load_raw(args.data))
    X, y = split_X_y(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, stratify=y, random_state=args.seed)
    print(f"[train] train={X_train.shape} test={X_test.shape} "
          f"pos_rate_train={y_train.mean():.3f}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=args.seed)
    results = {}
    best = {"name": None, "cv_roc_auc": -1.0, "roc_auc": None, "pipe": None, "params": None}

    for name, (estimator, grid) in model_space().items():
        print(f"\n[train] ===== {name} =====")
        with mlflow.start_run(run_name=name):
            pipe = Pipeline([("pre", build_preprocessor()), ("clf", estimator)])
            search = GridSearchCV(pipe, grid, scoring="roc_auc", cv=cv,
                                  n_jobs=-1, refit=True)
            search.fit(X_train, y_train)
            best_pipe = search.best_estimator_

            # Cross-validated metrics on the training set (all SCORING)
            cv_scores = cross_validate(best_pipe, X_train, y_train, cv=cv,
                                       scoring=SCORING, n_jobs=-1)
            cv_summary = {f"cv_{m}_mean": float(np.mean(cv_scores[f"test_{m}"]))
                          for m in SCORING}
            cv_summary.update({f"cv_{m}_std": float(np.std(cv_scores[f"test_{m}"]))
                               for m in SCORING})

            # Hold-out evaluation
            y_pred = best_pipe.predict(X_test)
            y_score = best_pipe.predict_proba(X_test)[:, 1]
            holdout = evaluate(y_test, y_pred, y_score)

            # Plots
            roc_p = FIG_DIR / f"roc_{name}.png"
            cm_p = FIG_DIR / f"confusion_{name}.png"
            fi_p = FIG_DIR / f"importance_{name}.png"
            plot_roc(y_test, y_score, name, roc_p)
            plot_confusion(y_test, y_pred, name, cm_p)
            plot_feature_importance(best_pipe, name, fi_p)

            # ---- MLflow logging ----
            mlflow.log_param("model", name)
            mlflow.log_param("cv_folds", 5)
            mlflow.log_param("test_size", args.test_size)
            mlflow.log_param("seed", args.seed)
            for k, v in search.best_params_.items():
                mlflow.log_param(k, v)
            mlflow.log_metric("best_cv_roc_auc_gridsearch", float(search.best_score_))
            for k, v in cv_summary.items():
                mlflow.log_metric(k, v)
            for k, v in holdout.items():
                mlflow.log_metric(f"holdout_{k}", float(v))
            for p in (roc_p, cm_p, fi_p):
                mlflow.log_artifact(str(p), artifact_path="plots")
            mlflow.sklearn.log_model(
                best_pipe, name="model",
                serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
            )

            print(f"[train] best params: {search.best_params_}")
            print(f"[train] CV ROC-AUC: {cv_summary['cv_roc_auc_mean']:.4f} "
                  f"+/- {cv_summary['cv_roc_auc_std']:.4f}")
            print(f"[train] hold-out: " +
                  ", ".join(f"{k}={v:.4f}" for k, v in holdout.items()))

            results[name] = {"best_params": search.best_params_,
                             "cv": cv_summary, "holdout": holdout}
            if cv_summary["cv_roc_auc_mean"] > best["cv_roc_auc"]:
                best = {"name": name, "cv_roc_auc": cv_summary["cv_roc_auc_mean"],
                        "roc_auc": holdout["roc_auc"],
                        "pipe": best_pipe, "params": search.best_params_}

    # ---- Persist the winning model + schema + metrics ----
    print(f"\n[train] BEST MODEL: {best['name']} "
          f"(CV ROC-AUC={best['cv_roc_auc']:.4f}, "
          f"hold-out ROC-AUC={best['roc_auc']:.4f})")
    joblib.dump(best["pipe"], ART_DIR / "model.joblib")
    schema = FeatureSchema()
    (ART_DIR / "feature_schema.json").write_text(json.dumps({
        "target": schema.target,
        "numeric": schema.numeric,
        "categorical": schema.categorical,
        "all_features": schema.all_features,
    }, indent=2))
    (ART_DIR / "metadata.json").write_text(json.dumps({
        "best_model": best["name"],
        "best_params": best["params"],
        "selection_metric": "cv_roc_auc_mean",
        "cv_roc_auc": best["cv_roc_auc"],
        "holdout_roc_auc": best["roc_auc"],
        "sklearn_input_order": ALL_FEATURES,
        "trained_on_rows": int(len(df)),
        "sklearn_version": __import__("sklearn").__version__,
        "python_version": platform.python_version(),
        "seed": args.seed,
    }, indent=2, default=str))
    (ROOT / "reports" / "metrics.json").write_text(json.dumps(results, indent=2,
                                                            default=str))
    print(f"[train] saved -> {ART_DIR/'model.joblib'}")
    print(f"[train] metrics -> reports/metrics.json")


if __name__ == "__main__":
    main()
