import os
from unittest.mock import patch

import pytest


def test_disabled_by_default_factory_no_throw():
    """Test that telemetry disabled by default never throws."""
    from src.telemetry import get_telemetry, init_telemetry, is_telemetry_enabled, start_span

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("TELEMETRY_ENABLED", None)
        os.environ.pop("ENABLE_TELEMETRY", None)
        init_telemetry()
        assert is_telemetry_enabled() is False
        t = get_telemetry()
        # Spans should be safe to create via helper
        with start_span("factory.disabled") as span:
            span.set_attribute("test", "ok")
        # Telemetry object should be callable safely but is a no-op
        t.event("noop-event", {"ok": True})


def test_enabled_but_provider_missing_graceful_noop():
    """Test that enabling telemetry without provider libs falls back to no-op.

    This test only runs when OpenTelemetry is NOT installed (basic CI job).
    It verifies graceful degradation to NoOp when TELEMETRY_ENABLED=true
    but the provider dependencies are missing.
    """
    # Skip if OpenTelemetry is installed (nothing to test - we want missing deps)
    try:
        import opentelemetry  # noqa: F401

        pytest.skip("OpenTelemetry is installed; cannot test missing-provider fallback")
    except ImportError:
        pass  # Good - OTel is missing, this is the scenario we want to test

    from src.telemetry import get_telemetry, init_telemetry, is_telemetry_enabled

    with patch.dict(os.environ, {"TELEMETRY_ENABLED": "true", "TELEMETRY_DEBUG": "true"}):
        init_telemetry()
        # When OTel is missing, telemetry should gracefully fall back to disabled
        assert is_telemetry_enabled() is False
        t = get_telemetry()
        t.event("still-noop")


def test_enabled_with_provider_installed_creates_spans():
    """Test that with telemetry extras installed, telemetry enables successfully.

    This test verifies that when TELEMETRY_ENABLED=true and OpenTelemetry is installed,
    telemetry initializes without errors and span creation doesn't throw.
    We don't verify the exact spans created because the provider creates its own
    tracer provider with console/OTLP exporters.
    """
    pytest.importorskip("opentelemetry")
    pytest.importorskip("opentelemetry.sdk.trace")

    from src.telemetry import init_telemetry, is_telemetry_enabled, start_span

    # Initialize telemetry with enabled flag
    with patch.dict(os.environ, {"TELEMETRY_ENABLED": "true"}):
        init_telemetry()
        # When OpenTelemetry is installed, telemetry should be enabled
        assert is_telemetry_enabled() is True

        # Span creation should work without errors
        with start_span("test.span.created") as span:
            span.set_attribute("test_key", "test_value")
            span.add_event("test_event", {"event_key": "event_value"})

        # No assertion on span collection since we're using the real provider
        # which exports to console or OTLP, not an in-memory exporter
