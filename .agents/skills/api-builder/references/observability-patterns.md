# API Observability Patterns

> Comprehensive observability patterns for logs, traces, metrics, and health checks.

## Three Pillars of Observability

```
┌─────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY                           │
├───────────────────┬──────────────────┬─────────────────────┤
│       LOGS        │      TRACES      │      METRICS        │
├───────────────────┼──────────────────┼─────────────────────┤
│ What happened     │ Request flow     │ System health       │
│ Error details     │ Latency breakdown│ Performance trends  │
│ Audit trail       │ Service deps     │ Business KPIs       │
└───────────────────┴──────────────────┴─────────────────────┘
```

---

## Structured Logging

### structlog Configuration

```python
import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level

def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_log_level,
            TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Usage
logger = structlog.get_logger()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    
    # Bind context for all logs in this request
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        logger.error(
            "request_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

### Log Output Format

```json
{
  "event": "request_completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "path": "/api/users/123",
  "status_code": 200,
  "duration_ms": 45.23,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info"
}
```

---

## Distributed Tracing

### OpenTelemetry Setup

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_tracing(app: FastAPI):
    # Configure tracer provider
    provider = TracerProvider()
    
    # Add OTLP exporter (Jaeger, Tempo, etc.)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    trace.set_tracer_provider(provider)
    
    # Auto-instrument
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    HTTPXClientInstrumentor().instrument()

# Manual tracing
tracer = trace.get_tracer(__name__)

async def complex_operation(user_id: int):
    with tracer.start_as_current_span("complex_operation") as span:
        span.set_attribute("user.id", user_id)
        
        # Child span
        with tracer.start_as_current_span("fetch_user"):
            user = await user_service.get(user_id)
        
        with tracer.start_as_current_span("process_data"):
            result = await process_user_data(user)
        
        span.set_attribute("result.items", len(result))
        return result
```

### Trace Context Propagation

```python
from opentelemetry.propagate import inject, extract
import httpx

async def call_external_service(data: dict):
    headers = {}
    inject(headers)  # Inject trace context
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://external-service.com/api",
            json=data,
            headers=headers
        )
    return response.json()
```

---

## Metrics Collection

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Define metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Active HTTP requests"
)

DB_POOL_SIZE = Gauge(
    "db_pool_connections",
    "Database connection pool size",
    ["state"]  # active, idle
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    ACTIVE_REQUESTS.inc()
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        return response
    finally:
        ACTIVE_REQUESTS.dec()

@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

### Business Metrics

```python
# Custom business metrics
USER_SIGNUPS = Counter(
    "user_signups_total",
    "Total user signups",
    ["plan", "source"]
)

ORDER_VALUE = Histogram(
    "order_value_dollars",
    "Order value in dollars",
    buckets=[10, 25, 50, 100, 250, 500, 1000]
)

ACTIVE_SUBSCRIPTIONS = Gauge(
    "active_subscriptions",
    "Active subscriptions by plan",
    ["plan"]
)

# Record business events
async def create_user(data: UserCreate):
    user = await user_service.create(data)
    
    USER_SIGNUPS.labels(
        plan=user.plan,
        source=data.source or "direct"
    ).inc()
    
    return user
```

---

## Health Checks

### Comprehensive Health Endpoint

```python
from enum import Enum
from pydantic import BaseModel
from typing import Dict

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck(BaseModel):
    status: HealthStatus
    checks: Dict[str, Dict]
    version: str
    uptime_seconds: float

async def check_database() -> dict:
    try:
        start = time.time()
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "latency_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_redis() -> dict:
    try:
        start = time.time()
        await redis.ping()
        return {
            "status": "healthy",
            "latency_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_external_api() -> dict:
    try:
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.external.com/health",
                timeout=5.0
            )
        return {
            "status": "healthy" if response.status_code == 200 else "degraded",
            "latency_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/health", response_model=HealthCheck)
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "external_api": await check_external_api(),
    }
    
    # Determine overall status
    if all(c["status"] == "healthy" for c in checks.values()):
        status = HealthStatus.HEALTHY
    elif any(c["status"] == "unhealthy" for c in checks.values()):
        status = HealthStatus.UNHEALTHY
    else:
        status = HealthStatus.DEGRADED
    
    return HealthCheck(
        status=status,
        checks=checks,
        version=settings.APP_VERSION,
        uptime_seconds=time.time() - app.state.start_time
    )

# Kubernetes probes
@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe."""
    return {"status": "alive", "pid": os.getpid()}

@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe."""
    db_ok = (await check_database())["status"] == "healthy"
    redis_ok = (await check_redis())["status"] == "healthy"
    
    if db_ok and redis_ok:
        return {"status": "ready"}
    
    raise HTTPException(status_code=503, detail="Not ready")
```

---

## Error Tracking

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def setup_sentry():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=settings.APP_VERSION,
        traces_sample_rate=0.1,  # 10% of requests
        profiles_sample_rate=0.1,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        before_send=filter_sensitive_data,
    )

def filter_sensitive_data(event, hint):
    """Remove sensitive data before sending to Sentry."""
    if "request" in event:
        headers = event["request"].get("headers", {})
        if "Authorization" in headers:
            headers["Authorization"] = "[FILTERED]"
        if "X-API-Key" in headers:
            headers["X-API-Key"] = "[FILTERED]"
    return event

# Manual error capture with context
async def process_payment(order_id: int):
    try:
        result = await payment_service.charge(order_id)
    except PaymentError as e:
        sentry_sdk.set_context("payment", {
            "order_id": order_id,
            "amount": e.amount,
            "provider": e.provider
        })
        sentry_sdk.capture_exception(e)
        raise
```

---

## Alerting Rules

### Prometheus Alerting

```yaml
# prometheus/alerts.yml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) 
          / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate (> 5%)"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, 
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 1.0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High latency (p95 > 1s)"
          description: "95th percentile latency is {{ $value | humanizeDuration }}"
      
      - alert: DatabaseConnectionsExhausted
        expr: db_pool_connections{state="idle"} < 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly exhausted"
```

---

## Dashboard Queries

### Grafana Dashboard Panels

```promql
# Request Rate
sum(rate(http_requests_total[5m])) by (endpoint)

# Error Rate %
100 * sum(rate(http_requests_total{status=~"5.."}[5m])) 
    / sum(rate(http_requests_total[5m]))

# Latency P50/P95/P99
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Active Connections
db_pool_connections{state="active"}

# Request Duration Heatmap
sum by (le) (increase(http_request_duration_seconds_bucket[1m]))
```
