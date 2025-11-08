import os
import sys

import pytest

# Ensure top-level import resolution like other tests
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


def test_get_tracer_returns_noop_when_opentelemetry_missing():
    # If opentelemetry is installed in the environment, skip this test to avoid false negatives
    try:
        import opentelemetry  # noqa: F401

        pytest.skip("OpenTelemetry is installed; skipping no-op tracer assertion")
    except Exception:
        pass

    import telemetry

    tr = telemetry.get_tracer("test")

    # Confirm this is our minimal no-op tracer implementation
    assert type(tr).__name__ == "_NoOpTracer"

    # And that spans can be started/ended without errors
    span = tr.start_span("unit-test")
    assert hasattr(span, "end")
    span.end()


def test_noop_span_methods():
    """Test all NoOp span methods execute without errors."""
    from telemetry_core.noop import NoOpTelemetry

    telem = NoOpTelemetry()
    span = telem.start_span("test-span", attrs={"key": "value"})

    # All methods should be no-ops
    span.set_attribute("attr_key", "attr_value")
    span.add_event("test-event", {"event_key": "event_value"})
    span.record_exception(ValueError("test exception"))
    span.end()

    # No errors raised = success


def test_noop_telemetry_event():
    """Test NoOpTelemetry.event() executes without errors."""
    from telemetry_core.noop import NoOpTelemetry

    telem = NoOpTelemetry()
    telem.event("test-event", {"key": "value"})
    telem.event("another-event")  # without attrs


def test_noop_telemetry_with_span():
    """Test NoOpTelemetry.with_span() executes function and returns result."""
    from telemetry_core.noop import NoOpTelemetry

    telem = NoOpTelemetry()

    def test_fn(span):
        span.set_attribute("test", "value")
        return "success"

    result = telem.with_span("test-span", test_fn, attrs={"outer": "attr"})
    assert result == "success"


def test_noop_telemetry_set_user():
    """Test NoOpTelemetry.set_user() executes without errors."""
    from telemetry_core.noop import NoOpTelemetry

    telem = NoOpTelemetry()
    telem.set_user({"user_id": "12345", "name": "test_user"})
    telem.set_user(None)  # with None


def test_noop_telemetry_set_attributes():
    """Test NoOpTelemetry.set_attributes() executes without errors."""
    from telemetry_core.noop import NoOpTelemetry

    telem = NoOpTelemetry()
    telem.set_attributes({"key1": "value1", "key2": "value2"})


def test_noop_telemetry_record_exception():
    """Test NoOpTelemetry.record_exception() executes without errors."""
    from telemetry_core.noop import NoOpTelemetry

    telem = NoOpTelemetry()
    exc = RuntimeError("test error")
    telem.record_exception(exc, attrs={"error_context": "unit test"})
    telem.record_exception(exc)  # without attrs


def test_noop_telemetry_init_shutdown():
    """Test NoOpTelemetry.init() and shutdown() execute without errors."""
    from telemetry_core.noop import NoOpTelemetry

    telem = NoOpTelemetry()
    telem.init()
    telem.shutdown()
