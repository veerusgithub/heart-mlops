"""Unit/integration tests for the FastAPI serving app and model inference."""
import sys
import warnings
from pathlib import Path

import pytest

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

import app as appmod  # noqa: E402

MODEL_AVAILABLE = (ROOT / "model_artifacts" / "model.joblib").exists()

# Two real patients from processed.cleveland.data (raw UCI encodings):
#   row 223 (label 0 - no disease) and row 192 (label 2 -> target 1).
# Used as smoke-test inputs; they are NOT a measure of accuracy.
LOW_RISK = {
    "age": 39, "sex": 0, "cp": 3, "trestbps": 94, "chol": 199, "fbs": 0,
    "restecg": 0, "thalach": 179, "exang": 0, "oldpeak": 0.0, "slope": 1,
    "ca": 0, "thal": 3,
}
HIGH_RISK = {
    "age": 51, "sex": 1, "cp": 4, "trestbps": 140, "chol": 298, "fbs": 0,
    "restecg": 0, "thalach": 122, "exang": 1, "oldpeak": 4.2, "slope": 2,
    "ca": 3, "thal": 7,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(appmod.app) as c:
        yield c


def test_root_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "model" in r.json()


def test_health(client):
    r = client.get("/health")
    assert r.status_code in (200, 503)
    assert "model_loaded" in r.json()


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "heart_requests_total" in r.text


@pytest.mark.skipif(not MODEL_AVAILABLE, reason="model artifact not trained")
def test_predict_schema(client):
    r = client.post("/predict", json=HIGH_RISK)
    assert r.status_code == 200
    body = r.json()
    for key in ("prediction", "label", "confidence", "probability_disease"):
        assert key in body
    assert body["prediction"] in (0, 1)
    assert 0.0 <= body["confidence"] <= 1.0
    assert 0.0 <= body["probability_disease"] <= 1.0


@pytest.mark.skipif(not MODEL_AVAILABLE, reason="model artifact not trained")
def test_predict_known_cases(client):
    """Sanity: a clearly low-risk vs high-risk record separate correctly."""
    low = client.post("/predict", json=LOW_RISK).json()
    high = client.post("/predict", json=HIGH_RISK).json()
    assert low["probability_disease"] < high["probability_disease"]
    assert low["prediction"] == 0
    assert high["prediction"] == 1


@pytest.mark.skipif(not MODEL_AVAILABLE, reason="model artifact not trained")
def test_batch_predict(client):
    r = client.post("/predict/batch", json={"records": [LOW_RISK, HIGH_RISK]})
    assert r.status_code == 200
    assert r.json()["count"] == 2


def test_validation_rejects_out_of_range(client):
    bad = dict(LOW_RISK)
    bad["age"] = 999  # out of [0,120]
    r = client.post("/predict", json=bad)
    assert r.status_code == 422


def test_validation_rejects_missing_field(client):
    bad = dict(LOW_RISK)
    del bad["chol"]
    r = client.post("/predict", json=bad)
    assert r.status_code == 422


@pytest.mark.parametrize("field,value", [
    ("cp", 0),      # UCI chest-pain codes are 1-4
    ("cp", 5),
    ("slope", 0),   # UCI slope codes are 1-3
    ("ca", 4),      # fluoroscopy vessel count is 0-3
    ("thal", 2),    # UCI thal codes are only 3 / 6 / 7
    ("thal", 5),
])
def test_validation_rejects_invalid_uci_codes(client, field, value):
    bad = dict(LOW_RISK)
    bad[field] = value
    assert client.post("/predict", json=bad).status_code == 422


@pytest.mark.parametrize("thal", [3, 6, 7])
def test_validation_accepts_all_valid_thal_codes(client, thal):
    ok = dict(LOW_RISK)
    ok["thal"] = thal
    r = client.post("/predict", json=ok)
    assert r.status_code in (200, 503)   # 503 only if model not trained


def test_sample_files_are_valid_requests(client):
    import json
    single = json.loads((ROOT / "samples" / "patient.json").read_text())
    batch = json.loads((ROOT / "samples" / "patients_batch.json").read_text())
    for rec in [single, *batch]:
        r = client.post("/predict", json=rec)
        assert r.status_code in (200, 503), r.text
