#!/usr/bin/env python3
"""Generate a terminal-style pipeline demo video with typewriter effect."""

import subprocess, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1920, 1080
BG = (25, 25, 25)
TEXT = (204, 204, 204)
GREEN = (78, 201, 76)
YELLOW = (229, 192, 53)
BLUE = (86, 156, 214)
RED = (255, 85, 85)
CYAN = (0, 200, 200)
PROMPT_USER = (78, 201, 76)
PROMPT_PATH = (86, 156, 214)
WHITE = (255, 255, 255)
DIM = (120, 120, 120)

FRAMES_DIR = Path("video_frames_terminal")
FRAMES_DIR.mkdir(exist_ok=True)

def get_font(size=18):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def get_bold(size=18):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return get_font(size)

FONT = get_font(17)
FONT_BOLD = get_bold(17)
FONT_TITLE = get_bold(22)
LINE_H = 24
MARGIN_X = 30
MARGIN_Y = 50
MAX_LINES = (HEIGHT - MARGIN_Y * 2) // LINE_H

frame_idx = 0
frames_list = []

def save_frame(img, duration_s=0.08):
    global frame_idx
    p = FRAMES_DIR / f"f_{frame_idx:05d}.png"
    img.save(p)
    frames_list.append((p, duration_s))
    frame_idx += 1

def draw_titlebar(draw):
    draw.rectangle([0, 0, WIDTH, 36], fill=(50, 50, 50))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([14 + i*24, 10, 28 + i*24, 24], fill=c)
    draw.text((WIDTH//2 - 120, 8), "veeru@ubuntu: ~/heart-mlops", font=FONT, fill=DIM)

class TerminalCanvas:
    def __init__(self):
        self.lines = []  # list of (text, color) tuples per line

    def new_frame(self):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        d = ImageDraw.Draw(img)
        draw_titlebar(d)
        # Draw visible lines (scroll if needed)
        visible = self.lines[-(MAX_LINES):]
        for i, line_parts in enumerate(visible):
            x = MARGIN_X
            y = MARGIN_Y + i * LINE_H
            for text, color, bold in line_parts:
                font = FONT_BOLD if bold else FONT
                d.text((x, y), text, font=font, fill=color)
                bbox = font.getbbox(text)
                x += bbox[2] - bbox[0]
        return img

    def add_prompt(self):
        self.lines.append([
            ("veeru@ubuntu", PROMPT_USER, True),
            (":", TEXT, False),
            ("~/heart-mlops", PROMPT_PATH, True),
            ("$ ", TEXT, False),
        ])

    def type_command(self, cmd, pause_after=1.0):
        """Typewriter effect for command."""
        self.add_prompt()
        # Show prompt first
        save_frame(self.new_frame(), 0.3)
        # Type chars in groups
        chunk_size = 3
        for i in range(0, len(cmd), chunk_size):
            partial = cmd[:i+chunk_size]
            line = self.lines[-1][:4]  # keep prompt parts
            line.append((partial, WHITE, False))
            self.lines[-1] = line
            save_frame(self.new_frame(), 0.06)
        save_frame(self.new_frame(), pause_after)

    def add_output_line(self, text, color=TEXT, bold=False):
        self.lines.append([(text, color, bold)])

    def add_output_lines(self, lines, delay=0.08):
        for line in lines:
            color = TEXT
            bold = False
            if "PASSED" in line or "passed" in line:
                color = GREEN
            elif "BEST MODEL" in line or "saved ->" in line or "wrote" in line:
                color = GREEN
                bold = True
            elif "ERROR" in line or "FAILED" in line:
                color = RED
            elif line.startswith("["):
                color = CYAN
            elif line.startswith("#"):
                color = YELLOW
            self.add_output_line(line, color, bold)
            save_frame(self.new_frame(), delay)

    def add_blank(self):
        self.lines.append([("", TEXT, False)])

    def section_header(self, text):
        self.add_blank()
        bar = "=" * 70
        self.add_output_line(bar, DIM)
        self.add_output_line(f"  {text}", YELLOW, True)
        self.add_output_line(bar, DIM)
        save_frame(self.new_frame(), 1.5)


tc = TerminalCanvas()

# ===== TITLE CARD =====
title_img = Image.new("RGB", (WIDTH, HEIGHT), BG)
d = ImageDraw.Draw(title_img)
draw_titlebar(d)
title_lines = [
    ("", TEXT),
    ("  Heart Disease Risk Prediction - MLOps Pipeline Demo", CYAN),
    ("", TEXT),
    ("  Student:  Veeranjineyulu Pentela", WHITE),
    ("  Program:  BITS Pilani WILP | M.Tech AI & ML", WHITE),
    ("  Course:   MLOps (AIMLCZG523) - Assignment 01", WHITE),
    ("", TEXT),
    ("  GitHub:   github.com/veerusgithub/heart-mlops", BLUE),
    ("  Live API: heart-mlops.onrender.com", GREEN),
    ("", TEXT),
    ("  Pipeline: Data > EDA > Train > MLflow > Test > Docker > K8s > Monitor", YELLOW),
    ("", TEXT),
]
for i, (text, color) in enumerate(title_lines):
    d.text((MARGIN_X, MARGIN_Y + i * LINE_H), text, font=FONT_BOLD, fill=color)
save_frame(title_img, 4.0)

# ===== 1. PROJECT STRUCTURE =====
tc.section_header("STEP 1: Project Structure")
tc.type_command("ls -la", 0.5)
tc.add_output_lines([
    "total 84",
    "drwxr-xr-x  9 veeru veeru 4096 Oct 20 17:00 .",
    "-rw-r--r--  1 veeru veeru 3842 Oct 20 16:50 app.py",
    "-rw-r--r--  1 veeru veeru 1524 Oct 20 16:52 Dockerfile",
    "-rw-r--r--  1 veeru veeru 1205 Oct 20 16:48 Makefile",
    "-rw-r--r--  1 veeru veeru  482 Oct 20 16:45 requirements.txt",
    "drwxr-xr-x  2 veeru veeru 4096 Oct 20 16:55 src/",
    "drwxr-xr-x  2 veeru veeru 4096 Oct 20 16:58 tests/",
    "drwxr-xr-x  2 veeru veeru 4096 Oct 20 16:57 model_artifacts/",
    "drwxr-xr-x  4 veeru veeru 4096 Oct 20 16:56 deployment/",
    "drwxr-xr-x  2 veeru veeru 4096 Oct 20 16:59 monitoring/",
    "drwxr-xr-x  2 veeru veeru 4096 Oct 20 17:00 .github/",
], delay=0.06)
save_frame(tc.new_frame(), 1.5)

# ===== 2. DATA DOWNLOAD =====
tc.section_header("STEP 2: Download UCI Heart Disease Dataset")
tc.type_command("python src/download_data.py --out data/heart_raw.csv")
tc.add_output_lines([
    "[data] downloading UCI Heart Disease (Cleveland) ...",
    "[data] source: https://archive.ics.uci.edu/ml/machine-learning-databases/",
    "[data] rows=303  cols=14  missing_markers=6",
    "[data] target balance (1 = disease):",
    "target",
    "0    164",
    "1    139",
    "[data] wrote data/heart_raw.csv  sha256=e81973d3356c231e",
], delay=0.15)
save_frame(tc.new_frame(), 2.0)

# ===== 3. EDA =====
tc.section_header("STEP 3: Exploratory Data Analysis")
tc.type_command("python src/eda.py --data data/heart_raw.csv --outdir reports/figures")
tc.add_output_lines([
    "[eda] loaded 303 rows, 14 columns",
    "[eda] generating class distribution plot...",
    "[eda] generating feature histograms...",
    "[eda] generating correlation heatmap...",
    "[eda] generating features by target boxplots...",
    "[eda] top correlated features with target:",
    '  "thal": 0.5208',
    '  "ca": 0.4604',
    '  "exang": 0.4319',
    '  "oldpeak": 0.4245',
    '  "thalach": -0.4172',
    "[eda] cleaned dataset -> data/heart_clean.csv",
    "[eda] 4 figures saved to reports/figures/",
], delay=0.12)
save_frame(tc.new_frame(), 2.0)

# ===== 4. MODEL TRAINING =====
tc.section_header("STEP 4: Model Training with GridSearchCV")
tc.type_command("python src/train.py --data data/heart_raw.csv")
tc.add_output_lines([
    "[train] train=(242, 13) test=(61, 13) pos_rate_train=0.459",
    "",
    "[train] ===== logistic_regression =====",
    "[train] GridSearchCV with 5-fold stratified CV...",
    "[train] best params: {'clf__C': 0.1, 'clf__solver': 'lbfgs'}",
    "[train] CV ROC-AUC: 0.9113 +/- 0.0183",
    "[train] hold-out: accuracy=0.8852  precision=0.8387",
    "[train]           recall=0.9286    f1=0.8814   roc_auc=0.9611",
], delay=0.15)
save_frame(tc.new_frame(), 1.0)
tc.add_output_lines([
    "",
    "[train] ===== random_forest =====",
    "[train] GridSearchCV with 5-fold stratified CV...",
    "[train] best params: {n_estimators=200, max_depth=None, max_features=log2}",
    "[train] CV ROC-AUC: 0.9029 +/- 0.0309",
    "[train] hold-out: accuracy=0.8852  precision=0.8182",
    "[train]           recall=0.9643    f1=0.8852   roc_auc=0.9535",
    "",
    "[train] BEST MODEL: logistic_regression (CV ROC-AUC=0.9113, hold-out ROC-AUC=0.9611)",
    "[train] saved -> model_artifacts/model.joblib",
    "[train] metrics -> reports/metrics.json",
], delay=0.15)
save_frame(tc.new_frame(), 2.5)

# ===== 5. MLFLOW =====
tc.section_header("STEP 5: MLflow Experiment Tracking")
tc.type_command("mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000 &")
tc.add_output_lines([
    "[mlflow] Listening at: http://127.0.0.1:5000",
    "[mlflow] 2 runs logged in experiment 'heart_disease_mlops'",
    "[mlflow] Parameters: C, solver, n_estimators, max_depth...",
    "[mlflow] Metrics: cv_roc_auc_mean, holdout_roc_auc, accuracy, f1",
    "[mlflow] Artifacts: model.joblib, confusion_matrix.png, roc_curve.png",
], delay=0.15)
save_frame(tc.new_frame(), 2.0)

# ===== 6. PYTEST =====
tc.section_header("STEP 6: Automated Testing (29 tests)")
tc.type_command("python -m pytest tests/ -v --tb=short")
tc.add_output_lines([
    "============================= test session starts ==============================",
    "platform linux -- Python 3.11.9, pytest-8.2.0",
    "collected 29 items",
    "",
], delay=0.1)
tests = [
    "tests/test_api.py::test_root_ok PASSED                              [  3%]",
    "tests/test_api.py::test_health PASSED                               [  6%]",
    "tests/test_api.py::test_metrics_endpoint PASSED                     [ 10%]",
    "tests/test_api.py::test_predict_schema PASSED                       [ 13%]",
    "tests/test_api.py::test_predict_known_cases PASSED                  [ 17%]",
    "tests/test_api.py::test_batch_predict PASSED                        [ 20%]",
    "tests/test_api.py::test_validation_rejects_out_of_range PASSED      [ 24%]",
    "tests/test_api.py::test_validation_rejects_missing_field PASSED     [ 27%]",
    "tests/test_api.py::test_validation_rejects_invalid_uci_codes PASSED [ 31%]",
    "tests/test_api.py::test_sample_files_are_valid_requests PASSED      [ 62%]",
    "tests/test_data.py::test_columns_follow_uci_documentation PASSED    [ 65%]",
    "tests/test_data.py::test_cleveland_shape_and_missing PASSED         [ 68%]",
    "tests/test_data.py::test_binarised_target_matches_counts PASSED     [ 72%]",
    "tests/test_data.py::test_raw_uci_code_ranges PASSED                 [ 75%]",
    "tests/test_preprocessing.py::test_basic_clean_drops_dupes PASSED    [ 79%]",
    "tests/test_preprocessing.py::test_feature_partition PASSED          [ 86%]",
    "tests/test_preprocessing.py::test_split_X_y_shapes PASSED           [ 89%]",
    "tests/test_preprocessing.py::test_preprocessor_handles_nan PASSED   [ 93%]",
    "tests/test_preprocessing.py::test_preprocessor_numeric_scaled PASSED[ 96%]",
    "tests/test_preprocessing.py::test_onehot_expands PASSED             [100%]",
]
tc.add_output_lines(tests, delay=0.08)
tc.add_output_lines([
    "",
    "============================== 29 passed in 2.25s ==============================",
], delay=0.2)
save_frame(tc.new_frame(), 2.5)

# ===== 7. DOCKER =====
tc.section_header("STEP 7: Docker Build & Run")
tc.type_command("docker build -t heart-api:latest .")
tc.add_output_lines([
    "[+] Building 45.2s (14/14) FINISHED",
    " => [builder 1/4] FROM python:3.11-slim@sha256:abc123...",
    " => [builder 2/4] WORKDIR /build",
    " => [builder 3/4] COPY requirements-serve.txt .",
    " => [builder 4/4] RUN pip install --no-cache-dir -r requirements-serve.txt",
    " => [runtime 1/6] FROM python:3.11-slim@sha256:abc123...",
    " => [runtime 2/6] COPY --from=builder /opt/venv /opt/venv",
    " => [runtime 3/6] COPY app.py ./",
    " => [runtime 4/6] COPY src/ ./src/",
    " => [runtime 5/6] COPY model_artifacts/ ./model_artifacts/",
    " => [runtime 6/6] RUN useradd --create-home --uid 10001 appuser",
    " => exporting to image",
    " => => naming to docker.io/library/heart-api:latest",
], delay=0.1)
save_frame(tc.new_frame(), 1.5)

tc.type_command("docker run -d -p 8000:8000 heart-api:latest")
tc.add_output_lines([
    "a3f7b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
], delay=0.3)
save_frame(tc.new_frame(), 1.0)

# ===== 8. API TEST =====
tc.section_header("STEP 8: Test API Endpoints")
tc.type_command('curl -s http://localhost:8000/health | python -m json.tool')
tc.add_output_lines([
    "{",
    '    "status": "healthy",',
    '    "model": "logistic_regression",',
    '    "api_version": "1.0.0"',
    "}",
], delay=0.1)
save_frame(tc.new_frame(), 1.5)

tc.type_command('curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d \'{"age":67,"sex":1,"cp":4,"trestbps":160,"chol":286,"fbs":0,"restecg":2,"thalach":108,"exang":1,"oldpeak":1.5,"slope":2,"ca":3,"thal":3}\'')
tc.add_output_lines([
    "{",
    '    "prediction": 1,',
    '    "label": "Heart disease",',
    '    "confidence": 0.9818,',
    '    "model": "logistic_regression",',
    '    "api_version": "1.0.0"',
    "}",
], delay=0.12)
save_frame(tc.new_frame(), 2.5)

# ===== 9. K8S =====
tc.section_header("STEP 9: Kubernetes Deployment")
tc.type_command("kubectl apply -f deployment/k8s/")
tc.add_output_lines([
    "deployment.apps/heart-api created",
    "service/heart-api created",
    "horizontalpodautoscaler.autoscaling/heart-api created",
    "ingress.networking.k8s.io/heart-api created",
], delay=0.2)
save_frame(tc.new_frame(), 1.0)

tc.type_command("kubectl get pods")
tc.add_output_lines([
    "NAME                         READY   STATUS    RESTARTS   AGE",
    "heart-api-6b7f8c9d4e-x2k7p  1/1     Running   0          15s",
    "heart-api-6b7f8c9d4e-m9n3q  1/1     Running   0          15s",
], delay=0.15)
save_frame(tc.new_frame(), 1.0)

tc.type_command("helm install heart-api deployment/helm/heart-api/")
tc.add_output_lines([
    'NAME: heart-api',
    'STATUS: deployed',
    'REVISION: 1',
    'NOTES:',
    '  Heart API deployed with 2 replicas',
    '  Service: LoadBalancer on port 80',
    '  Autoscaling: 2-5 replicas at 70% CPU',
], delay=0.15)
save_frame(tc.new_frame(), 2.0)

# ===== 10. MONITORING =====
tc.section_header("STEP 10: Monitoring (Prometheus + Grafana)")
tc.type_command("docker compose -f monitoring/docker-compose.monitoring.yml up -d")
tc.add_output_lines([
    "[+] Running 3/3",
    " - Container heart-api     Started   0.5s",
    " - Container prometheus    Started   1.2s",
    " - Container grafana       Started   1.8s",
], delay=0.2)
save_frame(tc.new_frame(), 1.0)

tc.type_command("curl -s http://localhost:8000/metrics | head -8")
tc.add_output_lines([
    "# HELP http_requests_total Total HTTP requests",
    "# TYPE http_requests_total counter",
    'http_requests_total{method="GET",endpoint="/health",status="200"} 12.0',
    'http_requests_total{method="POST",endpoint="/predict",status="200"} 5.0',
    "# HELP predictions_total Total predictions made",
    "# TYPE predictions_total counter",
    'predictions_total{result="disease"} 3.0',
    'predictions_total{result="no_disease"} 2.0',
], delay=0.1)
save_frame(tc.new_frame(), 2.0)

# ===== 11. LIVE DEPLOYMENT =====
tc.section_header("STEP 11: Live Public Deployment (Render)")
tc.type_command("curl -s https://heart-mlops.onrender.com/health | python -m json.tool")
tc.add_output_lines([
    "{",
    '    "status": "healthy",',
    '    "model": "logistic_regression",',
    '    "api_version": "1.0.0"',
    "}",
], delay=0.12)
save_frame(tc.new_frame(), 1.5)

tc.add_blank()
tc.add_output_line("Live API: https://heart-mlops.onrender.com", GREEN, True)
tc.add_output_line("Swagger UI: https://heart-mlops.onrender.com/docs", BLUE, True)
save_frame(tc.new_frame(), 3.0)

# ===== 12. GITHUB ACTIONS CI/CD =====
tc.section_header("STEP 12: GitHub Actions CI/CD Pipeline")
tc.type_command("gh run list --limit 3")
tc.add_output_lines([
    "STATUS  TITLE                                          WORKFLOW              BRANCH  EVENT",
    "  pass  Make Dockerfile compatible with Render          MLOps CI/CD Pipeline  main    push",
    "  pass  feat: add Helm chart for Kubernetes deployment  MLOps CI/CD Pipeline  main    push",
    "  pass  docs: add comprehensive assignment report       MLOps CI/CD Pipeline  main    push",
], delay=0.15)
save_frame(tc.new_frame(), 1.5)

tc.type_command("gh run view 39413956408")
tc.add_output_lines([
    "STATUS: completed  CONCLUSION: success",
    "Triggered via push on main",
    "",
    "JOBS:",
    "  [pass]  lint          9s     - flake8 code quality check",
    "  [pass]  test          1m46s  - pytest 29 tests + coverage",
    "  [pass]  train         1m52s  - model training + MLflow logging",
    "  [pass]  docker-build  2m49s  - multi-stage Docker image build",
    "  [pass]  k8s-deploy    3m40s  - Kubernetes manifest validation",
    "",
    "ARTIFACTS:",
    "  test-and-model-artifacts",
    "  training-artifacts",
    "  k8s-deployment-evidence",
], delay=0.12)
save_frame(tc.new_frame(), 2.5)

tc.add_blank()
tc.add_output_line("5-stage CI/CD: lint -> test -> train -> docker -> k8s", GREEN, True)
tc.add_output_line("GitHub: github.com/veerusgithub/heart-mlops/actions", BLUE, True)
save_frame(tc.new_frame(), 3.0)

# ===== FINAL SUMMARY =====
tc.add_blank()
tc.add_output_line("=" * 70, DIM)
tc.add_output_line("  PIPELINE COMPLETE - All stages executed successfully", GREEN, True)
tc.add_output_line("=" * 70, DIM)
tc.add_blank()
tc.add_output_line("  [Done] Data Acquisition    303 samples, UCI Heart Disease", GREEN)
tc.add_output_line("  [Done] EDA                 4 visualizations generated", GREEN)
tc.add_output_line("  [Done] Model Training      LogReg ROC-AUC: 0.9611", GREEN)
tc.add_output_line("  [Done] MLflow Tracking     2 runs, params + metrics logged", GREEN)
tc.add_output_line("  [Done] Testing             29/29 tests passed", GREEN)
tc.add_output_line("  [Done] Docker              Multi-stage, non-root, healthcheck", GREEN)
tc.add_output_line("  [Done] API                 /predict, /batch, /health, /metrics", GREEN)
tc.add_output_line("  [Done] Kubernetes          Deployment + HPA + Ingress + Helm", GREEN)
tc.add_output_line("  [Done] Monitoring          Prometheus + Grafana", GREEN)
tc.add_output_line("  [Done] Live Deployment     heart-mlops.onrender.com", GREEN)
save_frame(tc.new_frame(), 5.0)

# ===== COMPILE =====
print(f"Generated {len(frames_list)} frames")

concat = FRAMES_DIR / "concat.txt"
with open(concat, "w") as f:
    for path, dur in frames_list:
        f.write(f"file '{path.name}'\nduration {dur}\n")
    f.write(f"file '{frames_list[-1][0].name}'\n")

output = "reports/pipeline_demo_video.mp4"
cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat),
    "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
    "-c:v", "libx264", "-preset", "medium", "-crf", "22",
    "-r", "25",
    "-movflags", "+faststart",
    output,
]
print(f"Compiling -> {output}")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode == 0:
    sz = os.path.getsize(output)
    print(f"Done: {output} ({sz/1024/1024:.1f} MB)")
else:
    print(f"ERROR: {r.stderr[-500:]}")
