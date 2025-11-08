from typing import Any

import pytest

pytest.importorskip("opentelemetry")
from opentelemetry import trace

from telemetry_core.providers.opentelemetry_provider import create_opentelemetry


def _patch_provider_shutdown_to_raise(telemetry: Any) -> None:
    """Reach into the closure of telemetry.shutdown and patch provider.shutdown to raise.

    This exercises the exception swallow branch in shutdown for coverage.
    """
    shutdown_fn = telemetry.shutdown
    closure = getattr(shutdown_fn, "__closure__", None)
    if not closure:
        return
    for cell in closure:
        obj = getattr(cell, "cell_contents", None)
        if obj and hasattr(obj, "shutdown"):

            def _boom():  # type: ignore
                raise RuntimeError("simulated failure")

            obj.shutdown = _boom  # type: ignore[attr-defined]
            break


def test_opentelemetry_event_and_attribute_paths_console_exporter(monkeypatch):
    # Ensure console exporter path by unsetting endpoint
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    telemetry = create_opentelemetry()

    tracer = trace.get_tracer("x-agent")
    with tracer.start_as_current_span("test-span"):
        # Exercise event on active span
        telemetry.event("evt", {"a": 1})
        # Exercise user attribute attachment
        telemetry.set_user({"id": "u1", "role": "admin"})
        # Exercise generic attributes
        telemetry.set_attributes({"k": "v"})
        # Exercise record_exception with attrs
        telemetry.record_exception(ValueError("boom"), {"err.type": "ValueError"})

    # Basic sanity: current span after context should be a non-recording default
    assert trace.get_current_span() is not None
    # Exercise event path when there is no recording span
    telemetry.event("evt-no-active", {"b": 2})


def test_event_ignored_when_span_not_recording(monkeypatch):
    telemetry = create_opentelemetry()

    called = {"added": False}

    class DummySpan:
        def is_recording(self):
            return False

        def add_event(self, name, attrs=None):
            called["added"] = True

    # Force get_current_span to return a non-recording span to hit the guard branch
    monkeypatch.setattr("opentelemetry.trace.get_current_span", lambda: DummySpan())
    telemetry.event("guard-test", {"x": 1})
    # Since is_recording() is False, add_event should not be called
    assert called["added"] is False


def test_opentelemetry_shutdown_exception_is_swallowed(monkeypatch):
    telemetry = create_opentelemetry()
    # Patch provider.shutdown to raise to cover exception swallow path
    _patch_provider_shutdown_to_raise(telemetry)
    # Should not raise even though underlying provider.shutdown raises
    telemetry.shutdown()


def test_start_span_and_with_span_attribute_setting():
    telemetry = create_opentelemetry()
    span = telemetry.start_span("span-start", {"x": "y", "n": 1})
    span.add_event("inner")
    span.set_attribute("extra", "value")
    span.end()

    called = {}

    def _fn(s):
        s.add_event("evt")
        s.set_attribute("a", "b")
        called["ok"] = True

    telemetry.with_span("span-fn", _fn, {"attr": "val"})
    assert called.get("ok") is True
