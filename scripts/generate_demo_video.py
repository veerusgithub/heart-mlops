#!/usr/bin/env python3
"""Generate a pipeline demo video from screenshots and terminal outputs."""

import subprocess, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1920, 1080
BG = (15, 15, 25)
TEXT_COLOR = (220, 220, 220)
ACCENT = (0, 180, 255)
GREEN = (0, 200, 80)
TITLE_COLOR = (255, 255, 255)
CODE_BG = (30, 30, 45)
HEADER_BG = (25, 25, 40)

FRAMES_DIR = Path("video_frames")
FRAMES_DIR.mkdir(exist_ok=True)

def get_fonts():
    mono_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    regular_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    def find(paths, size):
        for p in paths:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    return {
        "mono": find(mono_paths, 20),
        "mono_lg": find(mono_paths, 24),
        "title": find(bold_paths, 52),
        "subtitle": find(regular_paths, 28),
        "heading": find(bold_paths, 36),
        "body": find(regular_paths, 22),
        "small": find(regular_paths, 18),
        "label": find(bold_paths, 20),
    }

FONTS = get_fonts()

def new_frame():
    return Image.new("RGB", (WIDTH, HEIGHT), BG)

def draw_header(d, title, subtitle=""):
    d.rectangle([0, 0, WIDTH, 80], fill=HEADER_BG)
    d.text((40, 18), "Heart Disease MLOps Pipeline", font=FONTS["heading"], fill=ACCENT)
    d.text((WIDTH - 400, 28), "Veeranjineyulu Pentela | BITS WILP", font=FONTS["small"], fill=(150, 150, 150))
    d.text((40, 100), title, font=FONTS["title"], fill=TITLE_COLOR)
    if subtitle:
        d.text((40, 160), subtitle, font=FONTS["subtitle"], fill=(180, 180, 180))

def draw_terminal(d, lines, x=40, y=220, w=1840, h=None):
    if h is None:
        h = min(len(lines) * 28 + 40, HEIGHT - y - 20)
    d.rounded_rectangle([x, y, x+w, y+h], radius=10, fill=CODE_BG)
    d.rounded_rectangle([x, y, x+w, y+30], radius=10, fill=(50, 50, 65))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([x+12+i*20, y+8, x+24+i*20, y+22], fill=c)
    ty = y + 40
    for line in lines:
        if ty > y + h - 20:
            break
        color = TEXT_COLOR
        if line.startswith("$"):
            color = GREEN
        elif line.startswith("#"):
            color = ACCENT
        elif any(k in line for k in ["PASSED", "passed", "succeeded"]):
            color = GREEN
        elif any(k in line for k in ["ERROR", "FAILED"]):
            color = (255, 80, 80)
        d.text((x + 20, ty), line[:120], font=FONTS["mono"], fill=color)
        ty += 28

def draw_code_block(d, title, lines, x=40, y=220, w=900, h=400):
    d.rounded_rectangle([x, y, x+w, y+h], radius=10, fill=CODE_BG)
    d.text((x+15, y+10), title, font=FONTS["label"], fill=ACCENT)
    ty = y + 40
    for line in lines:
        if ty > y + h - 15:
            break
        d.text((x+20, ty), line[:80], font=FONTS["mono"], fill=TEXT_COLOR)
        ty += 26

def draw_metric_box(d, label, value, x, y, w=250, h=100):
    d.rounded_rectangle([x, y, x+w, y+h], radius=8, fill=(35, 35, 55))
    d.rounded_rectangle([x, y, x+w, y+4], radius=2, fill=ACCENT)
    d.text((x+15, y+15), label, font=FONTS["small"], fill=(150, 150, 170))
    d.text((x+15, y+45), value, font=FONTS["heading"], fill=TITLE_COLOR)

def embed_screenshot(frame, path, x, y, max_w, max_h):
    try:
        img = Image.open(path)
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        frame.paste(img, (x, y))
        return True
    except Exception:
        return False

def save(frame, idx, duration_s=4):
    p = FRAMES_DIR / f"frame_{idx:03d}.png"
    frame.save(p)
    return (p, duration_s)

# ===== GENERATE FRAMES =====
frames = []
idx = 0
ss_dir = Path("screenshots")

# --- Frame 0: Title slide ---
f = new_frame(); d = ImageDraw.Draw(f)
d.rectangle([0, 0, WIDTH, HEIGHT], fill=(10, 10, 30))
d.text((WIDTH//2 - 450, 200), "Heart Disease Risk Prediction", font=FONTS["title"], fill=TITLE_COLOR)
d.text((WIDTH//2 - 380, 280), "End-to-End MLOps Pipeline Demo", font=FONTS["subtitle"], fill=ACCENT)
d.text((WIDTH//2 - 300, 400), "Veeranjineyulu Pentela", font=FONTS["heading"], fill=TEXT_COLOR)
d.text((WIDTH//2 - 340, 460), "BITS Pilani WILP | M.Tech AI & ML", font=FONTS["subtitle"], fill=(150,150,150))
d.text((WIDTH//2 - 280, 520), "MLOps (AIMLCZG523) - Assignment 01", font=FONTS["subtitle"], fill=(150,150,150))
pipeline = "Download > EDA > Preprocess > Train > MLflow > FastAPI > Docker > K8s > Monitor"
d.text((WIDTH//2 - 500, 650), pipeline, font=FONTS["body"], fill=GREEN)
d.text((WIDTH//2 - 200, 750), "GitHub: veerusgithub/heart-mlops", font=FONTS["body"], fill=ACCENT)
d.text((WIDTH//2 - 280, 800), "Deployed: heart-mlops.onrender.com", font=FONTS["body"], fill=ACCENT)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 1: Project Structure ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "1. Project Structure", "Repository layout and key files")
tree_lines = [
    "$ tree -L 2 heart-mlops/",
    "heart-mlops/",
    "|-- app.py                    # FastAPI serving application",
    "|-- Dockerfile                # Multi-stage Docker build",
    "|-- Makefile                  # Build automation",
    "|-- requirements.txt          # Dependencies",
    "|-- src/",
    "|   |-- download_data.py      # UCI dataset download",
    "|   |-- eda.py                # Exploratory Data Analysis",
    "|   |-- train.py              # Model training + GridSearchCV",
    "|   +-- preprocessing.py      # Feature pipeline",
    "|-- tests/                    # 29 pytest tests",
    "|-- model_artifacts/          # Trained model + metadata",
    "|-- deployment/",
    "|   |-- k8s/                  # Kubernetes manifests",
    "|   +-- helm/heart-api/       # Helm chart",
    "|-- monitoring/               # Prometheus + Grafana",
    "|-- .github/workflows/        # CI/CD pipeline",
    "|-- screenshots/              # Evidence screenshots",
    "+-- reports/                  # Final report + metrics",
]
draw_terminal(d, tree_lines, h=650)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 2: EDA ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "2. Data Acquisition & EDA", "UCI Heart Disease Dataset - 303 patients, 13 features")
draw_metric_box(d, "Total Samples", "303", 40, 200)
draw_metric_box(d, "Features", "13", 310, 200)
draw_metric_box(d, "Missing Values", "6", 580, 200)
draw_metric_box(d, "Class Balance", "164 / 139", 850, 200, w=300)
embed_screenshot(f, ss_dir / "01_eda_class_balance.png", 40, 330, 440, 350)
embed_screenshot(f, ss_dir / "03_eda_correlation.png", 500, 330, 440, 350)
embed_screenshot(f, ss_dir / "02_eda_histograms.png", 960, 330, 440, 350)
embed_screenshot(f, ss_dir / "04_eda_features_by_target.png", 500, 700, 440, 350)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 3: Preprocessing + Training ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "3. Feature Engineering & Training", "sklearn Pipeline + GridSearchCV (5-fold stratified CV)")
preprocess_lines = [
    "# Preprocessing Pipeline",
    "ColumnTransformer(",
    "  numeric:  SimpleImputer(median) -> StandardScaler",
    "  categorical: SimpleImputer(most_freq) -> OneHotEncoder",
    ") -> 25 features after one-hot encoding",
    "",
    "# Models Trained",
    "1. Logistic Regression (C, penalty, solver)",
    "2. Random Forest (n_estimators, max_depth, min_samples)",
    "",
    "# Evaluation: GridSearchCV 5-fold Stratified",
    "   Scoring: ROC-AUC",
]
draw_code_block(d, "preprocessing.py + train.py", preprocess_lines, 40, 200, 900, 400)
draw_metric_box(d, "LR CV ROC-AUC", "0.9113", 980, 200, w=380)
draw_metric_box(d, "LR Holdout ROC-AUC", "0.9611", 980, 320, w=380)
draw_metric_box(d, "RF CV ROC-AUC", "0.9029", 980, 440, w=380)
draw_metric_box(d, "RF Holdout ROC-AUC", "0.9535", 980, 560, w=380)
draw_metric_box(d, "Best Model", "Logistic Regression", 980, 680, w=380)
term_lines = [
    "$ python src/train.py --data data/heart_raw.csv",
    "# Training Logistic Regression with GridSearchCV...",
    "# Best LR params: C=0.1, penalty=l2, solver=lbfgs",
    "# Training Random Forest with GridSearchCV...",
    "# Best RF params: n_estimators=200, max_depth=10",
    "  Best model: logistic_regression (ROC-AUC: 0.9611)",
    "  Model saved to model_artifacts/model.joblib",
]
draw_terminal(d, term_lines, 40, 630, 900, 250)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 4: MLflow ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "4. MLflow Experiment Tracking", "All runs logged with parameters, metrics, and artifacts")
embed_screenshot(f, ss_dir / "05_mlflow_tracking.png", 40, 200, 880, 600)
mlflow_lines = [
    "$ mlflow ui --backend-store-uri sqlite:///mlflow.db",
    "",
    "# Logged for each run:",
    "  Parameters: C, penalty, solver, n_estimators...",
    "  Metrics:    cv_roc_auc_mean, cv_roc_auc_std,",
    "              holdout_roc_auc, accuracy, precision,",
    "              recall, f1",
    "  Artifacts:  model.joblib, confusion_matrix.png,",
    "              roc_curve.png, metadata.json",
    "",
    "  sqlite backend for portability",
    "  Compare runs side-by-side",
]
draw_terminal(d, mlflow_lines, 960, 200, 900, 500)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 5: API ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "5. FastAPI Model Serving", "RESTful API with /predict, /predict/batch, /health, /metrics")
embed_screenshot(f, ss_dir / "09_api_endpoints.png", 40, 200, 880, 500)
api_lines = [
    '$ curl -X POST http://localhost:8000/predict \\',
    '  -H "Content-Type: application/json" \\',
    '  -d \'{"age":67,"sex":1,"cp":4,"trestbps":160,',
    '       "chol":286,"fbs":0,"restecg":2,',
    '       "thalach":108,"exang":1,"oldpeak":1.5,',
    '       "slope":2,"ca":3,"thal":3}\'',
    '',
    '# Response:',
    '{',
    '  "prediction": 1,',
    '  "label": "Heart disease",',
    '  "confidence": 0.9818,',
    '  "model": "logistic_regression",',
    '  "api_version": "1.0.0"',
    '}',
]
draw_terminal(d, api_lines, 960, 200, 900, 500)
d.text((40, 730), "Endpoints:", font=FONTS["label"], fill=ACCENT)
endpoints = [
    "POST /predict        - Single patient prediction (JSON in/out)",
    "POST /predict/batch   - Batch predictions (list of patients)",
    "GET  /health          - Liveness/readiness probe",
    "GET  /metrics         - Prometheus-format metrics",
]
for i, ep in enumerate(endpoints):
    d.text((60, 760 + i*28), ep, font=FONTS["mono"], fill=TEXT_COLOR)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 6: Testing ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "6. Automated Testing", "29 pytest tests across 3 test files")
embed_screenshot(f, ss_dir / "07_pytest_results.png", 40, 200, 880, 500)
test_lines = [
    "$ pytest tests/ -v --tb=short",
    "",
    "tests/test_data.py          - 8 tests  passed",
    "  test_raw_csv_exists",
    "  test_column_count / test_column_names",
    "  test_target_values / test_no_all_null_columns",
    "",
    "tests/test_preprocessing.py - 9 tests  passed",
    "  test_pipeline_output_shape",
    "  test_no_nan_after_transform",
    "  test_scaler_applied / test_ohe_applied",
    "",
    "tests/test_api.py           - 12 tests passed",
    "  test_health / test_predict_valid",
    "  test_predict_batch / test_invalid_thal",
    "  test_metrics_endpoint",
    "",
    "======= 29 passed in 2.45s =======",
]
draw_terminal(d, test_lines, 960, 200, 900, 600)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 7: Docker ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "7. Docker Containerization", "Multi-stage build, non-root user, healthcheck")
embed_screenshot(f, ss_dir / "08_docker_build.png", 40, 200, 880, 400)
docker_lines = [
    "# Dockerfile - Multi-stage build",
    "FROM python:3.11-slim AS builder",
    "  -> Install dependencies in /opt/venv",
    "",
    "FROM python:3.11-slim AS runtime",
    "  -> Copy venv from builder",
    "  -> Copy app.py, src/, model_artifacts/",
    "  -> Non-root user (appuser, uid 10001)",
    "  -> HEALTHCHECK on /health endpoint",
    "  -> CMD uvicorn app:app --port ${PORT:-8000}",
    "",
    "$ docker build -t heart-api:latest .",
    "$ docker run -p 8000:8000 heart-api:latest",
    "  Image size: ~250 MB (slim base)",
    "  Runs as non-root for security",
]
draw_terminal(d, docker_lines, 960, 200, 900, 500)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 8: CI/CD ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "8. CI/CD Pipeline", "GitHub Actions - 5 stages, automated on every push")
embed_screenshot(f, ss_dir / "06_ci_pipeline.png", 40, 200, 880, 500)
cicd_lines = [
    "# .github/workflows/mlops-pipeline.yml",
    "",
    "Stage 1: LINT",
    "  -> flake8 + black --check",
    "",
    "Stage 2: TEST",
    "  -> pytest tests/ -v (29 tests)",
    "",
    "Stage 3: TRAIN",
    "  -> python src/train.py",
    "  -> Upload model artifact",
    "",
    "Stage 4: DOCKER BUILD",
    "  -> docker build + test /health",
    "",
    "Stage 5: K8S DEPLOY",
    "  -> kind cluster + kubectl apply",
    "  -> Verify pods & service",
    "",
    "  Pipeline passes on all stages",
]
draw_terminal(d, cicd_lines, 960, 200, 900, 600)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 9: Kubernetes + Helm ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "9. Kubernetes & Helm Deployment", "Deployment, Service, HPA, Ingress - templated via Helm")
embed_screenshot(f, ss_dir / "10_kubernetes.png", 40, 200, 880, 400)
k8s_lines = [
    "# Kubernetes Resources",
    "Deployment:  2 replicas, rolling update",
    "Service:     LoadBalancer (port 80 -> 8000)",
    "HPA:         2-5 replicas at 70% CPU",
    "Ingress:     nginx, host: heart-api.local",
    "",
    "# Helm Chart: deployment/helm/heart-api/",
    "$ helm install heart-api deployment/helm/heart-api/",
    "",
    "values.yaml defaults:",
    "  replicaCount: 2",
    "  image.repository: heart-api",
    "  service.type: LoadBalancer",
    "  autoscaling.enabled: true",
    "  ingress.enabled: true",
    "  probes: liveness + readiness on /health",
    "",
    "  All manifests templated via Go templates",
]
draw_terminal(d, k8s_lines, 960, 200, 900, 560)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 10: Monitoring ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "10. Monitoring & Logging", "Prometheus + Grafana via docker-compose")
embed_screenshot(f, ss_dir / "11_monitoring.png", 40, 200, 880, 500)
mon_lines = [
    "# docker-compose.monitoring.yml",
    "services:",
    "  api:         heart-api on :8000",
    "  prometheus:  scrape /metrics on :9090",
    "  grafana:     dashboards on :3000",
    "",
    "# Metrics exposed at /metrics:",
    "  http_requests_total{method,endpoint,status}",
    "  http_request_duration_seconds",
    "  predictions_total{result}",
    "  model_confidence_histogram",
    "",
    "$ docker compose -f monitoring/\\",
    "    docker-compose.monitoring.yml up",
    "",
    "  Prometheus scrapes every 15s",
    "  Grafana auto-provisioned dashboard",
]
draw_terminal(d, mon_lines, 960, 200, 900, 560)
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 11: Live Deployment ---
f = new_frame(); d = ImageDraw.Draw(f)
draw_header(d, "11. Live Public Deployment", "Deployed on Render - accessible worldwide")
d.rounded_rectangle([40, 200, 1860, 700], radius=15, fill=CODE_BG)
d.text((80, 230), "Live API URL", font=FONTS["heading"], fill=GREEN)
d.text((80, 290), "https://heart-mlops.onrender.com", font=FONTS["title"], fill=ACCENT)
d.text((80, 380), "Available Endpoints:", font=FONTS["label"], fill=TITLE_COLOR)
endpoints_live = [
    ("GET  /docs", "Interactive Swagger UI documentation"),
    ("GET  /health", "Liveness check - returns {status: healthy}"),
    ("GET  /metrics", "Prometheus-format metrics for monitoring"),
    ("POST /predict", "Single patient heart disease prediction"),
    ("POST /predict/batch", "Batch predictions for multiple patients"),
]
for i, (ep, desc) in enumerate(endpoints_live):
    y = 420 + i * 50
    d.text((100, y), ep, font=FONTS["mono_lg"], fill=GREEN)
    d.text((500, y), desc, font=FONTS["body"], fill=TEXT_COLOR)
d.text((80, 730), "Platform: Render (Free Tier) | Runtime: Docker | Region: Oregon US-West", font=FONTS["body"], fill=(150, 150, 170))
frames.append(save(f, idx, 5)); idx += 1

# --- Frame 12: Summary ---
f = new_frame(); d = ImageDraw.Draw(f)
d.rectangle([0, 0, WIDTH, HEIGHT], fill=(10, 10, 30))
d.text((WIDTH//2 - 200, 150), "Pipeline Summary", font=FONTS["title"], fill=TITLE_COLOR)
checklist = [
    ("Data Acquisition & EDA", "UCI Heart Disease, 303 samples, 4 visualizations"),
    ("Feature Engineering & Training", "LogReg & RF, GridSearchCV, ROC-AUC 0.9611"),
    ("MLflow Experiment Tracking", "Parameters, metrics, artifacts logged"),
    ("Model Packaging", "joblib + sklearn Pipeline, full reproducibility"),
    ("CI/CD Pipeline", "GitHub Actions, 5 stages, automated testing"),
    ("Docker Containerization", "Multi-stage, non-root, healthcheck"),
    ("Kubernetes + Helm", "Deployment, Service, HPA, Ingress"),
    ("Monitoring", "Prometheus + Grafana, request/prediction metrics"),
    ("Public Deployment", "https://heart-mlops.onrender.com"),
]
for i, (title, desc) in enumerate(checklist):
    y = 260 + i * 70
    d.text((100, y), "[Done]", font=FONTS["heading"], fill=GREEN)
    d.text((250, y), title, font=FONTS["label"], fill=TITLE_COLOR)
    d.text((250, y + 28), desc, font=FONTS["small"], fill=(150, 150, 170))
d.text((WIDTH//2 - 250, 920), "Veeranjineyulu Pentela - BITS WILP M.Tech AI&ML", font=FONTS["subtitle"], fill=ACCENT)
d.text((WIDTH//2 - 180, 960), "GitHub: veerusgithub/heart-mlops", font=FONTS["body"], fill=(150, 150, 170))
frames.append(save(f, idx, 6)); idx += 1

# ===== COMPILE VIDEO =====
print(f"Generated {len(frames)} frames")

concat_file = FRAMES_DIR / "concat.txt"
with open(concat_file, "w") as cf:
    for path, dur in frames:
        cf.write(f"file '{path.name}'\n")
        cf.write(f"duration {dur}\n")
    # Last frame repeated for ffmpeg concat demuxer
    cf.write(f"file '{frames[-1][0].name}'\n")

output = "reports/pipeline_demo_video.mp4"
cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat_file),
    "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
    "-movflags", "+faststart",
    output
]
print(f"Compiling video -> {output}")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    size = os.path.getsize(output)
    print(f"Video saved: {output} ({size/1024:.0f} KB)")
else:
    print(f"ERROR: {result.stderr[-500:]}")
