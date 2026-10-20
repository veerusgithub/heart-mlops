# ---------------------------------------------------------------------------
# Multi-stage build for the Heart Disease Risk Prediction API (FastAPI).
# Stage 1 installs dependencies into a venv; stage 2 is a slim runtime image.
# ---------------------------------------------------------------------------

FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt


# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_DIR=/app/model_artifacts

# copy the prepared virtualenv
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# application code + trained artifacts + shared preprocessing module
COPY app.py ./
COPY src/ ./src/
COPY model_artifacts/ ./model_artifacts/

# make src importable (for any pickled references) and run as non-root
ENV PYTHONPATH="/app:/app/src"
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# container-level health check hits the API's /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys,os; \
    sys.exit(0 if urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8000)}/health').status==200 else 1)"

CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
