# Heart Disease Risk Prediction — End-to-End MLOps Pipeline

Production-grade MLOps pipeline that predicts heart-disease risk from patient
clinical data (UCI Heart Disease / Cleveland) and serves it as a monitored,
containerised, Kubernetes-deployable API.

**Selected model:** Logistic Regression — **5-fold CV ROC-AUC 0.911 ± 0.018**;
hold-out (61 patients) ROC-AUC 0.961, recall 0.929. Chosen by cross-validation only.

---

## Pipeline at a glance

```
download → EDA/clean → preprocess (impute+scale+OHE) → train+tune (LogReg, RF)
   → MLflow tracking → best model.joblib → FastAPI /predict → Docker → Kubernetes
   → Prometheus + Grafana monitoring ;  all gated by GitHub Actions CI/CD
```

See `reports/figures/architecture.png` for the full diagram.

---

## Quickstart

```bash
# 1. Install
pip install -r requirements.txt

# 2. Data → EDA → Train (produces model_artifacts/ + reports/figures/ + mlflow.db)
make all            # or run the three scripts individually:
python src/download_data.py --out data/heart_raw.csv
python src/eda.py           --data data/heart_raw.csv --outdir reports/figures
python src/train.py         --data data/heart_raw.csv

# 3. Tests
make test           # 29 pytest tests: data, preprocessing, model/API

# 4. Serve locally
make serve          # uvicorn app:app on http://localhost:8000  (docs at /docs)
```

### Try the API

```bash
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"age":67,"sex":1,"cp":4,"trestbps":160,"chol":286,"fbs":0,"restecg":2,
       "thalach":108,"exang":1,"oldpeak":1.5,"slope":2,"ca":3,"thal":3}'
# -> {"prediction":1,"label":"Heart disease","confidence":0.9818,...}
# Inputs use the raw UCI codes: cp 1-4, slope 1-3, ca 0-3, thal in {3,6,7}.
```

---

## One-shot Docker + Kubernetes + monitoring verification (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy_and_verify.ps1
```

Builds the image, runs the container, tests `/predict`, deploys `deployment/` to
the current kubectl context (Docker Desktop Kubernetes or Minikube), tests the
Service, then starts Prometheus + Grafana and checks the scrape target. Text proof
is written to `screenshots/evidence/`; the script pauses where you should take the
PNG screenshots. Options: `-SkipK8s`, `-SkipMonitoring`, `-NoPause`.

## Docker

```bash
make docker-build                 # docker build -t heart-api:latest .
make docker-run                   # runs on :8000
# full stack with monitoring:
docker compose -f monitoring/docker-compose.monitoring.yml up --build
#   API        http://localhost:8000/docs
#   Prometheus http://localhost:9090
#   Grafana    http://localhost:3000  (admin/admin)
```

## Kubernetes (Minikube)

```bash
eval $(minikube docker-env)       # build into Minikube's docker
docker build -t heart-api:latest .
kubectl apply -f deployment/
minikube service heart-api-service --url
```

## MLflow UI

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

---

## Repository layout

| Path | Purpose |
|------|---------|
| `heart+disease/` | Original UCI files (`processed.cleveland.data`, `heart-disease.names`) |
| `src/download_data.py` | Read the UCI Cleveland file (bundled, else UCI URL); add column names, `?`→NaN, binarise `num` |
| `src/preprocessing.py` | Feature schema + sklearn preprocessing pipeline (shared) |
| `src/eda.py` | EDA figures + summary |
| `src/train.py` | Train, tune (GridSearchCV), evaluate, MLflow logging, save best |
| `src/predict.py` | Standalone batch/single inference CLI |
| `app.py` | FastAPI serving app (`/predict`, `/health`, `/metrics`) |
| `tests/` | Pytest unit tests (preprocessing + API/model) |
| `Dockerfile` | Multi-stage, non-root serving image |
| `scripts/deploy_and_verify.ps1` | Docker + Kubernetes + monitoring verification, saves evidence |
| `deployment/` | Kubernetes manifests (deployment, service, ingress, HPA) |
| `monitoring/` | Prometheus + Grafana config & compose stack |
| `.github/workflows/` | CI/CD: lint → test → train → docker build+smoke |
| `notebooks/` | Interactive EDA + training notebook |
| `reports/` | Report, metrics.json, figures |
| `model_artifacts/` | `model.joblib`, `feature_schema.json`, `metadata.json` |

---

## Dataset

UCI Heart Disease, **Cleveland** subset (`processed.cleveland.data`): 303 patients,
13 clinical features, no header row, `?` for missing values. The raw label `num`
(0-4) is binarised as `target = (num > 0)`. Result: **303 rows, 164 no-disease /
139 disease**; 6 missing cells (`ca` 4, `thal` 2), imputed inside the model
pipeline. Raw UCI codes are used throughout (cp 1-4, slope 1-3, thal 3/6/7).
The data script deliberately has no third-party fallback so mislabelled copies
can never be used silently.

## Model

Two classifiers are trained inside a single sklearn `Pipeline` (so preprocessing
is fit per fold, no leakage), each tuned with 5-fold stratified `GridSearchCV` on
ROC-AUC. The winner is picked by **cross-validated** ROC-AUC; the 20% hold-out
(61 rows) is only a final estimate. The fitted pipeline is serialised with its
preprocessing intact, guaranteeing train/serve parity.

| Model | CV ROC-AUC | Hold-out ROC-AUC | Accuracy | Precision | Recall | F1 |
|-------|-----------:|-----------------:|---------:|----------:|-------:|---:|
| **Logistic Regression** ✅ | **0.911** | **0.961** | 0.885 | 0.839 | 0.929 | 0.881 |
| Random Forest | 0.903 | 0.954 | 0.885 | 0.818 | 0.964 | 0.885 |

The hold-out set is small; the two models are statistically close (the recall gap
is one patient). See `reports/report.pdf`.

## Notes

- `src/` is the single source of truth; the notebook mirrors it for exploration.
- Predictions are **not medical advice**; this is an academic demonstration.

## License

MIT — see `LICENSE`.
