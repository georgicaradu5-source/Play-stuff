from datetime import datetime
from typing import Any, cast

import pytest

otel_trace = pytest.importorskip("opentelemetry.trace", reason="OpenTelemetry not installed")
otel_sdk_trace = pytest.importorskip(
    "opentelemetry.sdk.trace",
    reason="OpenTelemetry SDK not installed",
)
otel_export = pytest.importorskip(
    "opentelemetry.sdk.trace.export",
    reason="OpenTelemetry SDK exporter not installed",
)

from scheduler import run_scheduler  # noqa: E402
from x_client import XClient  # noqa: E402


def _setup_tracer():
    # Defer imports to after importorskip to avoid ImportError in type checkers
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)

    # Try to attach to an existing SDK provider if present; otherwise set a new one
    current = trace.get_tracer_provider()
    if hasattr(current, "add_span_processor"):
        try:
            current.add_span_processor(processor)  # type: ignore[reportUnknownMemberType]
            return exporter
        except Exception:
            pass

    provider = TracerProvider()
    provider.add_span_processor(processor)
    try:
        trace.set_tracer_provider(provider)
    except Exception:
        # If overriding not allowed, best-effort attach to whatever is current
        curr2 = trace.get_tracer_provider()
        if hasattr(curr2, "add_span_processor"):
            try:
                curr2.add_span_processor(processor)  # type: ignore[reportUnknownMemberType]
            except Exception:
                pass
    return exporter


class _FakeStorage:
    def bandit_choose(self, topics: list[str]) -> str:
        return topics[0] if topics else "automation"

    def is_text_duplicate(self, text: str, days: int = 7) -> bool:  # noqa: ARG002
        return False

    def log_action(self, **kwargs: Any) -> None:  # noqa: D401, ANN401
        # minimal stub – could capture actions for assertions if needed
        _ = kwargs


class _FakeAuth:
    # x_client spans access auth.mode even in dry_run
    mode = "tweepy"


@pytest.mark.skipif("opentelemetry" not in otel_trace.__package__, reason="OpenTelemetry not installed")
def test_spans_emitted_for_scheduler_and_client():
    exporter = _setup_tracer()

    # Minimal config: ensure today is allowed and a simple time window/topic
    today = datetime.today().isoweekday()
    config: dict[str, Any] = {
        "cadence": {"weekdays": [today]},
        "schedule": {"windows": ["morning"]},
        "topics": ["testing"],
        "learning": {"enabled": False},
        # interaction queries omitted to keep it light
    }

    storage = _FakeStorage()
    client = XClient(cast(Any, _FakeAuth()), dry_run=True)

    # Exercise scheduler (post-only) to get scheduler.run + scheduler.run_post_action
    run_scheduler(client=client, storage=cast(Any, storage), config=config, mode="post", dry_run=True)

    # Also exercise a couple of client calls to generate x_client.* spans
    client.get_me()
    client.search_recent("python")

    spans = exporter.get_finished_spans()
    names = [s.name for s in spans]

    # Assert scheduler spans
    assert "scheduler.run" in names
    assert "scheduler.run_post_action" in names

    # Assert client spans
    assert "x_client.get_me" in names
    assert "x_client.search_recent" in names

    # Attribute checks – find relevant spans and verify key attributes
    def find(name: str):
        return [s for s in spans if s.name == name]

    sched_run = find("scheduler.run")[0]
    sched_attrs = getattr(sched_run, "attributes", {})
    assert sched_attrs.get("mode") == "post"
    assert sched_attrs.get("dry_run") is True

    post_span = find("scheduler.run_post_action")[0]
    # topic and slot are set; we only verify they exist and types are reasonable
    post_attrs = getattr(post_span, "attributes", {})
    assert "topic" in post_attrs
    assert "slot" in post_attrs

    get_me_span = find("x_client.get_me")[0]
    get_me_attrs = getattr(get_me_span, "attributes", {})
    assert get_me_attrs.get("dry_run") is True
    assert get_me_attrs.get("mode") in ("tweepy", "oauth2")

    search_span = find("x_client.search_recent")[0]
    search_attrs = getattr(search_span, "attributes", {})
    assert search_attrs.get("query") == "python"
    assert search_attrs.get("max_results") == 20
