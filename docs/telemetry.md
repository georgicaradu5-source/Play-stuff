# Telemetry (optional)

This agent ships with optional OpenTelemetry tracing and W3C TraceContext log correlation. It's disabled by default and safe to turn on at any time. When disabled or when dependencies are missing, the code automatically falls back to a robust no-op provider.

## Enable in one minute

1. Install optional telemetry extras

```powershell
# Windows PowerShell
pip install -e .[telemetry]
```

```bash
# macOS/Linux
pip install -e .[telemetry]
```

2. Export environment variables

```powershell
# Windows PowerShell (canonical)
$env:TELEMETRY_ENABLED = "true"
$env:OTEL_SERVICE_NAME = "x-agent"          # optional, default: x-agent
# Use OTLP/HTTP exporter (e.g., local collector)
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318/v1/traces"  # optional

# Backward-compatible (also accepted)
$env:ENABLE_TELEMETRY = "true"
```

```bash
# macOS/Linux (canonical)
export TELEMETRY_ENABLED=true
export OTEL_SERVICE_NAME=x-agent                           # optional
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces  # optional

# Backward-compatible (also accepted)
export ENABLE_TELEMETRY=true
```

That's it. If OpenTelemetry packages aren't installed or the exporter can't be created, the agent continues with a no-op tracer.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEMETRY_ENABLED` | Enable telemetry (canonical) | `false` |
| `ENABLE_TELEMETRY` | Enable telemetry (backward-compatible) | `false` |
| `TELEMETRY_PROVIDER` | Provider name (currently only `opentelemetry`) | `opentelemetry` |
| `TELEMETRY_DEBUG` | Print debug logs on provider selection | `false` |
| `OTEL_SERVICE_NAME` | Service name for traces | `x-agent` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP endpoint (HTTP) | console exporter |
| `OTEL_TRACES_SAMPLER` | Sampling strategy | `always_on` |

## Troubleshooting

**Problem**: Telemetry enabled but no spans appear

- **Check**: Are telemetry extras installed? Run `pip list | grep opentelemetry`
- **Fix**: Install extras with `pip install -e .[telemetry]`
- **Verify**: Set `TELEMETRY_DEBUG=true` and check logs for provider selection messages

**Problem**: Import errors when telemetry is enabled

- **Cause**: Telemetry extras not installed
- **Behavior**: Agent automatically falls back to no-op provider
- **Fix**: Install extras or disable telemetry

**Problem**: Spans created but not exported

- **Check**: Is `OTEL_EXPORTER_OTLP_ENDPOINT` set correctly?
- **Default**: Without endpoint, spans go to console (stdout)
- **Fix**: Point to your collector (e.g., `http://localhost:4318/v1/traces`)

## Minimal, safe usage pattern

The agent already emits spans from key code paths using a context manager, and logs include trace/span IDs when a span is active.

```python
from telemetry import init_telemetry, start_span, get_tracer

# Initialize early (optional; safe to call even if OTel isn't installed)
init_telemetry()

# Use spans where it adds value
with start_span("x_client.search_recent") as span:
    span.set_attribute("query", query)
    span.set_attribute("max_results", max_results)
    # ... do the work ...

# Or fetch a tracer explicitly (when OTel is installed)
tracer = get_tracer(__name__)
with tracer.start_as_current_span("some.operation"):
    pass
```

- When ENABLE_TELEMETRY is false/unset: both helpers use a no-op backend.
- When ENABLE_TELEMETRY is true and packages are present: spans are emitted to the configured exporter.

## Diagnostics and CI-friendly checks

You can validate spans without any network calls using the in-memory exporter (this is how tests do it):

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# Set up a provider + in-memory exporter
provider = TracerProvider()
exporter = InMemorySpanExporter()
provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# Create a span through our helpers
from telemetry import start_span
with start_span("diagnostic-span") as span:
    span.set_attribute("ok", True)

spans = exporter.get_finished_spans()
assert any(s.name == "diagnostic-span" for s in spans)
```

Tip: set `OTEL_TRACES_SAMPLER` for custom sampling. Supported values include:

- `always_on`
- `parentbased_traceidratio/<ratio>` (e.g., `parentbased_traceidratio/0.2`)

## Privacy defaults

- Telemetry is disabled by default.
- No identifiers are emitted unless you opt in.
- When enabled, include only operational metadata (operation names, parameters sizes/counts)  -  avoid sensitive content.

## Advanced: Provider factory

Internally, the agent can choose a telemetry provider dynamically:

- If `ENABLE_TELEMETRY`/`TELEMETRY_ENABLED` is false: use a strict no-op provider.
- If true and OpenTelemetry is available: use the OpenTelemetry provider.
- If provider configuration fails or dependencies are missing: gracefully fall back to no-op.

Code: `src/telemetry_core/factory.py` and `src/telemetry_core/providers/opentelemetry_provider.py`.

## Adding spans to new endpoints (pattern)

When adding a new XClient endpoint, wrap the operation with a span and set a few attributes for observability.

```python
from reliability import request_with_retries, DEFAULT_TIMEOUT
from telemetry import start_span

class XClient:
    # ...
    def get_tweet(self, tweet_id: str) -> dict:
        with start_span("x_client.get_tweet") as span:
            try:
                span.set_attribute("tweet_id", tweet_id)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass

            if self.dry_run:
                return {"data": {"id": tweet_id, "text": "[dry-run]"}}

            if self.auth.mode == "tweepy":
                client = self.auth.get_tweepy_client()
                resp = client.get_tweet(tweet_id)
                return {"data": {"id": str(resp.data.id), "text": resp.data.text}}  # type: ignore[attr-defined]
            else:
                url = f"https://api.twitter.com/2/tweets/{tweet_id}"
                headers = {"Authorization": f"Bearer {self.auth.access_token}"}
                resp = request_with_retries("GET", url, headers=headers, timeout=DEFAULT_TIMEOUT)
                return resp.json()
```

This mirrors existing methods like `get_me` and `search_recent`, keeping behavior consistent with retries, idempotency, and dry-run.

## Adding new endpoints in XClient

When implementing new API endpoints in `XClient`, follow this pattern to ensure consistency with telemetry, reliability, and dry-run support:

### Pattern

1. Wrap the endpoint logic in a `start_span` context manager with a descriptive name (e.g., `"x_client.operation_name"`).
2. Set relevant attributes on the span (e.g., parameters, mode, dry_run) inside a `try/except` to never break if telemetry fails.
3. Check `self.dry_run` and return a mock response without calling the API.
4. Implement both `tweepy` and `oauth2` modes.
5. For `oauth2` mode, use `request_with_retries` from `reliability.py` to get automatic retries, backoff, and idempotency.
6. Return a consistent dict structure for both modes.

### Example: Adding a `get_user_timeline` endpoint

```python
from reliability import request_with_retries, DEFAULT_TIMEOUT
from telemetry import start_span
from typing import Any, cast

class XClient:
    # ... existing methods ...

    def get_user_timeline(self, user_id: str, max_results: int = 10) -> dict[str, Any]:
        """Get recent tweets from a specific user."""
        with start_span("x_client.get_user_timeline") as span:
            try:
                span.set_attribute("user_id", user_id)
                span.set_attribute("max_results", max_results)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass

            if self.dry_run:
                print(f"[DRY RUN] get_user_timeline(user_id={user_id}, max_results={max_results})")
                return {"data": [{"id": "dummy_tweet_id", "text": "[dry-run]"}]}

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.get_users_tweets(user_id, max_results=max_results)
                if resp.data:
                    return {"data": [{"id": str(t.id), "text": t.text} for t in resp.data]}
                return {"data": []}
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")
                url = f"{self.BASE_URL_V2}/users/{user_id}/tweets"
                headers = {"Authorization": f"Bearer {self.auth.access_token}"}
                params = {"max_results": max_results, "tweet.fields": "id,text"}
                resp = request_with_retries("GET", url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
                data = resp.json()
                return {"data": data.get("data", [])}
```

### Corresponding Test

```python
import os
import sys
import types

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from x_client import XClient  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = {}

    def json(self):
        return self._json


def make_fake_requests(sequence):
    state = {"calls": 0}

    def request(method, url, headers=None, params=None, json=None, timeout=None):
        state["calls"] += 1
        item = sequence[min(state["calls"] - 1, len(sequence) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    return types.SimpleNamespace(request=request), state


def test_get_user_timeline_oauth2_mode(monkeypatch):
    seq = [FakeResponse(200, {"data": [{"id": "123", "text": "Hello"}]})]
    fake_requests, state = make_fake_requests(seq)

    import reliability as rel
    monkeypatch.setattr(rel, "requests", types.SimpleNamespace(request=fake_requests.request), raising=False)

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(auth)

    result = client.get_user_timeline("user123", max_results=10)
    assert result["data"][0]["id"] == "123"
    assert state["calls"] >= 1
```

This pattern ensures that all endpoints:

- Have consistent telemetry spans (no-op safe when disabled)
- Use reliable HTTP calls with retries and timeouts
- Support dry-run testing
- Work in both auth modes
- Are covered by tests that don't require live API calls
