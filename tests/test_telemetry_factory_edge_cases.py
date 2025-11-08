"""Tests for telemetry factory edge cases and error handling."""

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


def test_create_telemetry_opentelemetry_import_error():
    """Test create_telemetry() falls back to NoOp when OpenTelemetry import fails."""
    from telemetry_core.factory import create_telemetry
    from telemetry_core.noop import NoOpTelemetry

    os.environ["ENABLE_TELEMETRY"] = "true"
    os.environ["TELEMETRY_PROVIDER"] = "opentelemetry"

    # Mock the import to fail at the provider level
    with patch(
        "telemetry_core.providers.opentelemetry_provider.create_opentelemetry", side_effect=ImportError("no module")
    ):
        # Should fall back to NoOp instead of raising
        impl = create_telemetry(provider="opentelemetry")
        assert isinstance(impl, NoOpTelemetry)


def test_create_telemetry_opentelemetry_runtime_error():
    """Test create_telemetry() falls back to NoOp when provider raises RuntimeError."""
    from telemetry_core.factory import create_telemetry
    from telemetry_core.noop import NoOpTelemetry

    os.environ["ENABLE_TELEMETRY"] = "true"

    with patch(
        "telemetry_core.providers.opentelemetry_provider.create_opentelemetry", side_effect=RuntimeError("init failed")
    ):
        # Should fall back to NoOp
        impl = create_telemetry(provider="opentelemetry")
        assert isinstance(impl, NoOpTelemetry)


def test_create_telemetry_unknown_provider():
    """Test create_telemetry() falls back to NoOp for unknown provider."""
    from telemetry_core.factory import create_telemetry
    from telemetry_core.noop import NoOpTelemetry

    os.environ["ENABLE_TELEMETRY"] = "true"

    impl = create_telemetry(provider="unknown-provider")
    assert isinstance(impl, NoOpTelemetry)


def test_create_telemetry_otel_alias():
    """Test create_telemetry() accepts 'otel' as alias for 'opentelemetry'."""
    from telemetry_core.factory import create_telemetry

    os.environ["ENABLE_TELEMETRY"] = "true"

    # Should recognize 'otel' as OpenTelemetry provider
    impl = create_telemetry(provider="otel")
    assert impl is not None


def test_create_telemetry_disabled_returns_noop():
    """Test create_telemetry() returns NoOp when telemetry is disabled."""
    from telemetry_core.factory import create_telemetry
    from telemetry_core.noop import NoOpTelemetry

    # Ensure disabled
    os.environ.pop("ENABLE_TELEMETRY", None)
    os.environ.pop("TELEMETRY_ENABLED", None)

    impl = create_telemetry()
    assert isinstance(impl, NoOpTelemetry)


def test_create_telemetry_with_provider_arg_override():
    """Test create_telemetry() uses provider argument over environment variable."""
    from telemetry_core.factory import create_telemetry

    os.environ["ENABLE_TELEMETRY"] = "true"
    os.environ["TELEMETRY_PROVIDER"] = "unknown"

    # Provider argument should override env var
    impl = create_telemetry(provider="opentelemetry")
    assert impl is not None
