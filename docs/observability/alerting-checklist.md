# Quota & Rate Limit Alerting Checklist

Quick reference for setting up monitoring and alerts for X Agent Unified quota and rate limit violations.

---

## Critical Thresholds (Free Tier)

| Metric | Limit | Warning (80%) | Critical (90%) |
|--------|-------|---------------|----------------|
| **Monthly Posts** | 1,500 | 1,200 | 1,350 |
| **Daily Posts** | ~68 (1500/22 weekdays) | 54 | 61 |
| **Window Posts** | Per config | Per config × 0.8 | Per config × 0.9 |

---

## Alert Checklist

### ✅ Pre-Deployment Checks

- [ ] Telemetry enabled (`ENABLE_TELEMETRY=true`)
- [ ] OTel Collector running and receiving traces
- [ ] Jaeger UI accessible (http://localhost:16686)
- [ ] Prometheus scraping OTel Collector metrics (if using)
- [ ] Alertmanager configured with notification channels (email, Slack, PagerDuty)

### ✅ Required Alert Rules

#### 1. Monthly Quota Alerts

```yaml
# Alert at 80% monthly quota
- alert: MonthlyQuotaWarning
  expr: xagent_posts_monthly / 1500 > 0.8
  for: 5m
  labels:
    severity: warning
    tier: free
  annotations:
    summary: "80% of monthly post quota used"
    description: "Used {{ $value | humanizePercentage }} of 1,500 monthly posts"
    runbook: "Reduce max_per_window or disable weekend posting"

# Alert at 90% monthly quota
- alert: MonthlyQuotaCritical
  expr: xagent_posts_monthly / 1500 > 0.9
  for: 1m
  labels:
    severity: critical
    tier: free
  annotations:
    summary: "90% of monthly post quota used - URGENT"
    description: "Used {{ $value | humanizePercentage }} of 1,500 monthly posts"
    runbook: "Pause agent immediately or upgrade to Basic tier"
```

#### 2. Daily Quota Alerts

```yaml
- alert: DailyQuotaHigh
  expr: xagent_posts_daily > 54
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Daily posts exceeding safe rate"
    description: "{{ $value }} posts today (safe daily rate: 68 max)"
```

#### 3. Rate Limit Violations

```yaml
# 429 Too Many Requests errors
- alert: RateLimitHit
  expr: rate(xagent_rate_limit_errors_total[5m]) > 0
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Agent hitting X API rate limits"
    description: "{{ $value }} rate limit errors/sec in last 5m"
    runbook: "Check rate_limiter.py logs; increase jitter_seconds"

# Consecutive rate limit errors (circuit breaker)
- alert: RateLimitCircuitBreaker
  expr: increase(xagent_rate_limit_errors_total[10m]) > 10
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Excessive rate limiting - circuit breaker triggered"
    description: "{{ $value }} rate limit errors in 10 minutes"
    runbook: "Pause agent for 15 minutes; review config"
```

#### 4. Budget Exhaustion

```yaml
# Window quota exhausted
- alert: WindowQuotaExhausted
  expr: xagent_window_quota_remaining{action="post"} == 0
  for: 5m
  labels:
    severity: info
  annotations:
    summary: "Post quota exhausted for current window"
    description: "Window: {{ $labels.window }}, Action: {{ $labels.action }}"

# Safety buffer breached
- alert: BudgetBufferBreached
  expr: xagent_budget_buffer_remaining < 0
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Safety buffer breached - quota overrun risk"
    description: "Buffer remaining: {{ $value }}"
    runbook: "Review budget.py logic; check for calculation errors"
```

#### 5. API Error Rate

```yaml
# High API error rate (excluding rate limits)
- alert: APIErrorRateHigh
  expr: rate(xagent_api_errors_total{code!="429"}[5m]) > 0.05
  for: 3m
  labels:
    severity: warning
  annotations:
    summary: "High API error rate (non-rate-limit)"
    description: "{{ $value }} errors/sec: {{ $labels.code }}"
    runbook: "Check X API status page; review error logs"
```

---

## Metric Instrumentation

### Required Metrics (Add to src/storage.py or new metrics.py)

```python
from prometheus_client import Counter, Gauge

# Counters
posts_monthly = Gauge('xagent_posts_monthly', 'Total posts this month')
posts_daily = Gauge('xagent_posts_daily', 'Total posts today')
rate_limit_errors = Counter('xagent_rate_limit_errors_total', 'Rate limit errors (429)')
api_errors = Counter('xagent_api_errors_total', 'API errors by status code', ['code'])

# Gauges
window_quota_remaining = Gauge(
    'xagent_window_quota_remaining',
    'Remaining quota for current window',
    ['window', 'action']
)
budget_buffer_remaining = Gauge('xagent_budget_buffer_remaining', 'Safety buffer remaining')

# Usage example in scheduler
def run_post_action(...):
    posts_daily.inc()
    posts_monthly.inc()
    window_quota_remaining.labels(window='morning', action='post').dec()
```

### Span Events for Quota Tracking

```python
# In src/budget.py or scheduler.py
from src.telemetry import get_tracer

tracer = get_tracer(__name__)

with tracer.start_as_current_span("check_quota") as span:
    remaining = get_remaining_quota()
    span.set_attribute("quota.remaining", remaining)
    span.set_attribute("quota.monthly_used", monthly_posts)
    span.set_attribute("quota.monthly_limit", 1500)

    if remaining < 150:  # < 10% remaining
        span.add_event("quota_warning", {"threshold": "90%"})
```

---

## Dashboard Panels

### Grafana Panel Examples

#### 1. Monthly Quota Gauge
```json
{
  "type": "gauge",
  "title": "Monthly Quota Usage",
  "targets": [{
    "expr": "xagent_posts_monthly / 1500 * 100"
  }],
  "thresholds": {
    "mode": "absolute",
    "steps": [
      {"value": 0, "color": "green"},
      {"value": 80, "color": "yellow"},
      {"value": 90, "color": "red"}
    ]
  }
}
```

#### 2. Daily Post Rate
```json
{
  "type": "graph",
  "title": "Posts per Day (Last 30 Days)",
  "targets": [{
    "expr": "xagent_posts_daily"
  }],
  "yaxes": [{
    "max": 68,
    "label": "Posts/day"
  }]
}
```

#### 3. Rate Limit Error Rate
```json
{
  "type": "graph",
  "title": "Rate Limit Errors (5m rate)",
  "targets": [{
    "expr": "rate(xagent_rate_limit_errors_total[5m])"
  }],
  "alert": {
    "name": "Rate Limit Spike",
    "conditions": [{"type": "gt", "value": 0.1}]
  }
}
```

---

## Notification Channels

### Slack Integration

```yaml
# alertmanager.yml
receivers:
  - name: 'slack-xagent'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#xagent-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}{{ end }}'
        send_resolved: true
```

### Email Alerts

```yaml
receivers:
  - name: 'email-critical'
    email_configs:
      - to: 'ops@example.com'
        from: 'alerts@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@example.com'
        auth_password: '${SMTP_PASSWORD}'
        headers:
          Subject: '[X Agent] {{ .GroupLabels.severity | toUpper }}: {{ .GroupLabels.alertname }}'
```

### PagerDuty (Critical Only)

```yaml
receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        severity: '{{ .GroupLabels.severity }}'
        description: '{{ .GroupLabels.alertname }}: {{ .Annotations.summary }}'
```

---

## Runbook Actions

### Monthly Quota > 80%

1. **Review config.yaml**:
   - Reduce `max_per_window.post` from 1 to 0 (disable posting temporarily)
   - Limit `cadence.weekdays` to [1, 2, 3, 4, 5] (skip weekends)

2. **Check database**:
   ```sql
   -- Get monthly post count
   SELECT COUNT(*) FROM actions WHERE action = 'post' AND timestamp > date('now', 'start of month');
   ```

3. **Estimate remaining budget**:
   ```python
   # In Python shell
   from src.budget import BudgetManager
   bm = BudgetManager(plan="free", enabled=True)
   print(f"Remaining: {bm.can_post()}")
   ```

4. **Options**:
   - Pause agent until next month
   - Upgrade to Basic tier (3,000 posts/month)
   - Switch to interact-only mode (`--mode interact`)

### Rate Limit Errors Spiking

1. **Check rate_limiter.py logs**:
   ```bash
   grep "Rate limit" logs/agent.log | tail -20
   ```

2. **Increase jitter**:
   ```yaml
   # config.yaml
   jitter_seconds: [5, 15]  # Up from [1, 3]
   ```

3. **Reduce concurrency** (if running multiple instances)

4. **Review X API status**: https://api.twitterstat.us/

### API 403 Forbidden

1. **Re-authorize**:
   ```bash
   rm .token.json
   python src/main.py --authorize
   ```

2. **Check app permissions** in X Developer Portal:
   - Should be "Read and write"
   - Verify OAuth 2.0 is enabled

3. **Verify scopes** in `.token.json`:
   ```bash
   cat .token.json | jq .scope
   # Should include: tweet.write, tweet.read, like.write, follows.write
   ```

---

## Testing Alerts

### Trigger Test Alert

```python
# test_alert.py
from prometheus_client import Counter, Gauge, push_to_gateway

# Simulate quota breach
posts_monthly = Gauge('xagent_posts_monthly', 'Monthly posts')
posts_monthly.set(1400)  # 93% of 1,500

# Push to Pushgateway (if using)
push_to_gateway('localhost:9091', job='xagent-test', registry=...)
```

### Silence False Positives

```bash
# amtool (Alertmanager CLI)
amtool silence add alertname="MonthlyQuotaWarning" --duration=1h --comment="Testing"
```

---

## Monthly Review Checklist

- [ ] Review quota usage trends (Grafana dashboard)
- [ ] Check for rate limit patterns (time of day, specific endpoints)
- [ ] Validate alert thresholds (adjust if too noisy/quiet)
- [ ] Test notification channels (send test alert)
- [ ] Update runbooks with lessons learned
- [ ] Archive old traces (Jaeger retention policy)
- [ ] Review and optimize config.yaml based on engagement metrics

---

## Emergency Stop

If quota is exhausted or rate limits are overwhelming:

```bash
# Stop agent immediately
pkill -f "python src/main.py"

# Disable in systemd (if running as service)
sudo systemctl stop xagent
sudo systemctl disable xagent

# Temporary pause: Set dry-run permanently
# config.yaml: Add safeguard
# OR: Environment override
export X_FORCE_DRY_RUN=true
```

---

**Status**: Alerting checklist complete
**Priority**: Set up monthly quota alerts (critical) and rate limit monitoring (high)
**Updated**: 2025-11-08
