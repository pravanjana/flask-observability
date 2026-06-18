# Flask Observability Stack

A full observability pipeline for a Flask application — structured logging, metrics, alerting, and Kubernetes monitoring.

## Architecture

Flask app (JSON logs + /metrics)

├── Promtail → Loki → Grafana (logs)

└── Prometheus → Grafana (metrics + alerts)

## Stack

| Component | Role |
|---|---|
| Flask | Application with structured JSON logging |
| prometheus-client | Custom metrics instrumentation |
| Promtail | Log collection from Docker containers |
| Loki | Log aggregation and storage |
| Prometheus | Metrics scraping and alerting |
| Grafana | Dashboards and alert management |
| Helm | Kubernetes deployment (kube-prometheus-stack) |
| GKE | Production Kubernetes cluster |

**Logging** — every request emits structured JSON with timestamp, level, path, method, status code, and latency.

**Metrics** — four custom Prometheus metrics:
- `flask_request_total` — request count by endpoint and status
- `flask_request_duration_seconds` — latency histogram with p50/p95/p99
- `flask_active_requests` — live gauge of in-flight requests
- `flask_error_total` — error count by endpoint

**Alerting** — two alert rules:
- `HighErrorRate` — fires when error rate exceeds 5% for 1 minute
- `HighLatency` — fires when p99 latency exceeds 1 second for 2 minutes

## Run locally

```bash
docker-compose up -d
```

Services:
- Flask app → http://localhost:5001
- Grafana → http://localhost:3000
- Prometheus → http://localhost:9090
- Loki → http://localhost:3100

## Deploy to Kubernetes

```bash
gcloud container clusters create flask-cluster \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type e2-small

kubectl create namespace flask-prod
kubectl apply -f k8s/

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring
```

## Dashboard

The RED method dashboard shows:
- Request rate by endpoint
- Error rate by endpoint
- p99 latency by endpoint
- Active requests (live gauge)
- Total error count
- Flask application logs

EOF
