"""
OpenTelemetry tracing integration for X Agent.

Provides optional distributed tracing with W3C TraceContext propagation.
Disabled by default; enable via TELEMETRY_ENABLED=true (or legacy ENABLE_TELEMETRY=true).
"""

from __future__ import annotations

import logging
import os
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.trace import Tracer

from src.telemetry_core.factory import create_telemetry
from src.telemetry_core.noop import NoOpTelemetry
from src.telemetry_core.types import Telemetry

logger = logging.getLogger(__name__)

_tracer_provider: TracerProvider | None = None
_telemetry_enabled: bool = False
_telemetry_impl: Telemetry | None = None


def init_telemetry() -> None:
    """
    Initialize telemetry based on environment variables using the provider factory.

    Env vars:
    - TELEMETRY_ENABLED / ENABLE_TELEMETRY: 'true' to enable (default: false)
    - TELEMETRY_PROVIDER: provider name ('opentelemetry')
    - TELEMETRY_DEBUG: 'true' for debug logs on provider selection
    - OTEL_SERVICE_NAME, OTEL_EXPORTER_OTLP_ENDPOINT: standard OTel envs

    If the provider cannot be loaded or dependencies are missing, falls back to NoOp.
    """
    global _tracer_provider, _telemetry_enabled, _telemetry_impl

    primary = os.getenv("TELEMETRY_ENABLED")
    legacy = os.getenv("ENABLE_TELEMETRY")

    enabled = (primary or legacy or "").strip().lower() == "true"
    debug = os.getenv("TELEMETRY_DEBUG", "false").lower() == "true"

    if not enabled:
        if debug:
            logger.debug("Telemetry disabled (TELEMETRY_ENABLED/ENABLE_TELEMETRY != true)")
        _telemetry_impl = NoOpTelemetry()
        _telemetry_enabled = False
        _configure_noop_provider()
        return

    provider_name = os.getenv("TELEMETRY_PROVIDER", "opentelemetry").strip().lower()

    try:
        impl = create_telemetry(provider=provider_name)
        _telemetry_impl = impl
        # Mark enabled only if not NoOp
        _telemetry_enabled = not isinstance(impl, NoOpTelemetry)
        if debug:
            logger.debug(
                "Telemetry requested: provider=%s, enabled=%s",
                provider_name,
                _telemetry_enabled,
            )
    except Exception as e:
        # Defensive: never break runtime
        logger.warning("Telemetry initialization failed; falling back to NoOp: %s", e)
        _telemetry_impl = NoOpTelemetry()
        _telemetry_enabled = False
        _configure_noop_provider()


def _configure_noop_provider() -> None:
    """Configure a no-op tracer provider when telemetry is disabled or unavailable."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider

        global _tracer_provider
        _tracer_provider = TracerProvider()
        trace.set_tracer_provider(_tracer_provider)
    except ImportError:
        # OTel not installed; tracing calls will be no-ops
        pass


def get_tracer(name: str | None = None) -> Tracer:
    """
    Get a tracer instance for creating spans.

    Args:
        name: Tracer name (typically __name__). Defaults to 'x-agent'.

    Returns:
        Tracer instance (no-op if telemetry is disabled or unavailable).
    """
    tracer_name = name or "x-agent"

    try:
        from opentelemetry import trace

        return trace.get_tracer(tracer_name)
    except ImportError:
        # Return a minimal no-op tracer
        return _NoOpTracer()  # type: ignore[return-value]


def get_telemetry() -> Telemetry:
    """Return the current Telemetry implementation (NoOp when disabled)."""
    global _telemetry_impl
    if _telemetry_impl is None:
        # Lazy init to safe default
        _telemetry_impl = NoOpTelemetry()
    return _telemetry_impl


def is_telemetry_enabled() -> bool:
    """Check if telemetry is currently enabled and initialized."""
    return _telemetry_enabled


class _NoOpTracer:
    """Minimal no-op tracer when OpenTelemetry is not available."""

    def start_span(self, name: str, **kwargs):
        return _NoOpSpan()


class _NoOpSpan:
    """Minimal no-op span when OpenTelemetry is not available."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass

    def end(self) -> None:
        pass


def start_span(name: str) -> AbstractContextManager[Any]:
    """Return a context manager that starts a span as current when available.

    - If OpenTelemetry is installed, uses tracer.start_as_current_span(name).
    - Otherwise, returns a no-op context manager whose __enter__ yields _NoOpSpan.
    """
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer("x-agent")
        return tracer.start_as_current_span(name)
    except ImportError:

        class _NoOpCM:
            def __enter__(self) -> _NoOpSpan:
                return _NoOpSpan()

            def __exit__(self, *args) -> Literal[False]:
                return False

        return _NoOpCM()
