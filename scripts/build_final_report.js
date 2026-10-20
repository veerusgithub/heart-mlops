#!/usr/bin/env node
/**
 * Build the final, comprehensive MLOps Assignment 01 submission report.
 * ~10 pages, aligned to every rubric item, with all screenshots embedded.
 *
 * Run:  node scripts/build_final_report.js
 * Out:  reports/MLOps_Assignment_01_Final_Report.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, HeadingLevel,
  AlignmentType, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, PageBreak, TabStopPosition, TabStopType,
  ExternalHyperlink, Header, Footer, PageNumber, NumberFormat,
  convertInchesToTwip,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const SS = path.join(ROOT, "screenshots");
const FIG = path.join(ROOT, "reports", "figures");

// ── Load real metrics ──
const metrics = JSON.parse(fs.readFileSync(path.join(ROOT, "reports", "metrics.json"), "utf8"));
const edaSummary = JSON.parse(fs.readFileSync(path.join(ROOT, "reports", "eda_summary.json"), "utf8"));
const metadata = JSON.parse(fs.readFileSync(path.join(ROOT, "model_artifacts", "metadata.json"), "utf8"));

const lr = metrics.logistic_regression;
const rf = metrics.random_forest;

// ── Helpers ──
const BLUE = "1a56db";
const DARK = "1a1a2e";
const GRAY = "555555";
const TW = convertInchesToTwip;

function heading(text, level = HeadingLevel.HEADING_1) {
  return new Paragraph({ heading: level, spacing: { before: 300, after: 120 }, children: [
    new TextRun({ text, bold: true, font: "Calibri", color: level === HeadingLevel.HEADING_1 ? BLUE : DARK }),
  ]});
}

function para(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120, line: 276 }, ...opts, children: [
    new TextRun({ text, font: "Calibri", size: 22, color: opts.color || "333333", ...opts }),
  ]});
}

function boldPara(label, text) {
  return new Paragraph({ spacing: { after: 100, line: 276 }, children: [
    new TextRun({ text: label, bold: true, font: "Calibri", size: 22 }),
    new TextRun({ text, font: "Calibri", size: 22, color: "333333" }),
  ]});
}

function codePara(text) {
  return new Paragraph({ spacing: { after: 80 }, children: [
    new TextRun({ text, font: "Consolas", size: 18, color: "2d2d2d" }),
  ]});
}

function img(filename, w = 5.5) {
  const fpath = fs.existsSync(path.join(SS, filename)) ? path.join(SS, filename) :
                fs.existsSync(path.join(FIG, filename)) ? path.join(FIG, filename) : null;
  if (!fpath) return new Paragraph({ children: [new TextRun({ text: `[Image not found: ${filename}]`, italics: true })] });
  const data = fs.readFileSync(fpath);
  const ext = path.extname(filename).slice(1) || "png";
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: [
    new ImageRun({ data, transformation: { width: TW(w) / 15, height: TW(w * 0.6) / 15 }, type: ext }),
  ]});
}

function caption(text) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [
    new TextRun({ text, italics: true, font: "Calibri", size: 18, color: GRAY }),
  ]});
}

function metricCell(text, opts = {}) {
  return new TableCell({
    width: { size: opts.w || 1300, type: WidthType.DXA },
    shading: opts.header ? { type: ShadingType.CLEAR, color: "auto", fill: "2c5ea8" } :
             opts.highlight ? { type: ShadingType.CLEAR, color: "auto", fill: "e8f5e9" } :
             { type: ShadingType.CLEAR, color: "auto", fill: opts.alt ? "f5f7fa" : "ffffff" },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, font: "Calibri", size: 18, bold: opts.header || opts.highlight,
        color: opts.header ? "ffffff" : "333333" }),
    ]})],
  });
}

// ── Build document ──
async function build() {
  const sections = [];

  // ======== TITLE PAGE ========
  sections.push({
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: TW(1), bottom: TW(1), left: TW(1.2), right: TW(1.2) } } },
    children: [
      ...Array(5).fill(new Paragraph({ spacing: { after: 0 }, children: [] })),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [
        new TextRun({ text: "Heart Disease Risk Prediction", font: "Calibri", size: 52, bold: true, color: BLUE }),
      ]}),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [
        new TextRun({ text: "End-to-End MLOps Pipeline", font: "Calibri", size: 36, color: "4C78A8" }),
      ]}),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [
        new TextRun({ text: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", font: "Calibri", size: 22, color: "cccccc" }),
      ]}),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [
        new TextRun({ text: "Machine Learning Operations (AIMLCZG523)", font: "Calibri", size: 26, color: GRAY }),
        new TextRun({ text: "\nAssignment 01 — 50 Marks", font: "Calibri", size: 26, color: GRAY, break: 1 }),
      ]}),
      ...Array(2).fill(new Paragraph({ spacing: { after: 0 }, children: [] })),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [
        new TextRun({ text: "Submitted by", font: "Calibri", size: 22, color: GRAY }),
      ]}),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [
        new TextRun({ text: "Pentela Veeranjineyulu", font: "Calibri", size: 30, bold: true, color: DARK }),
      ]}),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [
        new TextRun({ text: "BITS Pilani — Work Integrated Learning Programme", font: "Calibri", size: 22, color: GRAY }),
        new TextRun({ text: "\nM.Tech in Artificial Intelligence & Machine Learning", font: "Calibri", size: 22, color: GRAY, break: 1 }),
      ]}),
      ...Array(2).fill(new Paragraph({ spacing: { after: 0 }, children: [] })),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [
        new TextRun({ text: "October 2026", font: "Calibri", size: 24, color: GRAY }),
      ]}),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 }, children: [
        new TextRun({ text: "Repository: ", font: "Calibri", size: 22, color: GRAY }),
        new TextRun({ text: "https://github.com/veerusgithub/heart-mlops", font: "Calibri", size: 22, color: BLUE, underline: {} }),
      ]}),
    ],
  });

  // ======== CONTENT PAGES ========
  const content = [];

  // ──────────────────────────────────────────────
  // TABLE OF CONTENTS (manual)
  // ──────────────────────────────────────────────
  content.push(heading("Table of Contents"));
  const tocItems = [
    "1. Introduction & Problem Statement",
    "2. Data Acquisition & Exploratory Data Analysis [5 marks]",
    "3. Feature Engineering & Model Development [8 marks]",
    "4. Experiment Tracking with MLflow [5 marks]",
    "5. Model Packaging & Reproducibility [7 marks]",
    "6. CI/CD Pipeline & Automated Testing [8 marks]",
    "7. Model Containerization with Docker [5 marks]",
    "8. Production Deployment on Kubernetes [7 marks]",
    "9. Monitoring & Logging [3 marks]",
    "10. Architecture Overview",
    "11. Setup & Installation Instructions",
    "12. Conclusion",
  ];
  for (const item of tocItems) {
    content.push(para(item, { color: BLUE }));
  }
  content.push(new Paragraph({ children: [new PageBreak()] }));

  // ──────────────────────────────────────────────
  // 1. INTRODUCTION
  // ──────────────────────────────────────────────
  content.push(heading("1. Introduction & Problem Statement"));
  content.push(para(
    "Cardiovascular diseases (CVDs) are the leading cause of death globally, accounting for an estimated 17.9 million lives each year according to the World Health Organization. Early detection and accurate risk assessment can significantly improve patient outcomes by enabling timely interventions. This project addresses this critical healthcare challenge by building a machine learning classifier that predicts heart disease risk from routine clinical measurements, and deploying it as a production-ready, monitored REST API."
  ));
  content.push(para(
    "The assignment implements a complete MLOps lifecycle — from raw data acquisition through exploratory analysis, leak-free preprocessing, experiment tracking, automated testing, CI/CD, Docker containerization, Kubernetes orchestration, and Prometheus + Grafana monitoring. Every component is wired together so the entire pipeline runs reproducibly from a clean checkout using a single requirements.txt file."
  ));
  content.push(boldPara("Problem Statement: ", "Given 13 clinical features from the UCI Heart Disease dataset (Cleveland Clinic, 303 patients), build a binary classifier to predict the presence or absence of heart disease, package it as a FastAPI microservice, and deploy it on Kubernetes with full observability."));
  content.push(boldPara("Key Design Principles: ", ""));
  content.push(para("(a) Reproducibility — fixed random seeds (42), pinned dependency ranges, and a data download script that reads a bundled copy of the original UCI file."));
  content.push(para("(b) Train/Serve Parity — preprocessing and the model live in a single scikit-learn Pipeline object, guaranteeing that an API request is transformed exactly like a training row, eliminating skew."));
  content.push(para("(c) Production-Readiness — non-root Docker container, liveness/readiness probes, input validation with Pydantic Literal types enforcing UCI codes, and a CI pipeline that fails on any code or test error."));

  // ──────────────────────────────────────────────
  // 2. DATA ACQUISITION & EDA [5 marks]
  // ──────────────────────────────────────────────
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(heading("2. Data Acquisition & Exploratory Data Analysis [5 marks]"));

  content.push(heading("2.1 Data Acquisition", HeadingLevel.HEADING_2));
  content.push(para(
    "The dataset is the UCI Heart Disease dataset, Cleveland Clinic subset (processed.cleveland.data), obtained from the UCI Machine Learning Repository. A reproducible download script (src/download_data.py) fetches the file, assigns proper column headers, and saves it as data/heart_raw.csv. The bundled copy of the original UCI file (heart+disease/processed.cleveland.data) ensures offline reproducibility."
  ));
  content.push(boldPara("Dataset Characteristics:", ""));
  content.push(para(`  • Rows: ${edaSummary.n_rows} patients (Cleveland Clinic cohort)`));
  content.push(para(`  • Features: ${edaSummary.n_features} clinical attributes (age, sex, chest pain type, blood pressure, cholesterol, blood sugar, ECG, heart rate, exercise angina, ST depression, ST slope, fluoroscopy vessels, thalassemia)`));
  content.push(para(`  • Target: Binary — num > 0 encoded as target = 1 (disease present). Original num ranges 0–4 representing different diagnoses.`));
  content.push(para(`  • Missing values: ${edaSummary.missing_values_total} total (ca: ${edaSummary.missing_by_column.ca} rows, thal: ${edaSummary.missing_by_column.thal} rows) — marked as '?' in the raw file, handled by median/mode imputation inside the pipeline.`));
  content.push(para("  • Raw UCI encodings preserved: cp 1–4 (not 0–3), slope 1–3, thal 3/6/7 (normal, fixed defect, reversible defect), ca 0–3, restecg 0–2."));

  content.push(heading("2.2 Data Cleaning", HeadingLevel.HEADING_2));
  content.push(para(
    "Cleaning is intentionally minimal and deterministic — operations that are safe to do before the train/test split (no information leakage). The basic_clean() function in src/preprocessing.py: (1) drops exact duplicate rows, (2) coerces all '?' entries to NaN using pd.to_numeric(errors='coerce'), and (3) casts the target to integer. All value-based imputation (median for numeric, most-frequent for categorical) is deferred to the sklearn ColumnTransformer so it is fit only on the training fold during cross-validation."
  ));

  content.push(heading("2.3 Exploratory Data Analysis", HeadingLevel.HEADING_2));
  content.push(para(
    `The EDA script (src/eda.py) generates four professional visualizations from the cleaned dataset. The class distribution shows ${edaSummary.class_balance.no_disease} healthy vs ${edaSummary.class_balance.disease} disease patients (${(edaSummary.class_balance.disease_ratio * 100).toFixed(1)}% positive rate), indicating a reasonably balanced dataset that does not require aggressive oversampling. Class weights are set to 'balanced' in both classifiers as a safeguard.`
  ));
  content.push(img("01_eda_class_balance.png", 4.5));
  content.push(caption("Figure 1: Class Balance — 164 healthy (54.1%) vs 139 disease (45.9%)"));

  content.push(para(
    "Feature distributions reveal clinically meaningful patterns. Age ranges from 29 to 77 with a concentration around 55–60, matching the known epidemiology of heart disease. Resting blood pressure (trestbps) clusters around 120–140 mm Hg with a right tail. Serum cholesterol (chol) centers near 250 mg/dl with notable outliers above 400. Maximum heart rate (thalach) shows a bimodal distribution that correlates inversely with disease presence."
  ));
  content.push(img("02_eda_histograms.png", 5.5));
  content.push(caption("Figure 2: Feature Distributions — Histograms of all 13 clinical features"));

  content.push(para(
    `The correlation heatmap identifies the features most strongly associated with the target. The top correlations are: thal (r = ${edaSummary.top_target_correlations.thal}), ca (r = ${edaSummary.top_target_correlations.ca}), exang (r = ${edaSummary.top_target_correlations.exang}), oldpeak (r = ${edaSummary.top_target_correlations.oldpeak}), and thalach (r = ${edaSummary.top_target_correlations.thalach}). Multi-collinearity is low — no pair of features exceeds |r| = 0.5 except thal and ca, which are clinically related. This supports using all 13 features without VIF-based elimination.`
  ));
  content.push(img("03_eda_correlation.png", 5));
  content.push(caption("Figure 3: Correlation Heatmap — Inter-feature correlations and target associations"));

  content.push(img("04_eda_features_by_target.png", 5.5));
  content.push(caption("Figure 4: Feature Distributions by Target — Clear separation visible in thalach, oldpeak, ca, and thal"));

  // ──────────────────────────────────────────────
  // 3. FEATURE ENGINEERING & MODEL DEVELOPMENT [8 marks]
  // ──────────────────────────────────────────────
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(heading("3. Feature Engineering & Model Development [8 marks]"));

  content.push(heading("3.1 Preprocessing Pipeline", HeadingLevel.HEADING_2));
  content.push(para(
    "Feature engineering uses a scikit-learn ColumnTransformer fitted inside each cross-validation fold, preventing any data leakage. The pipeline is defined once in src/preprocessing.py and reused in training and serving:"
  ));
  content.push(para("Numeric features (age, trestbps, chol, thalach, oldpeak, ca):"));
  content.push(para("  • Step 1: SimpleImputer(strategy='median') — fills the 4 missing ca values with the training fold median"));
  content.push(para("  • Step 2: StandardScaler() — zero-mean, unit-variance scaling for stable gradient descent in Logistic Regression"));
  content.push(para("Categorical features (sex, cp, fbs, restecg, exang, slope, thal):"));
  content.push(para("  • Step 1: SimpleImputer(strategy='most_frequent') — fills the 2 missing thal values with the mode"));
  content.push(para("  • Step 2: OneHotEncoder(handle_unknown='ignore', sparse_output=False) — creates 19 binary columns from the 7 categorical features"));
  content.push(para("Total post-transformation feature count: 6 (numeric, scaled) + 19 (one-hot) = 25 input dimensions to the classifier."));

  content.push(heading("3.2 Model Training & Hyperparameter Tuning", HeadingLevel.HEADING_2));
  content.push(para(
    "Two classifiers are trained inside a Pipeline([('pre', ColumnTransformer), ('clf', classifier)]), ensuring the full preprocessing-to-prediction chain is a single serialisable object. Each is tuned with GridSearchCV using 5-fold stratified cross-validation and ROC-AUC as the scoring metric."
  ));

  content.push(boldPara("Logistic Regression: ", `Linear baseline chosen for interpretability. Hyperparameter search over C ∈ {0.01, 0.1, 1.0, 10.0} and solver ∈ {lbfgs, liblinear}, with max_iter=1000 and class_weight='balanced'. Best configuration: C = ${lr.best_params["clf__C"]}, solver = ${lr.best_params["clf__solver"]}.`));

  content.push(boldPara("Random Forest: ", `Non-linear ensemble that captures feature interactions. Search over n_estimators ∈ {200, 400}, max_depth ∈ {None, 5, 10}, min_samples_leaf ∈ {1, 2, 4}, max_features ∈ {sqrt, log2}, with class_weight='balanced' and random_state=42. Best: n_estimators = ${rf.best_params["clf__n_estimators"]}, max_depth = ${rf.best_params["clf__max_depth"]}, min_samples_leaf = ${rf.best_params["clf__min_samples_leaf"]}, max_features = ${rf.best_params["clf__max_features"]}.`));

  content.push(heading("3.3 Model Selection & Evaluation", HeadingLevel.HEADING_2));
  content.push(para(
    "Model selection is based solely on cross-validated ROC-AUC on the training set (242 rows). The 20% hold-out set (61 rows) is reserved as an unbiased final estimate and never used for selection, preventing optimistic bias."
  ));

  // Results table
  const colW = [1700, 1200, 1400, 1200, 1200, 1100, 1100];
  const tableW = colW.reduce((a, b) => a + b, 0);
  const headers = ["Model", "CV ROC-AUC", "Holdout ROC-AUC", "Accuracy", "Precision", "Recall", "F1"];
  const lrRow = ["Logistic Reg.", lr.cv.cv_roc_auc_mean.toFixed(4), lr.holdout.roc_auc.toFixed(4),
    lr.holdout.accuracy.toFixed(4), lr.holdout.precision.toFixed(4), lr.holdout.recall.toFixed(4), lr.holdout.f1.toFixed(4)];
  const rfRow = ["Random Forest", rf.cv.cv_roc_auc_mean.toFixed(4), rf.holdout.roc_auc.toFixed(4),
    rf.holdout.accuracy.toFixed(4), rf.holdout.precision.toFixed(4), rf.holdout.recall.toFixed(4), rf.holdout.f1.toFixed(4)];

  content.push(new Table({
    width: { size: tableW, type: WidthType.DXA },
    columnWidths: colW,
    rows: [
      new TableRow({ children: headers.map((h, i) => metricCell(h, { header: true, w: colW[i] })) }),
      new TableRow({ children: lrRow.map((v, i) => metricCell(v, { highlight: i === 0, w: colW[i] })) }),
      new TableRow({ children: rfRow.map((v, i) => metricCell(v, { alt: true, w: colW[i] })) }),
    ],
  }));
  content.push(caption("Table 1: Model Performance Comparison — Logistic Regression selected (higher CV ROC-AUC)"));

  content.push(para(
    `Logistic Regression wins with CV ROC-AUC = ${lr.cv.cv_roc_auc_mean.toFixed(4)} ± ${lr.cv.cv_roc_auc_std.toFixed(4)}, versus Random Forest's ${rf.cv.cv_roc_auc_mean.toFixed(4)} ± ${rf.cv.cv_roc_auc_std.toFixed(4)}. On the hold-out set, LR achieves ROC-AUC = ${lr.holdout.roc_auc.toFixed(4)} with recall = ${lr.holdout.recall.toFixed(4)} — clinically important since missing a true positive (heart disease patient classified as healthy) has graver consequences than a false positive.`
  ));

  content.push(img("roc_logistic_regression.png", 4));
  content.push(caption(`Figure 5: ROC Curve — Logistic Regression (Hold-out AUC = ${lr.holdout.roc_auc.toFixed(3)})`));
  content.push(img("confusion_logistic_regression.png", 3.8));
  content.push(caption("Figure 6: Confusion Matrix — Logistic Regression on hold-out set (61 patients)"));
  content.push(img("importance_logistic_regression.png", 4.5));
  content.push(caption("Figure 7: Feature Importances (|coefficient|) — Top drivers of the prediction"));

  // ──────────────────────────────────────────────
  // 4. EXPERIMENT TRACKING [5 marks]
  // ──────────────────────────────────────────────
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(heading("4. Experiment Tracking with MLflow [5 marks]"));
  content.push(para(
    "MLflow is integrated for comprehensive experiment tracking with a local SQLite backend (mlflow.db), keeping all experiment data self-contained and version-controllable. The experiment name is 'heart-disease-classification'."
  ));
  content.push(boldPara("What is logged per run:", ""));
  content.push(para("  • Parameters: model name, CV folds (5), test size (0.2), random seed (42), and all best hyperparameters from GridSearchCV"));
  content.push(para("  • Metrics: 10 CV metrics (accuracy, precision, recall, F1, ROC-AUC — each with mean and std), 5 hold-out metrics, and the GridSearchCV best score"));
  content.push(para("  • Artifacts: ROC curve plot, confusion matrix plot, feature importance plot (per model), and the full fitted sklearn Pipeline serialised with cloudpickle"));
  content.push(para("  • Model: registered via mlflow.sklearn.log_model() for reproducible loading"));
  content.push(para(
    "The tracking URI is set to sqlite:///mlflow.db so all runs persist in the repository. Each run creates a timestamped entry under mlruns/ with the serialised model, environment spec (conda.yaml, requirements.txt), and all plot artifacts accessible via the MLflow UI (mlflow ui --backend-store-uri sqlite:///mlflow.db)."
  ));
  content.push(img("05_mlflow_tracking.png", 5.5));
  content.push(caption("Figure 8: MLflow Experiment Tracking — Model comparison and logged parameters"));

  // ──────────────────────────────────────────────
  // 5. MODEL PACKAGING [7 marks]
  // ──────────────────────────────────────────────
  content.push(heading("5. Model Packaging & Reproducibility [7 marks]"));
  content.push(para(
    "The winning model is saved as model_artifacts/model.joblib — a single fitted sklearn Pipeline containing the full ColumnTransformer + LogisticRegression. This design is critical for reproducibility: anyone loading this file gets the exact same preprocessing that was used during training, with no separate transformer objects to lose or version-mismatch."
  ));
  content.push(boldPara("Artifacts produced:", ""));
  content.push(para("  • model_artifacts/model.joblib — the fitted Pipeline (preprocessor + classifier)"));
  content.push(para("  • model_artifacts/feature_schema.json — lists numeric vs categorical features and input order, so the serving code knows which columns to pass"));
  content.push(para(`  • model_artifacts/metadata.json — records best_model (${metadata.best_model}), best_params, selection_metric, sklearn_version (${metadata.sklearn_version}), python_version (${metadata.python_version}), seed (${metadata.seed}), and trained_on_rows (${metadata.trained_on_rows})`));
  content.push(para("  • requirements.txt — 30 pinned dependency ranges covering pandas, numpy, scikit-learn, mlflow, fastapi, uvicorn, prometheus-client, pytest, and more"));
  content.push(para("  • requirements-serve.txt — minimal subset for the Docker image (no training deps), reducing image size"));
  content.push(para(
    "Full reproducibility: from a clean checkout, running 'pip install -r requirements.txt && python src/download_data.py && python src/train.py' recreates the model with identical results (seed=42 throughout). The pipeline runs end-to-end in GitHub Actions CI to prove this."
  ));

  // ──────────────────────────────────────────────
  // 6. CI/CD [8 marks]
  // ──────────────────────────────────────────────
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(heading("6. CI/CD Pipeline & Automated Testing [8 marks]"));

  content.push(heading("6.1 GitHub Actions Workflow", HeadingLevel.HEADING_2));
  content.push(para(
    "The CI/CD pipeline (.github/workflows/mlops-pipeline.yml, 212 lines) runs on every push to main and consists of 5 sequential jobs, each dependent on the previous one. If any job fails, the entire pipeline stops with clear error logs."
  ));
  content.push(boldPara("Job 1 — Lint: ", "Runs flake8 with two passes. First pass checks for syntax errors and undefined names (E9, F63, F7, F82) and fails the build on violations. Second pass checks style with max-line-length=100 but exits zero (non-blocking warnings)."));
  content.push(boldPara("Job 2 — Test: ", "Installs dependencies, downloads the dataset, trains the model (required for API tests), and runs the full pytest suite. Uploads test results as JUnit XML and model artifacts."));
  content.push(boldPara("Job 3 — Train: ", "Full training pipeline: download data → EDA visualisations → GridSearchCV + MLflow tracking. Uploads model_artifacts/, reports/, and mlflow.db as workflow artifacts for traceability."));
  content.push(boldPara("Job 4 — Docker Build: ", "Builds the multi-stage Docker image, starts the container, and runs smoke tests: health check, valid prediction (thal=3), and validation test (thal=2 must return HTTP 422)."));
  content.push(boldPara("Job 5 — K8s Deploy: ", "Creates a kind (Kubernetes-in-Docker) cluster, loads the image, applies deployment/service/HPA manifests, waits for rollout, port-forwards, and tests /health, /predict, /predict/batch, and input validation end-to-end."));
  content.push(img("06_ci_pipeline.png", 5.5));
  content.push(caption("Figure 9: GitHub Actions CI/CD Pipeline — All 5 jobs passed successfully"));

  content.push(heading("6.2 Automated Test Suite (29 Tests)", HeadingLevel.HEADING_2));
  content.push(para("The test suite (tests/) contains 29 pytest tests across three modules:"));
  content.push(boldPara("test_data.py (4 tests): ", "Validates the raw UCI dataset — column order matches documentation, shape is 303×14, missing markers are '?', binarised target matches published class counts (164/139), and raw code ranges (cp 1–4, slope 1–3, thal ∈ {3,6,7}, ca 0–3)."));
  content.push(boldPara("test_preprocessing.py (7 tests): ", "Verifies basic_clean drops duplicates, coerces '?' to NaN, feature partition (numeric + categorical = all 13, no overlap), split_X_y shapes, imputer handles missing values, output is fully numeric and scaled, and OHE expands categoricals to 25 dimensions."));
  content.push(boldPara("test_api.py (18 tests): ", "Integration tests using FastAPI TestClient: root endpoint, health check, /metrics exposes Prometheus counters, /predict response schema, known low-risk vs high-risk classification, batch prediction, out-of-range rejection (age=999→422), missing field rejection, parametrised invalid UCI code tests (cp=0, cp=5, slope=0, ca=4, thal=2, thal=5 all→422), valid thal codes 3/6/7 accepted, and sample JSON files produce valid requests."));
  content.push(img("07_pytest_results.png", 5.5));
  content.push(caption("Figure 10: Pytest Results — All 29/29 tests passed in 7.92 seconds"));

  // ──────────────────────────────────────────────
  // 7. DOCKER [5 marks]
  // ──────────────────────────────────────────────
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(heading("7. Model Containerization with Docker [5 marks]"));
  content.push(para(
    "The Dockerfile implements a multi-stage build optimised for production deployment:"
  ));
  content.push(boldPara("Stage 1 — Builder: ", "Uses python:3.11-slim as base, creates a virtual environment at /opt/venv, and installs only the serving dependencies from requirements-serve.txt (not the full training stack). This separation keeps the runtime image lean."));
  content.push(boldPara("Stage 2 — Runtime: ", "Fresh python:3.11-slim image, copies only the prepared venv from the builder stage. Application code (app.py), source modules (src/), and trained model artifacts (model_artifacts/) are copied in. A non-root user 'appuser' (uid 10001) is created for security."));
  content.push(boldPara("Security & Health:", ""));
  content.push(para("  • Non-root execution: USER appuser (uid 10001) — principle of least privilege"));
  content.push(para("  • HEALTHCHECK: pings /health every 30s with 10s startup grace, 3 retries before marking unhealthy"));
  content.push(para("  • EXPOSE 8000: documents the serving port"));
  content.push(para("  • PYTHONPATH=/app:/app/src: ensures imports resolve correctly for the pickled Pipeline"));
  content.push(boldPara("Endpoints exposed:", ""));
  content.push(para("  • POST /predict — single patient JSON → {prediction, label, confidence, probability_disease, model_name}"));
  content.push(para("  • POST /predict/batch — {records: [...]} → {count, predictions: [...]}"));
  content.push(para("  • GET /health — liveness/readiness probe returning model status"));
  content.push(para("  • GET /metrics — Prometheus text exposition format (counters + histograms)"));
  content.push(para("  • GET /docs — Swagger UI for interactive testing"));
  content.push(para(
    "Input validation uses Pydantic v2 with strict type constraints: age ∈ [0, 120], thal ∈ Literal[3, 6, 7] (enforcing valid UCI codes — thal=2 is correctly rejected with HTTP 422), cp ∈ [1, 4], slope ∈ [1, 3], ca ∈ [0, 3]. This prevents malformed inputs from reaching the model."
  ));
  content.push(img("08_docker_build.png", 5.5));
  content.push(caption("Figure 11: Docker Build & Smoke Test — Multi-stage build, health check, and prediction"));
  content.push(img("09_api_endpoints.png", 5.5));
  content.push(caption("Figure 12: FastAPI Endpoints — /predict, /predict/batch, /health, and input validation (thal=2 → 422)"));

  // ──────────────────────────────────────────────
  // 8. KUBERNETES [7 marks]
  // ──────────────────────────────────────────────
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(heading("8. Production Deployment on Kubernetes [7 marks]"));
  content.push(para(
    "The application is deployed on Kubernetes using declarative manifests in deployment/. In CI, a kind (Kubernetes-in-Docker) cluster proves the deployment end-to-end; the same manifests work on GKE, EKS, AKS, or any conformant cluster."
  ));
  content.push(boldPara("deployment.yaml — Deployment:", ""));
  content.push(para("  • 2 replicas for high availability"));
  content.push(para("  • Resource requests: 100m CPU, 256Mi memory; limits: 500m CPU, 512Mi memory"));
  content.push(para("  • Liveness probe: GET /health every 15s (initial delay 10s) — restarts unresponsive pods"));
  content.push(para("  • Readiness probe: GET /health every 10s (initial delay 5s) — removes unhealthy pods from Service"));
  content.push(para("  • Prometheus annotations: scrape=true, port=8000, path=/metrics — auto-discovered by Prometheus"));
  content.push(boldPara("service.yaml — Service:", ""));
  content.push(para("  • Type: LoadBalancer (cloud) — maps external port 80 → container port 8000"));
  content.push(para("  • On local clusters (kind/minikube): port-forward or NodePort access"));
  content.push(boldPara("hpa.yaml — Horizontal Pod Autoscaler:", ""));
  content.push(para("  • API version: autoscaling/v2"));
  content.push(para("  • Min replicas: 2, Max replicas: 5"));
  content.push(para("  • Scale-up trigger: average CPU utilisation exceeds 70%"));
  content.push(boldPara("ingress.yaml — Ingress:", ""));
  content.push(para("  • nginx Ingress controller with host-based routing (heart-api.local)"));
  content.push(para("  • Rewrite-target annotation for clean URL routing"));

  content.push(heading("8.2 Helm Chart", HeadingLevel.HEADING_2));
  content.push(para(
    "In addition to raw manifests, a Helm chart is provided at deployment/helm/heart-api/ for templated, configurable deployments. The chart packages all four Kubernetes resources (Deployment, Service, HPA, Ingress) with a single values.yaml that parameterises image, replicas, resources, autoscaling thresholds, probe paths, and Prometheus annotations."
  ));
  content.push(boldPara("Chart structure:", ""));
  content.push(codePara("deployment/helm/heart-api/"));
  content.push(codePara("├── Chart.yaml              # Chart metadata (v1.0.0)"));
  content.push(codePara("├── values.yaml             # Default configuration values"));
  content.push(codePara("└── templates/"));
  content.push(codePara("    ├── _helpers.tpl        # Common label definitions"));
  content.push(codePara("    ├── deployment.yaml     # Templated Deployment"));
  content.push(codePara("    ├── service.yaml        # Templated Service"));
  content.push(codePara("    ├── hpa.yaml            # Conditional HPA (autoscaling.enabled)"));
  content.push(codePara("    └── ingress.yaml        # Conditional Ingress (ingress.enabled)"));
  content.push(boldPara("Key values.yaml defaults: ", "replicaCount=2, service.type=LoadBalancer, autoscaling min=2 max=5 at 70% CPU, ingress host=heart-api.local, Prometheus scrape enabled."));
  content.push(boldPara("Deploy with Helm:", ""));
  content.push(codePara("helm install heart-api deployment/helm/heart-api/"));
  content.push(codePara("helm install heart-api deployment/helm/heart-api/ --set image.tag=v2.0"));
  content.push(para(
    "The Helm chart provides the same deployment as the raw manifests but adds configurability — teams can override any value at install time without editing YAML files, making it suitable for multi-environment deployments (dev, staging, production)."
  ));

  content.push(heading("8.3 CI Validation", HeadingLevel.HEADING_2));
  content.push(para(
    "The CI pipeline (Job 5) validates the full deployment: kind cluster creation → image loading → kubectl apply → rollout status → port-forward → health check → prediction → batch prediction → input validation (thal=2 → 422). Pod logs are collected as artifacts for debugging."
  ));
  content.push(img("10_kubernetes.png", 5.5));
  content.push(caption("Figure 13: Kubernetes Deployment — 2 pods running, Service exposed, API verified via port-forward"));

  // ──────────────────────────────────────────────
  // 9. MONITORING [3 marks]
  // ──────────────────────────────────────────────
  content.push(heading("9. Monitoring & Logging [3 marks]"));
  content.push(heading("9.1 API Request Logging", HeadingLevel.HEADING_2));
  content.push(para(
    "Every prediction request is logged as structured JSON to stdout (container-friendly), including: event type, full input features, prediction, probability_disease, and latency_ms. This integrates with any log aggregation system (ELK, Loki, CloudWatch). Batch requests log the count and total latency."
  ));
  content.push(heading("9.2 Prometheus Metrics", HeadingLevel.HEADING_2));
  content.push(para(
    "The /metrics endpoint exposes three prometheus_client instruments:"
  ));
  content.push(para("  • heart_predictions_total (Counter, label: outcome) — counts predictions by class ('Heart disease' vs 'No heart disease'), enabling class distribution monitoring and drift detection"));
  content.push(para("  • heart_requests_total (Counter, labels: endpoint, status) — counts HTTP requests per endpoint and status code, tracking error rates"));
  content.push(para("  • heart_predict_latency_seconds (Histogram) — prediction latency distribution, for SLA monitoring"));

  content.push(heading("9.3 Prometheus + Grafana Stack", HeadingLevel.HEADING_2));
  content.push(para(
    "A docker-compose.monitoring.yml file launches the full monitoring stack: the API, Prometheus (scraping every 15s), and Grafana (admin/admin). A pre-provisioned Grafana dashboard (monitoring/grafana/dashboards/heart_api_dashboard.json) displays: request rate, prediction latency percentiles (p50/p95/p99), error rate, and prediction class distribution. Datasource and dashboard provisioning are fully automated via YAML configuration."
  ));
  content.push(codePara("docker compose -f monitoring/docker-compose.monitoring.yml up --build"));
  content.push(para("  • API: http://localhost:8000/docs  •  Prometheus: http://localhost:9090  •  Grafana: http://localhost:3000"));
  content.push(img("11_monitoring.png", 5.5));
  content.push(caption("Figure 14: Prometheus + Grafana Monitoring Stack — Targets active, metrics flowing"));

  // ──────────────────────────────────────────────
  // 10. ARCHITECTURE
  // ──────────────────────────────────────────────
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(heading("10. Architecture Overview"));
  content.push(para(
    "The end-to-end pipeline architecture connects six stages: (1) Data acquisition and EDA scripts produce the cleaned dataset and visualisations. (2) The training pipeline runs GridSearchCV inside a sklearn Pipeline, logs to MLflow, and persists the winning model. (3) The FastAPI app loads the fitted Pipeline and serves predictions with Prometheus metrics. (4) Docker packages the app into a slim, non-root container. (5) Kubernetes orchestrates replicas, load balancing, and auto-scaling. (6) Prometheus + Grafana provide real-time monitoring and alerting. GitHub Actions CI/CD ties all stages together, running on every push to main."
  ));
  if (fs.existsSync(path.join(FIG, "architecture.png"))) {
    content.push(img("architecture.png", 5.5));
    content.push(caption("Figure 15: End-to-End MLOps Pipeline Architecture"));
  }

  // ──────────────────────────────────────────────
  // 11. SETUP INSTRUCTIONS
  // ──────────────────────────────────────────────
  content.push(heading("11. Setup & Installation Instructions"));
  content.push(para("Prerequisites: Python 3.11+, Docker, kubectl, and (optionally) kind or minikube for local Kubernetes."));
  content.push(boldPara("Quick Start:", ""));
  content.push(codePara("git clone https://github.com/veerusgithub/heart-mlops.git"));
  content.push(codePara("cd heart-mlops"));
  content.push(codePara("pip install -r requirements.txt"));
  content.push(codePara("python src/download_data.py --out data/heart_raw.csv"));
  content.push(codePara("python src/eda.py --data data/heart_raw.csv --outdir reports/figures"));
  content.push(codePara("python src/train.py --data data/heart_raw.csv"));
  content.push(codePara("python -m pytest tests/ -v"));
  content.push(codePara("uvicorn app:app --host 0.0.0.0 --port 8000"));
  content.push(boldPara("Docker:", ""));
  content.push(codePara("docker build -t heart-api:latest ."));
  content.push(codePara("docker run -d --name heart-api -p 8000:8000 heart-api:latest"));
  content.push(codePara('curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \\'));
  content.push(codePara('  -d \'{"age":63,"sex":1,"cp":1,"trestbps":145,"chol":233,"fbs":1,"restecg":2,"thalach":150,"exang":0,"oldpeak":2.3,"slope":3,"ca":0,"thal":6}\''));
  content.push(boldPara("Kubernetes (raw manifests):", ""));
  content.push(codePara("kubectl apply -f deployment/deployment.yaml"));
  content.push(codePara("kubectl apply -f deployment/service.yaml"));
  content.push(codePara("kubectl apply -f deployment/hpa.yaml"));
  content.push(codePara("kubectl rollout status deployment/heart-api"));
  content.push(boldPara("Kubernetes (Helm chart):", ""));
  content.push(codePara("helm install heart-api deployment/helm/heart-api/"));
  content.push(boldPara("Monitoring:", ""));
  content.push(codePara("docker compose -f monitoring/docker-compose.monitoring.yml up --build"));

  // ──────────────────────────────────────────────
  // 12. REPOSITORY STRUCTURE
  // ──────────────────────────────────────────────
  content.push(heading("12. Repository Structure"));
  const tree = [
    "heart-mlops/",
    "├── .github/workflows/mlops-pipeline.yml   # 5-stage CI/CD pipeline",
    "├── app.py                                  # FastAPI serving application",
    "├── Dockerfile                              # Multi-stage production build",
    "├── Makefile                                # Common task shortcuts",
    "├── requirements.txt                        # Full development dependencies",
    "├── requirements-serve.txt                  # Minimal serving dependencies",
    "├── data/                                   # Raw and cleaned datasets",
    "├── deployment/                             # K8s manifests & Helm chart",
    "│   ├── deployment.yaml                     #   2-replica Deployment",
    "│   ├── service.yaml                        #   LoadBalancer Service",
    "│   ├── hpa.yaml                            #   HPA (2-5 pods, 70% CPU)",
    "│   ├── ingress.yaml                        #   nginx Ingress",
    "│   └── helm/heart-api/                     #   Helm chart",
    "│       ├── Chart.yaml                      #     Chart metadata",
    "│       ├── values.yaml                     #     Default values",
    "│       └── templates/                      #     Templated manifests",
    "├── model_artifacts/                        # Trained model + metadata",
    "│   ├── model.joblib                        #   Fitted sklearn Pipeline",
    "│   ├── feature_schema.json                 #   Feature definitions",
    "│   └── metadata.json                       #   Training metadata",
    "├── monitoring/                             # Observability stack",
    "│   ├── docker-compose.monitoring.yml       #   API + Prometheus + Grafana",
    "│   ├── prometheus.yml                      #   Scrape config",
    "│   └── grafana/                            #   Dashboard + provisioning",
    "├── notebooks/                              # EDA Jupyter notebook",
    "├── reports/                                # Generated reports & figures",
    "├── samples/                                # Example API request JSONs",
    "├── screenshots/                            # Assignment evidence",
    "├── src/                                    # Core source code",
    "│   ├── download_data.py                    #   UCI data acquisition",
    "│   ├── eda.py                              #   Exploratory data analysis",
    "│   ├── preprocessing.py                    #   Feature pipeline (shared)",
    "│   ├── train.py                            #   Model training + MLflow",
    "│   └── predict.py                          #   CLI prediction utility",
    "└── tests/                                  # 29 pytest tests",
    "    ├── test_data.py                        #   Dataset integrity (4)",
    "    ├── test_preprocessing.py               #   Pipeline correctness (7)",
    "    └── test_api.py                         #   API integration (18)",
  ];
  for (const line of tree) {
    content.push(new Paragraph({ spacing: { after: 20 }, children: [
      new TextRun({ text: line, font: "Consolas", size: 16, color: "2d2d2d" }),
    ]}));
  }

  // ──────────────────────────────────────────────
  // 13. CONCLUSION
  // ──────────────────────────────────────────────
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(heading("13. Conclusion"));
  content.push(para(
    "This project demonstrates a complete, production-grade MLOps pipeline from raw clinical data to a monitored Kubernetes-deployed prediction API. The key achievements across the nine assignment tasks are:"
  ));
  content.push(para(
    `(1) Data & EDA: Comprehensive analysis of 303 Cleveland Clinic patients with 4 professional visualisations revealing key predictive features (thal, ca, exang, oldpeak, thalach).`
  ));
  content.push(para(
    `(2) Modeling: Logistic Regression selected by 5-fold stratified CV ROC-AUC = ${lr.cv.cv_roc_auc_mean.toFixed(4)}, achieving hold-out ROC-AUC = ${lr.holdout.roc_auc.toFixed(4)} and recall = ${lr.holdout.recall.toFixed(4)} — critical for minimising missed diagnoses.`
  ));
  content.push(para(
    "(3) Experiment Tracking: MLflow logs every parameter, metric, plot, and serialised model with a SQLite backend for full auditability."
  ));
  content.push(para(
    "(4) Reproducibility: Single sklearn Pipeline (preprocessor + classifier), pinned requirements, fixed seeds, and a data download script ensure identical results from any clean checkout."
  ));
  content.push(para(
    "(5) CI/CD: 5-stage GitHub Actions pipeline (lint → test → train → docker → k8s) with 29 automated tests — the pipeline fails on any error and provides artifact uploads for every stage."
  ));
  content.push(para(
    "(6) Containerization: Multi-stage Docker build with non-root user, health check, Pydantic input validation (UCI code enforcement via Literal types), and Swagger UI."
  ));
  content.push(para(
    "(7) Kubernetes: 2-replica Deployment with HPA (2–5 pods at 70% CPU), LoadBalancer Service, nginx Ingress, liveness/readiness probes, and Prometheus scrape annotations."
  ));
  content.push(para(
    "(8) Monitoring: Prometheus + Grafana stack with custom counters (predictions by class, requests by endpoint) and latency histograms, pre-provisioned dashboards, and structured JSON logging."
  ));
  content.push(para(
    `(9) Documentation: This 10-page report with 15 figures, setup instructions, and architecture diagram. Repository: https://github.com/veerusgithub/heart-mlops`
  ));

  // ──────────────────────────────────────────────
  // ASSEMBLE
  // ──────────────────────────────────────────────
  sections.push({
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: TW(0.8), bottom: TW(0.8), left: TW(1), right: TW(1) } },
      pageNumberStart: 1, pageNumberFormatType: NumberFormat.DECIMAL },
    headers: { default: new Header({ children: [
      new Paragraph({ alignment: AlignmentType.RIGHT, children: [
        new TextRun({ text: "Heart Disease MLOps Pipeline — Assignment 01", font: "Calibri", size: 16, color: "999999" }),
      ] }),
    ] }) },
    footers: { default: new Footer({ children: [
      new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "Page ", font: "Calibri", size: 16, color: "999999" }),
        new TextRun({ children: [PageNumber.CURRENT], font: "Calibri", size: 16, color: "999999" }),
      ] }),
    ] }) },
    children: content,
  });

  const doc = new Document({ sections });
  const buf = await Packer.toBuffer(doc);
  const out = path.join(ROOT, "reports", "MLOps_Assignment_01_Final_Report.docx");
  fs.writeFileSync(out, buf);
  console.log(`\n✅ Report saved: ${out} (${(buf.length / 1024).toFixed(0)} KB)`);
}

build().catch(e => { console.error(e); process.exit(1); });
