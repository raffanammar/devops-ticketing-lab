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
- Docker Compose orchestration
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

The application stack is orchestrated using Docker Compose.

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
