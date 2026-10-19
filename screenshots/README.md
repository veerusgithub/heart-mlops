# Screenshots for the report

Capture these while running the pipeline on your machine and drop the PNGs here,
then reference them in the report / submission.

| Suggested filename | What to capture | Command to produce it |
|--------------------|-----------------|-----------------------|
| `01_training_run.png` | Training console output with metrics | `python src/train.py --data data/heart_raw.csv` |
| `02_mlflow_ui.png` | MLflow UI comparing the two runs | `mlflow ui --backend-store-uri sqlite:///mlflow.db` → open :5000 |
| `03_pytest.png` | All tests passing | `make test` |
| `04_github_actions.png` | Green CI pipeline on GitHub | Push to GitHub → Actions tab |
| `05_docker_build.png` | Successful image build | `docker build -t heart-api:latest .` |
| `06_docker_run_curl.png` | Container serving `/predict` | `docker run -p 8000:8000 heart-api:latest` + curl |
| `07_swagger_docs.png` | FastAPI Swagger UI | open `http://localhost:8000/docs` |
| `08_k8s_pods.png` | Pods running | `kubectl get pods,svc` |
| `09_k8s_service_url.png` | Service URL / endpoint test | `minikube service heart-api-service --url` |
| `10_grafana.png` | Grafana dashboard with live metrics | compose stack → open :3000 |
| `11_prometheus_targets.png` | Prometheus scraping the API | open `http://localhost:9090/targets` |

Already included: `live_api_proof.txt` — real curl requests/responses captured
against a running uvicorn server during development.
