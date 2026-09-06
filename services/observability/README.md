# Observability Stack

Prometheus and Grafana for monitoring Folium services.

## Services

- **Prometheus**: Metrics collection and storage
  - URL: http://localhost:9090
  - Scrapes metrics from backend, transcription, summarization, and Temporal services

- **Grafana**: Metrics visualization and dashboards
  - URL: http://localhost:3001
  - Default credentials: `admin` / `admin`
  - Pre-configured Prometheus datasource

## Usage

Start the observability stack with the main docker-compose:

```bash
docker compose up folium-prometheus folium-grafana folium-loki
```

Or start all services:

```bash
docker compose up
```

Promtail is intentionally excluded from normal local startup because it mounts
the Docker socket. Start it only on Docker hosts that explicitly permit
`grafana/promtail:3.6.8` to mount that socket:

```bash
docker compose --profile observability up --detach folium-promtail
```

## Adding Metrics to Services

### FastAPI (Backend, Transcription, Summarization)

Install prometheus client:

```bash
uv add prometheus-client
```

Add to your FastAPI app:

```python
from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Dashboard Examples

Check the `provisioning/dashboards/` directory for pre-configured dashboards.

## Configuration

- `prometheus.yml`: Scrape configuration
- `provisioning/datasources/`: Grafana datasource configuration
- `provisioning/dashboards/`: Dashboard provisioning configuration

### Temporal Metrics Policy

Temporal is scraped once per minute with a post-relabel sample limit of 1,000.
Prometheus retains workflow completion/timeout, request/error, task-queue
backlog/lag, worker and poller capacity, and request-latency count/sum signals.
All other Temporal metric families are dropped before storage, along with
deployment-specific or unbounded labels such as worker build, partition,
namespace ID, workflow ID, and run ID.

The service-health dashboard uses `workflow_success` for workflow completions
and `service_errors` for request errors. Temporal's local endpoint does not
currently emit a `workflow_failed` metric.
