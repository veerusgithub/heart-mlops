.PHONY: help install data eda train test lint serve docker-build docker-run \
        compose-up compose-down k8s-deploy mlflow-ui clean all

help:
	@echo "Targets:"
	@echo "  install       pip install -r requirements.txt"
	@echo "  data          download the dataset"
	@echo "  eda           run EDA + generate figures"
	@echo "  train         train models, tune, log to MLflow, save best"
	@echo "  test          run pytest"
	@echo "  lint          run flake8"
	@echo "  serve         run the FastAPI app locally (uvicorn)"
	@echo "  docker-build  build the serving image"
	@echo "  docker-run    run the serving container on :8000"
	@echo "  compose-up    API + Prometheus + Grafana via docker compose"
	@echo "  k8s-deploy    apply the Kubernetes manifests"
	@echo "  mlflow-ui     launch the MLflow tracking UI"
	@echo "  all           data -> eda -> train -> test"

install:
	pip install -r requirements.txt

data:
	python src/download_data.py --out data/heart_raw.csv

eda: data
	python src/eda.py --data data/heart_raw.csv --outdir reports/figures

train: data
	python src/train.py --data data/heart_raw.csv

test:
	python -m pytest tests/ -v

lint:
	flake8 src app.py tests --max-line-length=100 --select=E9,F63,F7,F82 --show-source

serve:
	uvicorn app:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t heart-api:latest .

docker-run:
	docker run --rm -p 8000:8000 heart-api:latest

compose-up:
	docker compose -f monitoring/docker-compose.monitoring.yml up --build

compose-down:
	docker compose -f monitoring/docker-compose.monitoring.yml down

k8s-deploy:
	kubectl apply -f deployment/

mlflow-ui:
	mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__ .pytest_cache \
	       mlruns mlflow.db

all: data eda train test
