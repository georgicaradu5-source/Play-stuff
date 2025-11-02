"""
OpenTelemetry tracing integration for X Agent.

Provides optional distributed tracing with W3C TraceContext propagation.
Disabled by default; enable via ENABLE_TELEMETRY=true environment variable.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.trace import Tracer

logger = logging.getLogger(__name__)

_tracer_provider: TracerProvider | None = None
_telemetry_enabled: bool = False


def init_telemetry() -> None:
    """
    Initialize OpenTelemetry tracing based on environment variables.

    Environment variables:
    - ENABLE_TELEMETRY: Set to 'true' to enable tracing (default: false)
    - OTEL_SERVICE_NAME: Service name for traces (default: 'x-agent')
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP HTTP endpoint (optional; if unset, uses in-memory/no-op)
    - OTEL_TRACES_SAMPLER: Sampling strategy (default: 'parentbased_always_on')

    If telemetry is disabled or OTel packages are not installed, configures a no-op provider.
    """
    global _tracer_provider, _telemetry_enabled

    enable_telemetry = os.getenv("ENABLE_TELEMETRY", "false").lower() == "true"

    if not enable_telemetry:
        logger.debug("Telemetry disabled (ENABLE_TELEMETRY != true)")
        _telemetry_enabled = False
        _configure_noop_provider()
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ParentBasedTraceIdRatio

        _telemetry_enabled = True

        service_name = os.getenv("OTEL_SERVICE_NAME", "x-agent")
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        sampler_name = os.getenv("OTEL_TRACES_SAMPLER", "parentbased_always_on").lower()

        # Configure sampler
        if sampler_name == "always_on":
            sampler = ALWAYS_ON
        elif sampler_name.startswith("parentbased_traceidratio"):
            # Extract ratio if specified, default to 1.0
            ratio = 1.0
            if "/" in sampler_name:
                try:
                    ratio = float(sampler_name.split("/")[-1])
                except ValueError:
                    pass
            sampler: Any = ParentBasedTraceIdRatio(ratio)
        else:  # default: parentbased_always_on
            sampler = ALWAYS_ON

        resource = Resource.create({"service.name": service_name})
        _tracer_provider = TracerProvider(resource=resource, sampler=sampler)

        # Configure exporter
        if otlp_endpoint:
            logger.info(f"Telemetry enabled with OTLP endpoint: {otlp_endpoint}")
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        else:
            logger.info("Telemetry enabled with in-memory/console exporter (no OTLP endpoint)")
            # Use console exporter for local dev/testing
            _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(_tracer_provider)
        logger.info(f"OpenTelemetry tracing initialized (service: {service_name}, sampler: {sampler_name})")

    except ImportError as e:
        logger.warning(
            f"Telemetry enabled but OpenTelemetry packages not installed: {e}. "
            "Install with: pip install -e .[telemetry]"
        )
        _telemetry_enabled = False
        _configure_noop_provider()
    except Exception as e:
        logger.error(f"Failed to initialize telemetry: {e}", exc_info=True)
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
        return _NoOpTracer()


def is_telemetry_enabled() -> bool:
    """Check if telemetry is currently enabled and initialized."""
    return _telemetry_enabled


class _NoOpTracer:
    """Minimal no-op tracer when OpenTelemetry is not available."""

    def start_span(self, name: str, **kwargs):  # type: ignore
        return _NoOpSpan()


class _NoOpSpan:
    """Minimal no-op span when OpenTelemetry is not available."""

    def __enter__(self):  # type: ignore
        return self

    def __exit__(self, *args):  # type: ignore
        pass

    def set_attribute(self, key: str, value: any) -> None:  # type: ignore
        pass

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        pass

    def set_status(self, status: any) -> None:  # type: ignore
        pass

    def end(self) -> None:
        pass
