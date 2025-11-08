"""Advanced tests for OpenTelemetry provider implementation."""

import os
import sys
from unittest.mock import Mock, patch

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


def test_opentelemetry_provider_shutdown_raises():
    """Test OpenTelemetry provider handles shutdown() exceptions gracefully."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"
    os.environ["TELEMETRY_PROVIDER"] = "opentelemetry"

    telem = create_opentelemetry()

    # Mock the provider to raise on shutdown
    with patch("opentelemetry.sdk.trace.TracerProvider.shutdown", side_effect=RuntimeError("shutdown error")):
        # Should not raise; exception is caught
        telem.shutdown()


def test_opentelemetry_provider_event_on_non_recording_span():
    """Test event() when current span is not recording."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"

    telem = create_opentelemetry()

    # Mock get_current_span to return a non-recording span
    mock_span = Mock()
    mock_span.is_recording.return_value = False

    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        # Should not call add_event on non-recording span
        telem.event("test-event", {"key": "value"})
        mock_span.add_event.assert_not_called()


def test_opentelemetry_provider_event_on_none_span():
    """Test event() when there is no current span."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"

    telem = create_opentelemetry()

    with patch("opentelemetry.trace.get_current_span", return_value=None):
        # Should not raise when no span is active
        telem.event("test-event", {"key": "value"})


def test_opentelemetry_provider_set_user_no_current_span():
    """Test set_user() when there is no current span."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"

    telem = create_opentelemetry()

    with patch("opentelemetry.trace.get_current_span", return_value=None):
        # Should not raise when no span is active
        telem.set_user({"user_id": "12345"})


def test_opentelemetry_provider_set_user_with_none():
    """Test set_user(None) returns early without errors."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"

    telem = create_opentelemetry()

    # Should not raise
    telem.set_user(None)


def test_opentelemetry_provider_set_attributes_no_current_span():
    """Test set_attributes() when there is no current span."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"

    telem = create_opentelemetry()

    with patch("opentelemetry.trace.get_current_span", return_value=None):
        # Should not raise when no span is active
        telem.set_attributes({"key": "value"})


def test_opentelemetry_provider_record_exception_no_current_span():
    """Test record_exception() when there is no current span."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"

    telem = create_opentelemetry()

    with patch("opentelemetry.trace.get_current_span", return_value=None):
        # Should not raise when no span is active
        exc = ValueError("test error")
        telem.record_exception(exc, attrs={"context": "test"})


def test_opentelemetry_provider_with_otlp_endpoint():
    """Test OpenTelemetry provider with OTLP endpoint configured."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318/v1/traces"
    os.environ["OTEL_SERVICE_NAME"] = "test-service"

    # Should create provider with OTLP exporter
    telem = create_opentelemetry()

    # Verify basic functionality
    span = telem.start_span("test-span", attrs={"test": "value"})
    span.set_attribute("key", "value")
    span.add_event("test-event", {"event_key": "event_value"})
    span.end()


def test_opentelemetry_provider_with_span_context():
    """Test with_span() executes function with span context."""
    try:
        from telemetry_core.providers.opentelemetry_provider import (
            create_opentelemetry,
        )
    except ImportError:
        pytest.skip("OpenTelemetry not installed")

    os.environ["ENABLE_TELEMETRY"] = "true"

    telem = create_opentelemetry()

    def test_fn(span):
        span.set_attribute("inside", "fn")
        return "result"

    result = telem.with_span("test-span", test_fn, attrs={"outer": "attr"})
    assert result == "result"
