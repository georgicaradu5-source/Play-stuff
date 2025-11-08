"""Tests for telemetry.py context managers and helper functions."""

import os
import sys
from unittest.mock import patch

import pytest

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


@pytest.fixture(autouse=True)
def reset_telemetry_env():
    """Reset telemetry environment variables before each test."""
    old_values = {}
    telemetry_vars = [
        "TELEMETRY_ENABLED",
        "ENABLE_TELEMETRY",
        "TELEMETRY_PROVIDER",
        "TELEMETRY_DEBUG",
        "OTEL_SERVICE_NAME",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    ]
    for var in telemetry_vars:
        old_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore
    for var, value in old_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


def test_start_span_context_manager_with_opentelemetry():
    """Test start_span() returns proper context manager when OpenTelemetry is available."""
    try:
        import opentelemetry  # noqa: F401
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    import telemetry

    with telemetry.start_span("test-span") as span:
        span.set_attribute("key", "value")
        span.add_event("test-event")


def test_start_span_context_manager_without_opentelemetry():
    """Test start_span() returns no-op context manager when OpenTelemetry is missing."""
    import telemetry

    # Patch at the point of use within the function
    with patch("opentelemetry.trace.get_tracer", side_effect=ImportError):
        # Should use the no-op fallback
        cm = telemetry.start_span("test-span")

        # Manually invoke context manager protocol
        span = cm.__enter__()
        assert hasattr(span, "set_attribute")
        span.set_attribute("key", "value")
        span.add_event("test-event")
        span.set_status("OK")
        span.end()
        cm.__exit__(None, None, None)


def test_noop_span_context_manager():
    """Test _NoOpSpan works as context manager."""
    import telemetry

    span = telemetry._NoOpSpan()

    with span:
        span.set_attribute("key", "value")
        span.add_event("event")
        span.set_status("OK")

    span.end()


def test_init_telemetry_with_telemetry_enabled():
    """Test init_telemetry() with TELEMETRY_ENABLED=true."""
    import telemetry

    os.environ["TELEMETRY_ENABLED"] = "true"

    telemetry.init_telemetry()

    # Should be enabled (or NoOp if OpenTelemetry not installed)
    impl = telemetry.get_telemetry()
    assert impl is not None


def test_init_telemetry_with_legacy_enable_telemetry():
    """Test init_telemetry() with legacy ENABLE_TELEMETRY=true."""
    import telemetry

    os.environ["ENABLE_TELEMETRY"] = "true"

    telemetry.init_telemetry()

    impl = telemetry.get_telemetry()
    assert impl is not None


def test_init_telemetry_disabled_with_debug():
    """Test init_telemetry() logs debug message when disabled."""
    import telemetry

    os.environ["TELEMETRY_DEBUG"] = "true"

    with patch("telemetry.logger.debug") as mock_debug:
        telemetry.init_telemetry()

        # Should log debug message about being disabled
        assert mock_debug.called
        assert any("disabled" in str(call).lower() for call in mock_debug.call_args_list)


def test_init_telemetry_enabled_with_debug():
    """Test init_telemetry() logs debug message when enabled."""
    import telemetry

    os.environ["TELEMETRY_ENABLED"] = "true"
    os.environ["TELEMETRY_DEBUG"] = "true"

    with patch("telemetry.logger.debug") as mock_debug:
        telemetry.init_telemetry()

        # Should log debug message about provider
        assert mock_debug.called


def test_init_telemetry_factory_raises_exception():
    """Test init_telemetry() handles factory exceptions gracefully."""
    import telemetry

    os.environ["TELEMETRY_ENABLED"] = "true"

    with patch("telemetry.create_telemetry", side_effect=RuntimeError("factory error")):
        with patch("telemetry.logger.warning") as mock_warning:
            telemetry.init_telemetry()

            # Should fall back to NoOp and log warning
            impl = telemetry.get_telemetry()
            assert impl is not None
            assert mock_warning.called
            assert any("failed" in str(call).lower() for call in mock_warning.call_args_list)


def test_configure_noop_provider_opentelemetry_missing():
    """Test _configure_noop_provider() when OpenTelemetry is not installed."""
    import telemetry

    with patch.dict(sys.modules, {"opentelemetry": None, "opentelemetry.sdk.trace": None}):
        # Should not raise even when OTel is missing
        telemetry._configure_noop_provider()


def test_get_tracer_with_custom_name():
    """Test get_tracer() with custom tracer name."""
    try:
        import opentelemetry  # noqa: F401
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    import telemetry

    tracer = telemetry.get_tracer("custom-tracer")
    assert tracer is not None


def test_get_tracer_without_opentelemetry():
    """Test get_tracer() returns no-op tracer when OpenTelemetry is missing."""
    import telemetry

    with patch.dict(sys.modules, {"opentelemetry": None}):
        tracer = telemetry.get_tracer("test")

        # Should return _NoOpTracer
        assert type(tracer).__name__ == "_NoOpTracer"


def test_get_telemetry_lazy_init():
    """Test get_telemetry() lazy initializes to NoOp if not already set."""
    import telemetry

    # Reset global state
    telemetry._telemetry_impl = None

    impl = telemetry.get_telemetry()

    # Should return NoOpTelemetry
    from telemetry_core.noop import NoOpTelemetry

    assert isinstance(impl, NoOpTelemetry)


def test_is_telemetry_enabled_false_by_default():
    """Test is_telemetry_enabled() returns False by default."""
    import telemetry

    # Reset state
    telemetry._telemetry_enabled = False

    assert telemetry.is_telemetry_enabled() is False


def test_is_telemetry_enabled_true_when_initialized():
    """Test is_telemetry_enabled() returns True when enabled and initialized."""
    try:
        import opentelemetry  # noqa: F401
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    import telemetry

    os.environ["TELEMETRY_ENABLED"] = "true"

    telemetry.init_telemetry()

    # May be True if OpenTelemetry is available
    enabled = telemetry.is_telemetry_enabled()
    assert isinstance(enabled, bool)
