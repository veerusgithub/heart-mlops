"""
Exploratory Data Analysis for the Heart Disease dataset.

Generates professional visualisations and a small text summary:
  - target class balance
  - feature histograms (grid)
  - correlation heatmap
  - numeric-feature distributions split by target (box/violin)
All figures are written to reports/figures/ for the report and MLflow.

Usage
-----
    python src/eda.py --data data/heart_raw.csv --outdir reports/figures
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from preprocessing import ALL_FEATURES, NUMERIC_FEATURES, TARGET, basic_clean, load_raw

ROOT = Path(__file__).resolve().parent.parent  # repo root
sns.set_theme(style="whitegrid", context="talk")
PALETTE = {0: "#4C78A8", 1: "#E4572E"}


def plot_class_balance(df: pd.DataFrame, outdir: Path) -> dict:
    counts = df[TARGET].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(["No disease (0)", "Disease (1)"], counts.values,
                  color=[PALETTE[0], PALETTE[1]], edgecolor="black", linewidth=0.6)
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, str(v),
                ha="center", va="bottom", fontsize=14, fontweight="bold")
    ax.set_title("Target Class Balance", fontweight="bold")
    ax.set_ylabel("Patient count")
    ax.set_ylim(0, counts.max() * 1.15)
    fig.tight_layout()
    fig.savefig(outdir / "class_balance.png", dpi=130)
    plt.close(fig)
    total = int(counts.sum())
    return {"no_disease": int(counts.get(0, 0)),
            "disease": int(counts.get(1, 0)),
            "total": total,
            "disease_ratio": round(float(counts.get(1, 0)) / total, 4)}


def plot_histograms(df: pd.DataFrame, outdir: Path) -> None:
    feats = ALL_FEATURES
    ncols = 4
    nrows = int(np.ceil(len(feats) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.6 * nrows))
    axes = axes.flatten()
    for i, col in enumerate(feats):
        ax = axes[i]
        ax.hist(df[col].dropna(), bins=20, color="#4C78A8",
                edgecolor="white", alpha=0.9)
        ax.set_title(col, fontsize=14, fontweight="bold")
        ax.tick_params(labelsize=10)
    for j in range(len(feats), len(axes)):
        axes[j].axis("off")
    fig.suptitle("Feature Distributions (Histograms)", fontsize=20, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(outdir / "histograms.png", dpi=120)
    plt.close(fig)


def plot_correlation(df: pd.DataFrame, outdir: Path) -> None:
    corr = df[ALL_FEATURES + [TARGET]].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, cmap="RdBu_r", center=0, annot=True,
                fmt=".2f", annot_kws={"size": 9}, square=True,
                cbar_kws={"shrink": 0.8, "label": "Pearson r"}, ax=ax,
                linewidths=0.5, linecolor="white")
    ax.set_title("Correlation Heatmap", fontweight="bold", pad=14)
    fig.tight_layout()
    fig.savefig(outdir / "correlation_heatmap.png", dpi=120)
    plt.close(fig)


def plot_target_splits(df: pd.DataFrame, outdir: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    for i, col in enumerate(NUMERIC_FEATURES):
        ax = axes[i]
        data = [df.loc[df[TARGET] == 0, col].dropna(),
                df.loc[df[TARGET] == 1, col].dropna()]
        parts = ax.violinplot(data, showmeans=True, showmedians=False)
        for pc, c in zip(parts["bodies"], [PALETTE[0], PALETTE[1]]):
            pc.set_facecolor(c)
            pc.set_alpha(0.65)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(["No disease", "Disease"], fontsize=11)
        ax.set_title(col, fontsize=14, fontweight="bold")
    fig.suptitle("Numeric Features by Target Class", fontsize=20, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(outdir / "feature_by_target.png", dpi=120)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "data" / "heart_raw.csv"))
    parser.add_argument("--outdir", default=str(ROOT / "reports" / "figures"))
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = basic_clean(load_raw(args.data))
    print(f"[eda] cleaned shape: {df.shape}")

    summary = {
        "n_rows": int(len(df)),
        "n_features": len(ALL_FEATURES),
        "missing_values_total": int(df[ALL_FEATURES].isna().sum().sum()),
        "missing_by_column": {k: int(v) for k, v in
                              df[ALL_FEATURES].isna().sum().items() if v > 0},
    }
    summary["class_balance"] = plot_class_balance(df, outdir)
    plot_histograms(df, outdir)
    plot_correlation(df, outdir)
    plot_target_splits(df, outdir)

    # correlations with target, sorted
    corr_t = (df[ALL_FEATURES + [TARGET]].corr(numeric_only=True)[TARGET]
              .drop(TARGET).sort_values(key=abs, ascending=False))
    summary["top_target_correlations"] = {k: round(float(v), 4)
                                          for k, v in corr_t.head(8).items()}

    (outdir.parent / "eda_summary.json").write_text(json.dumps(summary, indent=2))
    # Save cleaned dataset for downstream + the deliverable "cleaned dataset"
    clean_path = ROOT / "data" / "heart_clean.csv"
    df.to_csv(clean_path, index=False)

    print("[eda] figures written to", outdir)
    print("[eda] summary:\n", json.dumps(summary, indent=2))
    print("[eda] cleaned dataset ->", clean_path)


if __name__ == "__main__":
    main()
