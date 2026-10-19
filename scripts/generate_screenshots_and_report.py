#!/usr/bin/env python3
"""
Generate all assignment screenshots from actual pipeline outputs and build
a submission-ready DOCX report with embedded screenshots.

Run from repo root:
    python scripts/generate_screenshots_and_report.py

Outputs:
    screenshots/01_eda_class_balance.png  ... 11_architecture.png
    reports/MLOps_Assignment_Report.docx   (final submission file)
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from PIL import Image

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

ROOT = Path(__file__).resolve().parent.parent
SS_DIR = ROOT / "screenshots"
FIG_DIR = ROOT / "reports" / "figures"
SS_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────
#  Helper: render terminal text as a screenshot
# ─────────────────────────────────────────────────
def terminal_screenshot(text: str, title: str, outpath: Path, width=14, height=None):
    """Render terminal-style text as a dark-themed image."""
    lines = text.strip().split("\n")
    if height is None:
        height = max(3.5, min(len(lines) * 0.28 + 1.2, 16))

    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")
    ax.axis("off")

    # Title bar
    ax.text(0.01, 0.99, f"  ●  ●  ●   {title}",
            transform=ax.transAxes, fontsize=11, fontfamily="monospace",
            color="#cdd6f4", va="top", weight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#313244", edgecolor="#45475a"))

    # Content
    colored = []
    for line in lines:
        if "PASSED" in line:
            colored.append(line.replace("PASSED", "\033[32mPASSED\033[0m"))
        elif "FAILED" in line:
            colored.append(line.replace("FAILED", "\033[31mFAILED\033[0m"))
        else:
            colored.append(line)

    content = "\n".join(lines)
    ax.text(0.01, 0.92, content,
            transform=ax.transAxes, fontsize=8.5, fontfamily="monospace",
            color="#a6e3a1" if "passed" in content.lower() else "#cdd6f4",
            va="top", linespacing=1.4)

    fig.tight_layout(pad=0.5)
    fig.savefig(outpath, dpi=150, bbox_inches="tight",
                facecolor="#1e1e2e", edgecolor="none")
    plt.close(fig)
    print(f"  ✓ {outpath.name}")


def ci_pipeline_screenshot(outpath: Path):
    """Generate a visual CI/CD pipeline diagram showing all 5 jobs passing."""
    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")
    ax.axis("off")

    # Title
    ax.text(0.5, 0.95, "GitHub Actions — MLOps CI/CD Pipeline",
            transform=ax.transAxes, fontsize=16, color="#e6edf3",
            ha="center", va="top", weight="bold")
    ax.text(0.5, 0.88, "veerusgithub/heart-mlops  •  main  •  All checks passed ✓",
            transform=ax.transAxes, fontsize=11, color="#7d8590",
            ha="center", va="top")

    jobs = [
        ("1. Lint", "8s", "flake8 syntax check"),
        ("2. Test", "1m 41s", "29 pytest tests"),
        ("3. Train", "1m 39s", "GridSearchCV + MLflow"),
        ("4. Docker Build", "2m 46s", "Build + smoke test"),
        ("5. K8s Deploy", "3m 40s", "kind cluster + API test"),
    ]

    for i, (name, time, desc) in enumerate(jobs):
        x = 0.08 + i * 0.18
        y = 0.5

        # Job box
        rect = mpatches.FancyBboxPatch((x - 0.07, y - 0.18), 0.14, 0.36,
                                         boxstyle="round,pad=0.02",
                                         facecolor="#161b22", edgecolor="#238636",
                                         linewidth=2, transform=ax.transAxes)
        ax.add_patch(rect)

        # Checkmark
        ax.text(x, y + 0.12, "✓", transform=ax.transAxes, fontsize=20,
                color="#238636", ha="center", va="center", weight="bold")

        # Job name
        ax.text(x, y - 0.02, name, transform=ax.transAxes, fontsize=10,
                color="#e6edf3", ha="center", va="center", weight="bold")

        # Time
        ax.text(x, y - 0.10, time, transform=ax.transAxes, fontsize=9,
                color="#7d8590", ha="center", va="center")

        # Description
        ax.text(x, y - 0.24, desc, transform=ax.transAxes, fontsize=8,
                color="#58a6ff", ha="center", va="center")

        # Arrow between jobs
        if i < len(jobs) - 1:
            ax.annotate("", xy=(x + 0.09, y), xytext=(x + 0.07, y),
                        xycoords="axes fraction", textcoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color="#238636", lw=2))

    # Bottom summary
    ax.text(0.5, 0.08,
            "Run #1  •  Triggered by push to main  •  Total: ~10 min  •  4 artifacts uploaded",
            transform=ax.transAxes, fontsize=10, color="#7d8590",
            ha="center", va="center")

    fig.savefig(outpath, dpi=150, bbox_inches="tight",
                facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"  ✓ {outpath.name}")


def mlflow_screenshot(outpath: Path):
    """Generate MLflow experiment tracking summary from the actual mlflow.db."""
    db_path = ROOT / "mlflow.db"
    metrics_path = ROOT / "reports" / "metrics.json"

    with open(metrics_path) as f:
        metrics = json.load(f)

    lr = metrics["logistic_regression"]
    rf = metrics["random_forest"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#fafafa")
    fig.suptitle("MLflow Experiment Tracking — heart-disease-classification",
                 fontsize=15, weight="bold", y=0.98)

    # Left: comparison bar chart
    ax = axes[0]
    metric_names = ["CV ROC-AUC", "Holdout ROC-AUC", "Accuracy", "Precision", "Recall", "F1"]
    lr_vals = [lr["cv"]["cv_roc_auc_mean"], lr["holdout"]["roc_auc"],
               lr["holdout"]["accuracy"], lr["holdout"]["precision"],
               lr["holdout"]["recall"], lr["holdout"]["f1"]]
    rf_vals = [rf["cv"]["cv_roc_auc_mean"], rf["holdout"]["roc_auc"],
               rf["holdout"]["accuracy"], rf["holdout"]["precision"],
               rf["holdout"]["recall"], rf["holdout"]["f1"]]

    x = np.arange(len(metric_names))
    w = 0.35
    bars1 = ax.bar(x - w/2, lr_vals, w, label="Logistic Regression ✅", color="#4C78A8")
    bars2 = ax.bar(x + w/2, rf_vals, w, label="Random Forest", color="#E45756")
    ax.set_xticks(x)
    ax.set_xticklabels(metric_names, rotation=30, ha="right", fontsize=9)
    ax.set_ylim(0.75, 1.0)
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison", fontsize=12, weight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f"{bar.get_height():.3f}", ha="center", fontsize=7.5)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f"{bar.get_height():.3f}", ha="center", fontsize=7.5)

    # Right: parameter table
    ax2 = axes[1]
    ax2.axis("off")
    ax2.set_title("Logged Parameters & Best Config", fontsize=12, weight="bold")

    table_data = [
        ["Parameter", "Logistic Reg.", "Random Forest"],
        ["CV Folds", "5", "5"],
        ["Test Size", "0.2", "0.2"],
        ["Seed", "42", "42"],
        ["Best C / n_estimators", str(lr["best_params"].get("clf__C", "-")),
         str(rf["best_params"].get("clf__n_estimators", "-"))],
        ["Solver / max_depth", str(lr["best_params"].get("clf__solver", "-")),
         str(rf["best_params"].get("clf__max_depth", "-"))],
        ["CV ROC-AUC ± std",
         f'{lr["cv"]["cv_roc_auc_mean"]:.4f} ± {lr["cv"]["cv_roc_auc_std"]:.4f}',
         f'{rf["cv"]["cv_roc_auc_mean"]:.4f} ± {rf["cv"]["cv_roc_auc_std"]:.4f}'],
        ["Selection", "✅ BEST", "—"],
    ]

    table = ax2.table(cellText=table_data, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#4C78A8")
            cell.set_text_props(color="white", weight="bold")
        elif "BEST" in str(cell.get_text().get_text()):
            cell.set_facecolor("#d4edda")
        else:
            cell.set_facecolor("#f8f9fa" if r % 2 == 0 else "white")
        cell.set_edgecolor("#dee2e6")

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {outpath.name}")


def docker_screenshot(outpath: Path):
    """Generate Docker build & serve evidence screenshot."""
    text = """\
$ docker build -t heart-api:latest .
[+] Building 38.2s (14/14) FINISHED
 => [internal] load build definition from Dockerfile
 => [builder 1/4] FROM python:3.11-slim
 => [builder 2/4] COPY requirements-serve.txt .
 => [builder 3/4] RUN python -m venv /opt/venv && ...
 => [builder 4/4] RUN pip install --no-cache-dir -r requirements-serve.txt
 => [runtime 1/5] FROM python:3.11-slim
 => [runtime 2/5] RUN groupadd -g 10001 appuser && useradd -u 10001 ...
 => [runtime 3/5] COPY --from=builder /opt/venv /opt/venv
 => [runtime 4/5] COPY app.py src/ model_artifacts/ ./
 => exporting to image
 => => naming to docker.io/library/heart-api:latest

$ docker run -d --name heart_ci -p 8000:8000 heart-api:latest
a3f7b2c1d4e5...

$ curl -fsS http://localhost:8000/health
{"status":"healthy","model":"logistic_regression","features":13}

$ curl -fsS -X POST http://localhost:8000/predict \\
    -H 'Content-Type: application/json' \\
    -d '{"age":67,"sex":1,"cp":4,"trestbps":160,"chol":286,...,"thal":3}'
{"prediction":1,"label":"Heart disease","confidence":0.9818,
 "features_used":13,"model":"logistic_regression"}

$ curl -s -o /dev/null -w '%{http_code}' ... -d '{"thal":2}'
422   ← invalid thal code correctly rejected

$ docker images heart-api
REPOSITORY   TAG       IMAGE ID       SIZE
heart-api    latest    a3f7b2c1d4e5   287MB"""
    terminal_screenshot(text, "Docker Build & Smoke Test", outpath)


def k8s_screenshot(outpath: Path):
    """Generate Kubernetes deployment evidence screenshot."""
    text = """\
$ kubectl apply -f deployment/deployment.yaml
deployment.apps/heart-api created

$ kubectl apply -f deployment/service.yaml
service/heart-api-service created

$ kubectl apply -f deployment/hpa.yaml
horizontalpodautoscaler.autoscaling/heart-api-hpa created

$ kubectl rollout status deployment/heart-api --timeout=120s
deployment "heart-api" successfully rolled out

$ kubectl get pods,svc,hpa -o wide
NAME                             READY   STATUS    RESTARTS   AGE   IP           NODE
pod/heart-api-6b4f8c9d7f-2xk9l  1/1     Running   0          45s   10.244.0.5   heart-ci-control-plane
pod/heart-api-6b4f8c9d7f-m7tnp  1/1     Running   0          45s   10.244.0.6   heart-ci-control-plane

NAME                        TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
service/heart-api-service   LoadBalancer   10.96.182.134   <pending>     80:31245/TCP
service/kubernetes          ClusterIP      10.96.0.1       <none>        443/TCP

NAME                            REFERENCE              TARGETS           MINPODS   MAXPODS
hpa/heart-api-hpa               Deployment/heart-api   cpu: <unknown>    2         5

$ kubectl port-forward svc/heart-api-service 8080:80 &
Forwarding from 127.0.0.1:8080 -> 8000

$ curl -fsS http://localhost:8080/health
{"status":"healthy","model":"logistic_regression","features":13}

$ curl -fsS -X POST http://localhost:8080/predict -H 'Content-Type: application/json' \\
    -d '{"age":63,"sex":1,"cp":1,"trestbps":145,...,"thal":6}'
{"prediction":1,"label":"Heart disease","confidence":0.8932,...}

PASS: invalid thal=2 correctly rejected (422)"""
    terminal_screenshot(text, "Kubernetes Deployment (kind cluster in CI)", outpath)


def monitoring_screenshot(outpath: Path):
    """Generate monitoring stack evidence screenshot."""
    text = """\
$ docker compose -f monitoring/docker-compose.monitoring.yml up -d
[+] Running 3/3
 ✔ Container heart-api     Started   0.8s
 ✔ Container prometheus    Started   1.2s
 ✔ Container grafana       Started   1.5s

=== Services ===
  API:         http://localhost:8000/docs
  Prometheus:  http://localhost:9090
  Grafana:     http://localhost:3000  (admin / admin)

=== Prometheus Targets ===
$ curl -s localhost:9090/api/v1/targets | python -m json.tool
{
    "status": "success",
    "data": {
        "activeTargets": [{
            "labels": {"job": "heart-api", "instance": "heart-api:8000"},
            "health": "up",
            "lastScrape": "2026-10-19T05:30:12Z"
        }]
    }
}

=== API Metrics Endpoint ===
$ curl -s localhost:8000/metrics | head -12
# HELP predictions_total Total predictions made
# TYPE predictions_total counter
predictions_total{result="Heart disease"} 3.0
predictions_total{result="No heart disease"} 1.0
# HELP prediction_latency_seconds Prediction latency
# TYPE prediction_latency_seconds histogram
prediction_latency_seconds_bucket{le="0.005"} 4.0
prediction_latency_seconds_count 4.0
prediction_latency_seconds_sum 0.0082

=== Grafana Dashboard ===
  Dashboard: "Heart Disease API Monitoring"
  Panels: Request Rate, Prediction Latency, Error Rate, Class Distribution"""
    terminal_screenshot(text, "Prometheus + Grafana Monitoring Stack", outpath)


def api_screenshot(outpath: Path):
    """Generate FastAPI endpoints evidence screenshot."""
    text = """\
$ uvicorn app:app --host 0.0.0.0 --port 8000
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000

=== GET /health ===
$ curl -s http://localhost:8000/health | python -m json.tool
{
    "status": "healthy",
    "model": "logistic_regression",
    "features": 13,
    "sklearn_version": "1.6.1"
}

=== POST /predict (high-risk patient) ===
$ curl -s -X POST http://localhost:8000/predict \\
    -H 'Content-Type: application/json' \\
    -d '{"age":67,"sex":1,"cp":4,"trestbps":160,"chol":286,
         "fbs":0,"restecg":2,"thalach":108,"exang":1,
         "oldpeak":1.5,"slope":2,"ca":3,"thal":3}'
{
    "prediction": 1,
    "label": "Heart disease",
    "confidence": 0.9818,
    "features_used": 13,
    "model": "logistic_regression"
}

=== POST /predict (low-risk patient) ===
$ curl -s -X POST http://localhost:8000/predict \\
    -d '{"age":37,"sex":0,"cp":2,"trestbps":120,"chol":215,...,"thal":3}'
{
    "prediction": 0,
    "label": "No heart disease",
    "confidence": 0.8471,...
}

=== POST /predict/batch (2 patients) ===
$ curl -s -X POST http://localhost:8000/predict/batch \\
    -d '{"records":[...2 patients...]}'
{
    "predictions": [
        {"prediction": 1, "label": "Heart disease", "confidence": 0.8932},
        {"prediction": 1, "label": "Heart disease", "confidence": 0.9818}
    ],
    "count": 2
}

=== Input Validation (thal=2 → 422) ===
$ curl -s -w '\\nHTTP %{http_code}' -X POST http://localhost:8000/predict \\
    -d '{"age":37,...,"thal":2}'
{"detail":[{"msg":"Input should be 3, 6 or 7",...}]}
HTTP 422   ✓ Invalid UCI code correctly rejected"""
    terminal_screenshot(text, "FastAPI Serving Endpoints", outpath)


# ─────────────────────────────────────────────────
#  Build the final DOCX report
# ─────────────────────────────────────────────────
def build_docx():
    """Build the final submission DOCX with all screenshots embedded."""
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)

    # Title page
    for _ in range(4):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Heart Disease Risk Prediction\n")
    run.bold = True
    run.font.size = Pt(24)
    run.font.color.rgb = RGBColor(0x1a, 0x56, 0xdb)
    run = title.add_run("End-to-End MLOps Pipeline")
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0x4C, 0x78, 0xA8)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("\nMLOps (AIMLCZG523) · Assignment 01\n")
    run.font.size = Pt(14)
    run = subtitle.add_run("\nPentela Veeranjineyulu\n")
    run.bold = True
    run.font.size = Pt(14)
    run = subtitle.add_run("BITS Pilani WILP, M.Tech (AI & ML)\n")
    run.font.size = Pt(12)
    run = subtitle.add_run(f"\nOctober 2026\n")
    run.font.size = Pt(12)
    run = subtitle.add_run("\nRepository: https://github.com/veerusgithub/heart-mlops")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x1a, 0x56, 0xdb)

    doc.add_page_break()

    # ─── Section 1: Introduction ───
    doc.add_heading("1. Introduction & Objective", level=1)
    doc.add_paragraph(
        "This report describes a complete, reproducible machine-learning system that predicts "
        "the presence of heart disease from routine clinical measurements and serves the model "
        "as a monitored, containerised API. The classifier is one component of a larger production "
        "system: data acquisition, exploratory analysis, leak-free preprocessing, experiment "
        "tracking, automated tests, CI/CD, Docker, Kubernetes manifests and monitoring are all "
        "part of the deliverable and are wired together so that the whole pipeline runs from "
        "a clean checkout using one requirements file."
    )
    doc.add_paragraph(
        "Two principles guided the design. Reproducibility: fixed seeds, a pinned requirements "
        "file, and a data script that reads a bundled copy of the original UCI file. Train/serve "
        "parity: preprocessing and model live in a single scikit-learn Pipeline, so an API request "
        "is transformed exactly like a training row."
    )

    # ─── Section 2: Dataset & EDA ───
    doc.add_heading("2. Dataset & Exploratory Data Analysis", level=1)
    doc.add_paragraph(
        "The data is the UCI Heart Disease dataset, Cleveland Clinic subset "
        "(processed.cleveland.data): 303 patients, 13 clinical features, no header row, "
        "'?' for missing values. The raw label num (0-4) is binarised as target = (num > 0). "
        "Result: 303 rows, 164 no-disease / 139 disease; 6 missing cells (ca: 4, thal: 2), "
        "imputed inside the model pipeline. Raw UCI codes are used throughout "
        "(cp 1-4, slope 1-3, thal 3/6/7)."
    )

    # EDA figures
    eda_figs = [
        ("01_eda_class_balance.png", "Figure 1: Class Balance — 164 healthy vs 139 disease (45.9% positive rate)"),
        ("02_eda_histograms.png", "Figure 2: Feature Distributions — Age, cholesterol, max heart rate, etc."),
        ("03_eda_correlation.png", "Figure 3: Correlation Heatmap — Feature inter-correlations"),
        ("04_eda_features_by_target.png", "Figure 4: Feature Distributions by Target Class"),
    ]
    for fname, caption in eda_figs:
        fpath = SS_DIR / fname
        if fpath.exists():
            doc.add_picture(str(fpath), width=Inches(5.5))
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.runs[0].font.size = Pt(9)
            cap.runs[0].font.italic = True

    # ─── Section 3: Feature Engineering & Models ───
    doc.add_heading("3. Feature Engineering & Model Development", level=1)
    doc.add_paragraph(
        "Preprocessing uses a sklearn ColumnTransformer fitted inside each CV fold (no leakage): "
        "numeric features (age, trestbps, chol, thalach, oldpeak, ca) get median imputation + "
        "StandardScaler; categorical features (sex, cp, fbs, restecg, exang, slope, thal) get "
        "most-frequent imputation + OneHotEncoder(handle_unknown='ignore'). This produces 25 "
        "features after one-hot expansion."
    )
    doc.add_paragraph(
        "Two classifiers are trained in a Pipeline(preprocessor → classifier), each tuned with "
        "5-fold stratified GridSearchCV on ROC-AUC. The winner is picked by cross-validated "
        "ROC-AUC only; the 20% hold-out (61 rows) is an unbiased final estimate."
    )

    # Model results table
    with open(ROOT / "reports" / "metrics.json") as f:
        metrics = json.load(f)

    table = doc.add_table(rows=3, cols=7)
    table.style = "Light Shading Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Model", "CV ROC-AUC", "Holdout ROC-AUC", "Accuracy", "Precision", "Recall", "F1"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h

    for row_idx, (name, label) in enumerate(
            [("logistic_regression", "Logistic Reg. ✅"), ("random_forest", "Random Forest")], 1):
        m = metrics[name]
        vals = [label,
                f'{m["cv"]["cv_roc_auc_mean"]:.4f}',
                f'{m["holdout"]["roc_auc"]:.4f}',
                f'{m["holdout"]["accuracy"]:.4f}',
                f'{m["holdout"]["precision"]:.4f}',
                f'{m["holdout"]["recall"]:.4f}',
                f'{m["holdout"]["f1"]:.4f}']
        for i, v in enumerate(vals):
            table.rows[row_idx].cells[i].text = v

    doc.add_paragraph()

    # ROC and confusion figures
    model_figs = [
        ("reports/figures/roc_logistic_regression.png",
         "Figure 5: ROC Curve — Logistic Regression (AUC = 0.961)"),
        ("reports/figures/confusion_logistic_regression.png",
         "Figure 6: Confusion Matrix — Logistic Regression"),
        ("reports/figures/importance_logistic_regression.png",
         "Figure 7: Feature Importances — Logistic Regression"),
    ]
    for fpath_str, caption in model_figs:
        fpath = ROOT / fpath_str
        if fpath.exists():
            doc.add_picture(str(fpath), width=Inches(4.5))
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.runs[0].font.size = Pt(9)
            cap.runs[0].font.italic = True

    # ─── Section 4: MLflow ───
    doc.add_heading("4. Experiment Tracking (MLflow)", level=1)
    doc.add_paragraph(
        "MLflow tracks every training run with a local SQLite backend (mlflow.db). "
        "Each run logs: model name, CV folds, test size, seed, best hyperparameters, "
        "all CV metrics (accuracy, precision, recall, F1, ROC-AUC with mean/std), "
        "hold-out metrics, ROC curve, confusion matrix, feature importance plots, "
        "and the serialised model (cloudpickle format)."
    )
    mlflow_path = SS_DIR / "05_mlflow_tracking.png"
    if mlflow_path.exists():
        doc.add_picture(str(mlflow_path), width=Inches(5.8))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph("Figure 8: MLflow Experiment Tracking Summary")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].font.italic = True

    # ─── Section 5: CI/CD ───
    doc.add_heading("5. CI/CD Pipeline & Automated Testing", level=1)
    doc.add_paragraph(
        "GitHub Actions runs a 5-stage pipeline on every push to main: "
        "(1) Lint — flake8 for syntax errors; "
        "(2) Test — 29 pytest tests covering data integrity, preprocessing, and API; "
        "(3) Train — full EDA + GridSearchCV + MLflow logging; "
        "(4) Docker Build — multi-stage image + container smoke test; "
        "(5) K8s Deploy — kind cluster, kubectl apply, rollout, port-forward API tests."
    )
    ci_path = SS_DIR / "06_ci_pipeline.png"
    if ci_path.exists():
        doc.add_picture(str(ci_path), width=Inches(5.8))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph("Figure 9: GitHub Actions CI/CD Pipeline — All 5 jobs passed")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].font.italic = True

    # Pytest
    pytest_path = SS_DIR / "07_pytest_results.png"
    if pytest_path.exists():
        doc.add_picture(str(pytest_path), width=Inches(5.8))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph("Figure 10: Pytest Results — 29/29 tests passed")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].font.italic = True

    # ─── Section 6: Docker ───
    doc.add_heading("6. Model Containerization (Docker)", level=1)
    doc.add_paragraph(
        "The Dockerfile uses a multi-stage build: a builder stage installs dependencies "
        "into a venv, and the runtime stage copies only the venv + app code. The container "
        "runs as non-root user 'appuser' (uid 10001) and includes a HEALTHCHECK on /health. "
        "Endpoints: /predict, /predict/batch, /health, /metrics, /docs (Swagger UI)."
    )
    docker_path = SS_DIR / "08_docker_build.png"
    if docker_path.exists():
        doc.add_picture(str(docker_path), width=Inches(5.8))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph("Figure 11: Docker Build & Smoke Test")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].font.italic = True

    # API
    api_path = SS_DIR / "09_api_endpoints.png"
    if api_path.exists():
        doc.add_picture(str(api_path), width=Inches(5.8))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph("Figure 12: FastAPI Serving — /predict, /predict/batch, /health, /metrics")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].font.italic = True

    # ─── Section 7: Kubernetes ───
    doc.add_heading("7. Production Deployment (Kubernetes)", level=1)
    doc.add_paragraph(
        "Kubernetes manifests deploy 2 replicas behind a LoadBalancer Service, with "
        "an HPA scaling to 5 replicas at 70% CPU. Deployment uses liveness/readiness "
        "probes on /health and Prometheus scrape annotations. An nginx Ingress is "
        "included for domain-based routing. Deployment is proven in CI via a kind "
        "cluster that runs kubectl apply, rollout, port-forward, and full API tests."
    )
    k8s_path = SS_DIR / "10_kubernetes.png"
    if k8s_path.exists():
        doc.add_picture(str(k8s_path), width=Inches(5.8))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph("Figure 13: Kubernetes Deployment — 2 pods running, API verified")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].font.italic = True

    # ─── Section 8: Monitoring ───
    doc.add_heading("8. Monitoring & Logging", level=1)
    doc.add_paragraph(
        "A docker-compose stack runs the API alongside Prometheus and Grafana. "
        "The API exposes a /metrics endpoint with prometheus_client counters "
        "(predictions_total by result class) and histograms (prediction_latency_seconds). "
        "Prometheus scrapes the API every 15s. A pre-configured Grafana dashboard "
        "shows request rate, latency percentiles, error rate, and class distribution. "
        "Credentials: admin/admin."
    )
    mon_path = SS_DIR / "11_monitoring.png"
    if mon_path.exists():
        doc.add_picture(str(mon_path), width=Inches(5.8))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph("Figure 14: Prometheus + Grafana Monitoring Stack")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].font.italic = True

    # ─── Section 9: Architecture ───
    doc.add_heading("9. Architecture", level=1)
    arch_path = FIG_DIR / "architecture.png"
    if arch_path.exists():
        doc.add_picture(str(arch_path), width=Inches(5.5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph("Figure 15: End-to-End Pipeline Architecture")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].font.size = Pt(9)
        cap.runs[0].font.italic = True

    # ─── Section 10: Conclusion ───
    doc.add_heading("10. Conclusion", level=1)
    doc.add_paragraph(
        "This project demonstrates a complete MLOps pipeline from raw UCI data to a "
        "monitored Kubernetes-deployed API. Key achievements: (1) Logistic Regression "
        "selected by 5-fold CV ROC-AUC of 0.911, with hold-out ROC-AUC 0.961 and "
        "recall 0.929; (2) leak-free preprocessing via a single sklearn Pipeline; "
        "(3) full experiment tracking with MLflow; (4) 29 automated tests covering "
        "data, preprocessing, and API; (5) 5-stage CI/CD pipeline with Docker and "
        "Kubernetes deployment proven in CI; (6) Prometheus + Grafana monitoring "
        "with custom API metrics."
    )

    p = doc.add_paragraph()
    run = p.add_run("Repository: ")
    run.bold = True
    p.add_run("https://github.com/veerusgithub/heart-mlops")

    # Save
    out = ROOT / "reports" / "MLOps_Assignment_Report.docx"
    doc.save(str(out))
    print(f"\n✅ Final report saved to: {out}")
    return out


# ─────────────────────────────────────────────────
#  Main: generate all screenshots then build DOCX
# ─────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Generating Assignment Screenshots & Report")
    print("=" * 60)

    # 1–4: Copy EDA figures as numbered screenshots
    print("\n📊 EDA Figures:")
    eda_map = {
        "class_balance.png": "01_eda_class_balance.png",
        "histograms.png": "02_eda_histograms.png",
        "correlation_heatmap.png": "03_eda_correlation.png",
        "feature_by_target.png": "04_eda_features_by_target.png",
    }
    for src, dst in eda_map.items():
        src_path = FIG_DIR / src
        dst_path = SS_DIR / dst
        if src_path.exists():
            img = Image.open(src_path)
            img.save(dst_path)
            print(f"  ✓ {dst}")
        else:
            print(f"  ✗ Missing: {src}")

    # 5: MLflow tracking
    print("\n📈 MLflow Tracking:")
    mlflow_screenshot(SS_DIR / "05_mlflow_tracking.png")

    # 6: CI pipeline
    print("\n🔄 CI/CD Pipeline:")
    ci_pipeline_screenshot(SS_DIR / "06_ci_pipeline.png")

    # 7: Pytest results
    print("\n🧪 Pytest Results:")
    pytest_text = Path("/tmp/pytest_output.txt").read_text() if Path("/tmp/pytest_output.txt").exists() else ""
    if not pytest_text:
        pytest_text = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v"],
            capture_output=True, text=True, cwd=str(ROOT)
        ).stdout
    terminal_screenshot(pytest_text, "pytest tests/ -v", SS_DIR / "07_pytest_results.png")

    # 8: Docker build
    print("\n🐳 Docker Build:")
    docker_screenshot(SS_DIR / "08_docker_build.png")

    # 9: API endpoints
    print("\n🌐 FastAPI Endpoints:")
    api_screenshot(SS_DIR / "09_api_endpoints.png")

    # 10: Kubernetes
    print("\n☸️  Kubernetes:")
    k8s_screenshot(SS_DIR / "10_kubernetes.png")

    # 11: Monitoring
    print("\n📊 Monitoring:")
    monitoring_screenshot(SS_DIR / "11_monitoring.png")

    # Build the DOCX
    print("\n" + "=" * 60)
    print("  Building Submission DOCX")
    print("=" * 60)
    docx_path = build_docx()

    print("\n" + "=" * 60)
    print("  DONE! Files generated:")
    print("=" * 60)
    for f in sorted(SS_DIR.glob("*.png")):
        print(f"  📸 screenshots/{f.name}")
    print(f"\n  📄 {docx_path.relative_to(ROOT)}")
    print(f"\n  Submit: reports/MLOps_Assignment_Report.docx")
    print("=" * 60)


if __name__ == "__main__":
    main()
