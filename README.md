# DevOps Ticketing Lab

A production-style DevOps and Application Support portfolio project built to demonstrate troubleshooting, containerization, CI/CD, security scanning, observability, alerting, and incident simulation.

## Project Overview

This project simulates a production ticketing service and the operational practices commonly used by Application Support, Cloud Support, DevOps, and SRE teams.

The application provides a REST API for ticket management and runs as a containerized multi-service environment with automated testing, CI/CD, monitoring, dashboards, and alerting.

## Architecture

The environment consists of:

- Flask REST API
- PostgreSQL database
- Nginx reverse proxy
- Prometheus monitoring
- Grafana dashboards
- Alertmanager
- Webhook alert receiver
- Docker Compose orchestration (monitoring stack)
- Kubernetes (kind) orchestration (application stack)
- GitHub Actions CI/CD

Request flow:

```text
Client
  |
  v
Nginx
  |
  v
Flask API
  |
  v
PostgreSQL

Flask /metrics
  |
  v
Prometheus
  |
  +----> Grafana
  |
  v
Alertmanager
  |
  v
Webhook Receiver
```

## Application Features

The Flask application currently provides:

- `GET /health` - application health check
- `POST /tickets` - create a ticket
- `GET /tickets` - list tickets
- `GET /metrics` - Prometheus metrics
- `GET /simulate/slow` - simulate a slow response for local incident testing

The `/simulate/slow` endpoint is included for lab purposes to generate controlled latency during alert testing.

## Containerized Environment

The application stack runs in Docker containers. The local Kubernetes (kind) setup
is described in [Kubernetes Deployment](#kubernetes-deployment-local-kind);
Docker Compose is still used to orchestrate the monitoring stack below.

Main services:

| Service          | Purpose                                 |
| ---------------- | --------------------------------------- |
| Nginx            | Reverse proxy                           |
| Flask App        | Ticketing REST API                      |
| PostgreSQL       | Application database                    |
| Prometheus       | Metrics collection and alert evaluation |
| Grafana          | Metrics visualization                   |
| Alertmanager     | Alert routing and lifecycle management  |
| Webhook Receiver | Local alert notification receiver       |

## Kubernetes Deployment (Local, kind)

The application stack (Nginx, Flask API, PostgreSQL) also runs on a local Kubernetes
cluster created with [kind](https://kind.sigs.k8s.io/) (Kubernetes v1.31.0), deployed
declaratively from manifests under `k8s/base/`.

The observability stack (Prometheus, Grafana, Alertmanager) still runs on Docker Compose;
migrating it to Kubernetes is planned as a follow-up.

### Kubernetes Architecture

All resources live in the namespace `ticketing-lab`.

```text
Client (kubectl port-forward 8080:80)
  |
  v
Nginx Pod (Service: NodePort 30080)
  |  reverse proxy config mounted from ConfigMap
  v
Flask App Pod (Deployment + Service)
  |
  v
PostgreSQL Pod (Deployment + Service)
  |
  +--> PersistentVolumeClaim (database data)
  +--> Secret (database credentials)
```

### Kubernetes Components

| Manifest              | Kind                  | Purpose                                          |
| --------------------- | --------------------- | ------------------------------------------------ |
| db-secret.yaml        | Secret                | PostgreSQL credentials                           |
| db-pvc.yaml           | PersistentVolumeClaim | Durable storage for the database                 |
| db-deployment.yaml    | Deployment + Service  | PostgreSQL pod + cluster-internal access         |
| app-deployment.yaml   | Deployment + Service  | Flask API pod + cluster-internal access          |
| nginx-deployment.yaml | Deployment + Service  | Reverse proxy, exposed as NodePort 30080         |
| nginx-config.yaml     | ConfigMap             | Nginx config, mounted via volumeMounts + subPath |

### Prerequisites

- kind
- kubectl
- Docker Desktop running

### Deploy to kind

Build the application image:

```bash
docker build -t devops-ticketing-lab-app:latest .
```

Create the cluster and load the image into it:

```bash
kind create cluster --name ticketing-lab
kind load docker-image devops-ticketing-lab-app:latest --name ticketing-lab
```

The kind node runs its own container runtime and does not share images with Docker
Desktop, so the image must be loaded into the cluster explicitly. The app deployment
uses `imagePullPolicy: Never` so Kubernetes never attempts a registry pull.

Apply all manifests:

```bash
kubectl apply -f k8s/base/
```

Watch the rollout:

```bash
kubectl get pods -n ticketing-lab
```

### Verify the Deployment

Expose the app on localhost:

```bash
kubectl port-forward svc/nginx 8080:80 -n ticketing-lab
```

In a second terminal:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/tickets
```

Both endpoints must respond through the full chain (Nginx -> Flask -> PostgreSQL)
without any change to application code or configuration.

### Self-Healing Demonstration

Delete the Flask app pod to simulate a sudden workload failure:

```bash
kubectl get pods -n ticketing-lab
kubectl delete pod <app-pod-name> -n ticketing-lab --force --grace-period=0
```

The Deployment's ReplicaSet immediately reconciles actual state toward the desired
state and starts a replacement pod:

```bash
kubectl get pods -n ticketing-lab -w
```

The API stays reachable through the same endpoint after the new pod is ready — no
manual restart, no configuration change. `--force --grace-period=0` removes the pod
instantly, simulating abrupt node loss rather than a graceful shutdown.

### Cleanup

```bash
kind delete cluster --name ticketing-lab
```

The database PVC lives inside the kind cluster, so deleting the cluster also removes
its data — expected behavior for a local lab cluster.

## Automated Testing

The project uses `pytest` with an isolated SQLite in-memory database for application tests.

Current test coverage includes:

- Health check
- Successful ticket creation
- Missing ticket title validation
- Ticket listing

Run tests with:

```bash
pytest -v
```

## CI/CD Pipeline

GitHub Actions automatically validates changes pushed to the repository and pull requests targeting the main branch.

The pipeline includes:

1. Python dependency installation
2. Automated pytest execution
3. Docker image build
4. Container startup
5. Application health smoke test
6. Security vulnerability scanning with `pip-audit`
7. Container cleanup

The smoke test verifies the deployed container through the Nginx endpoint.

## Observability

Prometheus collects application metrics exposed by `prometheus-flask-exporter`.

Grafana is provisioned automatically and provides visibility into:

- Total HTTP requests
- HTTP request rate
- HTTP status codes
- HTTP error rate
- Average response time

Prometheus is available locally on port `9090`.

Grafana is available locally on port `3001`.

## Alerting

Prometheus alert rules are managed as configuration-as-code under:

```text
monitoring/prometheus/rules/
```

Alertmanager receives firing alerts from Prometheus and forwards notifications to the local webhook receiver.

Configured alerts:

| Alert            | Condition                                                            | Severity |
| ---------------- | -------------------------------------------------------------------- | -------- |
| ApplicationDown  | Flask application cannot be scraped for more than 1 minute           | Critical |
| HighErrorRate    | More than 20% of HTTP requests return 4xx/5xx for more than 1 minute | Warning  |
| HighResponseTime | HTTP p95 response time exceeds 500 ms for more than 1 minute         | Warning  |

The alert lifecycle tested in this lab is:

```text
Normal
  |
  v
Threshold exceeded
  |
  v
Pending
  |
  v
Firing
  |
  v
Alertmanager
  |
  v
Webhook notification
  |
  v
Condition recovered
  |
  v
Resolved notification
```

## Incident Simulation

The monitoring stack has been validated using controlled incident scenarios.

### Application Down

The Flask application container is stopped to simulate service unavailability.

Expected result:

```text
ApplicationDown -> pending -> firing -> resolved
```

### High Error Rate

Continuous requests to a non-existent endpoint generate HTTP `404` responses and increase the HTTP error rate above the configured threshold.

Expected result:

```text
HighErrorRate -> pending -> firing -> resolved
```

### High Response Time

The lab-only `/simulate/slow` endpoint intentionally delays responses by approximately one second.

Prometheus calculates p95 latency from the HTTP request duration histogram.

Expected result:

```text
HighResponseTime -> pending -> firing -> resolved
```

## Local Ports

| Service               | Port |
| --------------------- | ---: |
| Application via Nginx |   80 |
| Prometheus            | 9090 |
| Grafana               | 3001 |
| Alertmanager          | 9093 |
| Webhook Receiver      | 5001 |

## Run Locally

Start the environment:

```bash
docker compose up -d --build
```

Check running containers:

```bash
docker compose ps
```

Verify the application:

```bash
curl http://localhost/health
```

Run automated tests:

```bash
pytest -v
```

Stop the environment:

```bash
docker compose down
```

## Skills Demonstrated

This project demonstrates hands-on experience with:

- Linux
- Git and GitHub workflow
- Python and Flask
- REST API troubleshooting
- PostgreSQL
- SQLAlchemy
- Docker and Docker Compose
- Kubernetes (kind, kubectl)
- Nginx
- Automated testing with pytest
- GitHub Actions CI/CD
- Dependency vulnerability scanning
- Prometheus
- PromQL
- Grafana
- Alertmanager
- Metrics-based incident detection
- Incident simulation and recovery validation

## Repository Workflow

Development follows a feature branch workflow:

```text
Feature Branch
      |
      v
Local Development
      |
      v
Testing
      |
      v
Commit
      |
      v
Push
      |
      v
GitHub Actions
      |
      v
Pull Request
      |
      v
Main
```
