# Observability

This document describes the observability features available in X Agent, including distributed tracing with OpenTelemetry and log correlation.

## Overview

X Agent supports optional distributed tracing using OpenTelemetry with W3C TraceContext propagation. Tracing is **disabled by default** and requires explicit opt-in via environment variables.

### Features

- **Disabled by default**: No external dependencies or network calls unless explicitly enabled
- **Optional installation**: Telemetry packages are optional extras (`pip install -e .[telemetry]`)
- **W3C TraceContext**: Standards-compliant trace propagation
- **Log correlation**: Automatic injection of `trace_id` and `span_id` into structured logs
- **Flexible exporters**: Console output (default) or OTLP HTTP endpoint for production
- **Hermetic testing**: In-memory exporters for unit tests (no network calls)

## Quick Start

### 1. Install telemetry extras (optional)

```bash
pip install -e .[telemetry]
```

This installs:

- `opentelemetry-api>=1.26`
- `opentelemetry-sdk>=1.26`
- `opentelemetry-exporter-otlp-proto-http>=1.26`

### 2. Enable telemetry

Set environment variable:

```bash
export ENABLE_TELEMETRY=true
```

Or in `.env`:

```ini
ENABLE_TELEMETRY=true
```

### 3. Initialize tracing in your application

```python
from src.telemetry import init_telemetry
from src.logging_setup import attach_tracecontext_to_logs
import logging

# Initialize telemetry early in startup
init_telemetry()

# Configure log correlation
attach_tracecontext_to_logs(logging.getLogger())

# Now traces and logs are correlated
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_TELEMETRY` | `false` | Set to `true` to enable tracing |
| `OTEL_SERVICE_NAME` | `x-agent` | Service name for traces |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | None | OTLP HTTP endpoint URL (e.g., `http://localhost:4318/v1/traces`) |
| `OTEL_TRACES_SAMPLER` | `parentbased_always_on` | Sampling strategy (`always_on`, `parentbased_always_on`, `parentbased_traceidratio/0.1`) |

## Usage Examples

### Creating spans manually

```python
from src.telemetry import get_tracer

tracer = get_tracer(__name__)

with tracer.start_as_current_span("process_request") as span:
    span.set_attribute("user.id", user_id)
    span.set_attribute("request.type", "post")

    # Your code here
    result = process_data()

    span.set_attribute("result.count", len(result))
```

### Instrumenting scheduler iterations

```python
from src.telemetry import get_tracer

tracer = get_tracer("scheduler")

def run_iteration():
    with tracer.start_as_current_span("scheduler.iteration") as span:
        span.set_attribute("iteration.timestamp", datetime.utcnow().isoformat())

        # Schedule and execute actions
        actions = scheduler.get_due_actions()
        span.set_attribute("actions.count", len(actions))

        for action in actions:
            execute_action(action)
```

### Instrumenting API calls

```python
from src.telemetry import get_tracer

tracer = get_tracer("x_client")

def post_tweet(text: str):
    with tracer.start_as_current_span("x_api.post_tweet") as span:
        span.set_attribute("tweet.length", len(text))

        try:
            response = api_client.post(text)
            span.set_attribute("response.status", response.status_code)
            return response
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(e).__name__)
            raise
```

### Log correlation

When a span is active, log records automatically include `trace_id` and `span_id`:

```python
import logging
from src.logging_setup import attach_tracecontext_to_logs
from src.telemetry import get_tracer

attach_tracecontext_to_logs(logging.getLogger())
logger = logging.getLogger(__name__)

tracer = get_tracer(__name__)

with tracer.start_as_current_span("operation"):
    logger.info("Processing started")
    # Log output: ... Processing started [trace_id=a1b2c3... span_id=d4e5f6...]
```

## Deployment Scenarios

### Local development (console exporter)

Default when `ENABLE_TELEMETRY=true` and no OTLP endpoint is configured:

```bash
export ENABLE_TELEMETRY=true
python src/main.py
```

Traces are printed to console for debugging.

### Production (OTLP exporter)

Point to an OTLP HTTP endpoint (e.g., Jaeger, Zipkin, or a vendor collector):

```bash
export ENABLE_TELEMETRY=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4318/v1/traces
export OTEL_SERVICE_NAME=x-agent-prod
export OTEL_TRACES_SAMPLER=parentbased_traceidratio/0.1  # Sample 10% of traces
python src/main.py
```

### CI/Testing (disabled)

Telemetry is disabled by default, so no changes are needed for CI environments:

```bash
pytest  # Telemetry is off; tests run without external dependencies
```

To test telemetry features in unit tests, use in-memory exporters (see `tests/test_telemetry.py`).

## Sampling Strategies

- `always_on`: Sample all traces (high volume, useful for debugging)
- `parentbased_always_on`: Respect parent span sampling decision; sample all root spans
- `parentbased_traceidratio/0.1`: Respect parent decision; sample 10% of root spans (production default)

## Trace Context Format (W3C)

Trace IDs and span IDs follow the [W3C Trace Context](https://www.w3.org/TR/trace-context/) specification:

- **trace_id**: 32-character hex string (128 bits)
- **span_id**: 16-character hex string (64 bits)

Example log output:

```
2025-11-02 10:30:15 - x_client - INFO - Posted tweet [trace_id=4bf92f3577b34da6a3ce929d0e0e4736 span_id=00f067aa0ba902b7]
```

## Troubleshooting

### Telemetry not starting

**Symptom**: Logs show "Telemetry disabled" even with `ENABLE_TELEMETRY=true`

**Solution**:

1. Verify environment variable is set: `echo $ENABLE_TELEMETRY`
2. Install telemetry extras: `pip install -e .[telemetry]`
3. Check logs for import errors

### No traces visible

**Symptom**: Spans created but not visible in backend

**Solution**:

1. Verify `OTEL_EXPORTER_OTLP_ENDPOINT` is correct
2. Check network connectivity to collector
3. Verify collector is configured to receive HTTP (not gRPC)
4. Increase sampling rate: `OTEL_TRACES_SAMPLER=always_on`

### Log correlation not working

**Symptom**: Logs missing `trace_id` / `span_id`

**Solution**:

1. Ensure `attach_tracecontext_to_logs()` is called early
2. Verify a span is active when logging: `with tracer.start_as_current_span(...)`
3. Check telemetry is enabled: `from src.telemetry import is_telemetry_enabled; print(is_telemetry_enabled())`

## Performance Considerations

- **Disabled**: Zero overhead; no imports or initialization when `ENABLE_TELEMETRY=false`
- **Enabled (console)**: Minimal overhead; spans printed synchronously
- **Enabled (OTLP)**: Spans batched and sent asynchronously; ~1-2% CPU overhead
- **Sampling**: Use `parentbased_traceidratio` in production to reduce volume

## Further Reading

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/languages/python/)
- [W3C Trace Context Specification](https://www.w3.org/TR/trace-context/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
