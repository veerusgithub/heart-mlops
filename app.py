"""
FastAPI model-serving application for heart-disease risk prediction.

Endpoints
---------
GET  /            -> service metadata
GET  /health      -> liveness/readiness probe (model loaded?)
GET  /metrics     -> Prometheus metrics (requests, latency, predictions)
POST /predict     -> JSON patient record -> {prediction, confidence, ...}
POST /predict/batch -> list of records -> list of predictions

The app loads the single fitted sklearn Pipeline produced by src/train.py,
so preprocessing and model are applied exactly as in training.
"""
from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------------
# Logging: structured-ish JSON lines to stdout (container-friendly)
# ----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger("heart-api")

MODEL_DIR = Path(os.getenv("MODEL_DIR", "model_artifacts"))
MODEL_PATH = MODEL_DIR / "model.joblib"
SCHEMA_PATH = MODEL_DIR / "feature_schema.json"
META_PATH = MODEL_DIR / "metadata.json"

# Feature order the model expects (fallback if schema file is absent)
DEFAULT_FEATURE_ORDER = [
    "age", "trestbps", "chol", "thalach", "oldpeak", "ca",
    "sex", "cp", "fbs", "restecg", "exang", "slope", "thal",
]

# ----------------------------------------------------------------------------
# Prometheus metrics
# ----------------------------------------------------------------------------
PRED_COUNTER = Counter(
    "heart_predictions_total", "Total predictions served", ["outcome"])
REQ_COUNTER = Counter(
    "heart_requests_total", "Total HTTP requests", ["endpoint", "status"])
LATENCY = Histogram(
    "heart_predict_latency_seconds", "Prediction latency (seconds)")


# ----------------------------------------------------------------------------
# Request / response schemas
# ----------------------------------------------------------------------------
class PatientFeatures(BaseModel):
    """One patient record. Ranges mirror the Cleveland dataset."""
    age: float = Field(..., ge=0, le=120, description="Age in years")
    sex: int = Field(..., ge=0, le=1, description="0 = female, 1 = male")
    cp: int = Field(..., ge=1, le=4, description="Chest pain type (1-4; 4 = asymptomatic)")
    trestbps: float = Field(..., ge=50, le=260, description="Resting BP (mm Hg)")
    chol: float = Field(..., ge=80, le=700, description="Serum cholesterol (mg/dl)")
    fbs: int = Field(..., ge=0, le=1, description="Fasting blood sugar >120 (0/1)")
    restecg: int = Field(..., ge=0, le=2, description="Resting ECG (0-2)")
    thalach: float = Field(..., ge=50, le=260, description="Max heart rate")
    exang: int = Field(..., ge=0, le=1, description="Exercise-induced angina (0/1)")
    oldpeak: float = Field(..., ge=0, le=10, description="ST depression")
    slope: int = Field(..., ge=1, le=3, description="ST slope (1=up, 2=flat, 3=down)")
    ca: int = Field(..., ge=0, le=3, description="Major vessels coloured by fluoroscopy (0-3)")
    thal: Literal[3, 6, 7] = Field(..., description="3=normal, 6=fixed defect, 7=reversible defect")

    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 37, "sex": 0, "cp": 2, "trestbps": 120, "chol": 215,
                "fbs": 0, "restecg": 1, "thalach": 170, "exang": 0,
                "oldpeak": 0.0, "slope": 2, "ca": 0, "thal": 3,
            }
        }
    }


class PredictionResponse(BaseModel):
    prediction: int = Field(..., description="0 = no disease, 1 = disease")
    label: Literal["No heart disease", "Heart disease"]
    confidence: float = Field(..., description="Probability of predicted class")
    probability_disease: float = Field(..., description="P(disease)")
    model_name: str


class BatchRequest(BaseModel):
    records: List[PatientFeatures]


# ----------------------------------------------------------------------------
# App + model loading
# ----------------------------------------------------------------------------
_model = None
_feature_order = DEFAULT_FEATURE_ORDER
_model_name = "unknown"


def load_model() -> None:
    global _model, _feature_order, _model_name
    if not MODEL_PATH.exists():
        logger.error(json.dumps({"event": "model_missing", "path": str(MODEL_PATH)}))
        return
    _model = joblib.load(MODEL_PATH)
    if SCHEMA_PATH.exists():
        schema = json.loads(SCHEMA_PATH.read_text())
        _feature_order = schema.get("all_features", DEFAULT_FEATURE_ORDER)
    if META_PATH.exists():
        _model_name = json.loads(META_PATH.read_text()).get("best_model", "unknown")
    logger.info(json.dumps({"event": "model_loaded", "model": _model_name,
                            "n_features": len(_feature_order)}))


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


app = FastAPI(
    title="Heart Disease Risk Prediction API",
    description="Predicts heart-disease risk from patient clinical features.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    REQ_COUNTER.labels(endpoint="/", status="200").inc()
    return {
        "service": "Heart Disease Risk Prediction API",
        "version": "1.0.0",
        "model": _model_name,
        "model_loaded": _model is not None,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    ok = _model is not None
    status = "200" if ok else "503"
    REQ_COUNTER.labels(endpoint="/health", status=status).inc()
    payload = {"status": "healthy" if ok else "unhealthy", "model_loaded": ok}
    return JSONResponse(payload, status_code=200 if ok else 503)


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _predict_df(df: pd.DataFrame) -> list[dict]:
    df = df[_feature_order]
    preds = _model.predict(df)
    probs = _model.predict_proba(df)
    out = []
    for pred, prob in zip(preds, probs):
        p_disease = float(prob[1])
        confidence = float(max(prob))
        out.append({
            "prediction": int(pred),
            "label": "Heart disease" if int(pred) == 1 else "No heart disease",
            "confidence": round(confidence, 4),
            "probability_disease": round(p_disease, 4),
            "model_name": _model_name,
        })
    return out


@app.post("/predict", response_model=PredictionResponse)
def predict(features: PatientFeatures):
    if _model is None:
        REQ_COUNTER.labels(endpoint="/predict", status="503").inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    start = time.perf_counter()
    df = pd.DataFrame([features.model_dump()])
    result = _predict_df(df)[0]
    elapsed = time.perf_counter() - start

    LATENCY.observe(elapsed)
    PRED_COUNTER.labels(outcome=result["label"]).inc()
    REQ_COUNTER.labels(endpoint="/predict", status="200").inc()
    logger.info(json.dumps({
        "event": "prediction", "input": features.model_dump(),
        "prediction": result["prediction"],
        "probability_disease": result["probability_disease"],
        "latency_ms": round(elapsed * 1000, 2),
    }))
    return result


@app.post("/predict/batch")
def predict_batch(req: BatchRequest):
    if _model is None:
        REQ_COUNTER.labels(endpoint="/predict/batch", status="503").inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    start = time.perf_counter()
    df = pd.DataFrame([r.model_dump() for r in req.records])
    results = _predict_df(df)
    elapsed = time.perf_counter() - start
    LATENCY.observe(elapsed)
    for r in results:
        PRED_COUNTER.labels(outcome=r["label"]).inc()
    REQ_COUNTER.labels(endpoint="/predict/batch", status="200").inc()
    logger.info(json.dumps({"event": "batch_prediction",
                            "n": len(results),
                            "latency_ms": round(elapsed * 1000, 2)}))
    return {"count": len(results), "predictions": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
