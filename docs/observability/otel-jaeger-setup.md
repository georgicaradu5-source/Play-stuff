# OpenTelemetry + Jaeger Setup Guide

Complete guide for deploying production observability with OpenTelemetry Collector and Jaeger for X Agent Unified.

---

## Architecture Overview

```
X Agent → OpenTelemetry SDK → OTLP/HTTP → OTel Collector → Jaeger Backend → Jaeger UI
         (src/telemetry.py)              (localhost:4318) (processing)   (storage)    (query)
```

**Components:**
1. **X Agent** - Application instrumented with OpenTelemetry SDK
2. **OTel Collector** - Receives, processes, and exports traces
3. **Jaeger** - Distributed tracing backend and UI
4. **Alerting** - Quota/rate limit monitoring (optional)

---

## Prerequisites

- Docker + Docker Compose (recommended) OR manual installation
- X Agent installed with telemetry extras: `pip install -e .[telemetry]`
- Ports available: 4318 (OTLP), 16686 (Jaeger UI), 14250 (Jaeger gRPC)

---

## Quick Start: Docker Compose

### 1. Create docker-compose.yml

```yaml
version: '3.8'

services:
  # Jaeger all-in-one (backend + UI)
  jaeger:
    image: jaegertracing/all-in-one:1.51
    container_name: jaeger
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"  # Jaeger UI
      - "14250:14250"  # Jaeger gRPC
    networks:
      - observability

  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.91.0
    container_name: otel-collector
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4318:4318"    # OTLP HTTP receiver
      - "8888:8888"    # Prometheus metrics (collector health)
    depends_on:
      - jaeger
    networks:
      - observability

networks:
  observability:
    driver: bridge
```

### 2. Create otel-collector-config.yaml

```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

  # Add resource attributes
  resource:
    attributes:
      - key: deployment.environment
        value: production
        action: insert

exporters:
  # Export to Jaeger
  otlp:
    endpoint: jaeger:4317
    tls:
      insecure: true

  # Debug logging (optional, disable in production)
  logging:
    loglevel: info

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp, logging]
```

### 3. Start Services

```bash
# Start Jaeger + OTel Collector
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f otel-collector
docker-compose logs -f jaeger
```

### 4. Configure X Agent

Update `.env`:

```bash
# Enable telemetry
ENABLE_TELEMETRY=true

# Point to local OTel Collector
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces

# Service name for trace filtering
OTEL_SERVICE_NAME=x-agent-unified

# Sampling (1.0 = 100%, 0.1 = 10%)
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=1.0
```

### 5. Run Agent and View Traces

```bash
# Run agent (dry-run or live)
python src/main.py --mode both --dry-run true

# Open Jaeger UI
# Browser: http://localhost:16686

# Search for service: x-agent-unified
# Traces will appear with span details
```

---

## Jaeger UI Navigation

### Finding Traces

1. **Service**: Select `x-agent-unified`
2. **Operation**: Filter by operation (e.g., `run_scheduler`, `create_post`, `search_recent`)
3. **Tags**: Filter by custom attributes
   - `dry_run=false` (live operations)
   - `topic=power-platform`
   - `mode=both`
4. **Lookback**: Adjust time range (last hour, day, etc.)

### Analyzing Spans

- **Timeline view**: Visualize request flow and latency
- **Span details**: View attributes, events, logs
- **Trace graph**: See service dependencies
- **Compare traces**: Identify performance regressions

### Key Spans to Monitor

| Span Name | Description | Key Attributes |
|-----------|-------------|----------------|
| `run_scheduler` | Full scheduler cycle | `mode`, `dry_run` |
| `run_post_action` | Post creation flow | `topic`, `slot`, `window` |
| `run_interact_actions` | Search + engagement | `query`, `actions` |
| `create_post` | Tweet API call | `text_length`, `has_media` |
| `search_recent` | Search API call | `query`, `max_results` |
| `like_tweet` | Like action | `tweet_id` |
| `follow_user` | Follow action | `user_id` |

---

## Production Configuration

### OTel Collector (Advanced)

```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

  resource:
    attributes:
      - key: deployment.environment
        value: production
        action: insert

  # Tail sampling (reduce costs)
  tail_sampling:
    policies:
      # Always sample errors
      - name: errors-policy
        type: status_code
        status_code: {status_codes: [ERROR]}

      # Sample 10% of successful traces
      - name: probabilistic-policy
        type: probabilistic
        probabilistic: {sampling_percentage: 10}

exporters:
  otlp:
    endpoint: jaeger:4317
    tls:
      insecure: true

  # Send to external backend (e.g., Grafana Cloud, Honeycomb)
  otlphttp/cloud:
    endpoint: https://your-backend.com/v1/traces
    headers:
      Authorization: Bearer ${CLOUD_API_KEY}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource, tail_sampling]
      exporters: [otlp, otlphttp/cloud]
```

### Jaeger Storage Backends

**Development**: In-memory (default, ephemeral)
```yaml
# No additional config needed
```

**Production**: Persistent storage

**Option 1: Elasticsearch**
```yaml
jaeger:
  image: jaegertracing/all-in-one:1.51
  environment:
    - SPAN_STORAGE_TYPE=elasticsearch
    - ES_SERVER_URLS=http://elasticsearch:9200
  depends_on:
    - elasticsearch
```

**Option 2: Cassandra**
```yaml
jaeger:
  environment:
    - SPAN_STORAGE_TYPE=cassandra
    - CASSANDRA_SERVERS=cassandra:9042
```

**Option 3: Badger (embedded, single-node)**
```yaml
jaeger:
  environment:
    - SPAN_STORAGE_TYPE=badger
    - BADGER_DIRECTORY_VALUE=/badger/data
    - BADGER_DIRECTORY_KEY=/badger/key
  volumes:
    - ./jaeger-data:/badger
```

---

## Alerting Setup

### Monitoring Quota Exhaustion

Create a custom exporter in OTel Collector to track quota events:

```yaml
# otel-collector-config.yaml
exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: xagent

service:
  telemetry:
    metrics:
      level: detailed
      address: 0.0.0.0:8888
```

### Alert Rules (Prometheus + Alertmanager)

```yaml
# prometheus-rules.yml
groups:
  - name: x-agent-quota
    interval: 30s
    rules:
      # Alert when daily post quota > 80%
      - alert: PostQuotaHigh
        expr: xagent_posts_daily / xagent_posts_quota_daily > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "X Agent approaching daily post quota"
          description: "{{ $value }}% of daily post quota used"

      # Alert when monthly quota > 90%
      - alert: MonthlyQuotaCritical
        expr: xagent_posts_monthly / 1500 > 0.9
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "X Agent approaching monthly post limit (Free tier: 1,500)"
          description: "{{ $value }}% of monthly quota used"

      # Alert on rate limit violations
      - alert: RateLimitHit
        expr: rate(xagent_rate_limit_errors_total[5m]) > 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "X Agent hitting rate limits"
          description: "Rate limit errors detected in last 5 minutes"
```

### Grafana Dashboard (Optional)

Import pre-built dashboard for X Agent:

```json
{
  "dashboard": {
    "title": "X Agent Unified",
    "panels": [
      {
        "title": "Daily Posts",
        "targets": [{"expr": "xagent_posts_daily"}]
      },
      {
        "title": "Monthly Quota Usage",
        "targets": [{"expr": "xagent_posts_monthly / 1500 * 100"}]
      },
      {
        "title": "API Latency (p95)",
        "targets": [{"expr": "histogram_quantile(0.95, rate(xagent_api_duration_bucket[5m]))"}]
      },
      {
        "title": "Rate Limit Errors",
        "targets": [{"expr": "rate(xagent_rate_limit_errors_total[5m])"}]
      }
    ]
  }
}
```

---

## Troubleshooting

### Traces Not Appearing in Jaeger

1. **Check OTel Collector logs:**
   ```bash
   docker-compose logs otel-collector
   # Look for: "Traces received", "Exporter errors"
   ```

2. **Verify agent configuration:**
   ```bash
   # Check OTLP endpoint is reachable
   curl -X POST http://localhost:4318/v1/traces
   # Should return 405 (method not allowed), not connection error
   ```

3. **Check telemetry enabled:**
   ```python
   # In Python shell
   import os
   print(os.getenv("ENABLE_TELEMETRY"))  # Should be "true"
   ```

4. **Test with console exporter:**
   ```bash
   # Remove OTEL_EXPORTER_OTLP_ENDPOINT from .env
   # Run agent - spans will print to console
   python src/main.py --mode post --dry-run true
   ```

### High Collector Memory Usage

1. **Reduce batch size:**
   ```yaml
   processors:
     batch:
       send_batch_size: 512  # Down from 1024
       timeout: 5s
   ```

2. **Enable tail sampling** (sample after processing, reduces volume)

3. **Limit trace retention:**
   ```yaml
   # Jaeger
   jaeger:
     environment:
       - SPAN_RETENTION=48h  # Default: 7 days
   ```

### Missing Span Attributes

1. **Check code instrumentation:**
   ```python
   # Ensure span.set_attribute() calls are not in try/except blocks
   with tracer.start_as_current_span("operation") as span:
       span.set_attribute("key", value)  # Add explicit error handling
   ```

2. **Verify attribute limits:**
   - Max 128 attributes per span (OTel SDK default)
   - Attribute values > 1024 chars may be truncated

---

## Cost Optimization

### Sampling Strategies

**Development**: 100% sampling
```bash
OTEL_TRACES_SAMPLER=always_on
```

**Production**: Tail sampling with error priority
```yaml
# In OTel Collector config
processors:
  tail_sampling:
    policies:
      - name: errors
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 1000}
      - name: sample-rest
        type: probabilistic
        probabilistic: {sampling_percentage: 5}
```

**High-traffic**: Parent-based probabilistic
```bash
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling
```

### Storage Retention

```yaml
# Jaeger
jaeger:
  environment:
    - SPAN_RETENTION=48h  # Reduce from default 7d
```

### Collector Resource Limits

```yaml
# docker-compose.yml
otel-collector:
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
```

---

## Security Considerations

### API Keys in Spans

⚠️ **Never log sensitive data in span attributes!**

```python
# BAD - Exposes secrets
span.set_attribute("api_key", api_key)

# GOOD - Redact or hash
span.set_attribute("api_key_hash", hashlib.sha256(api_key.encode()).hexdigest()[:8])
```

### TLS for Production

```yaml
# otel-collector-config.yaml
exporters:
  otlp:
    endpoint: jaeger:4317
    tls:
      insecure: false
      cert_file: /etc/certs/client.crt
      key_file: /etc/certs/client.key
      ca_file: /etc/certs/ca.crt
```

### Authentication

```yaml
# OTel Collector with auth
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318
        auth:
          authenticator: basicauth

extensions:
  basicauth:
    htpasswd:
      file: /etc/otel/.htpasswd
```

---

## Next Steps

1. **Set up alerts** for quota thresholds (see Alerting Setup)
2. **Create Grafana dashboards** for real-time monitoring
3. **Document custom spans** in your codebase
4. **Configure log aggregation** (Loki, Elasticsearch) alongside traces
5. **Integrate with CI/CD** - trace deployments and compare performance

---

## References

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OTel Collector Configuration](https://opentelemetry.io/docs/collector/configuration/)
- [W3C TraceContext Spec](https://www.w3.org/TR/trace-context/)
- [X Agent Telemetry Implementation](../telemetry.md)

---

**Status**: Production-ready observability stack for X Agent Unified
**Updated**: 2025-11-08
