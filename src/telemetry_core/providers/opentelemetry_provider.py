from __future__ import annotations

import os
from typing import Any

from ..types import Attributes, SpanLike, Telemetry


def create_opentelemetry() -> Telemetry:
    """Create an OpenTelemetry-backed Telemetry implementation.

    Uses console exporter by default; if OTEL_EXPORTER_OTLP_ENDPOINT is set,
    configures OTLP/HTTP exporter. Dependencies are imported dynamically.
    """

    # Dynamic imports to avoid hard dependency when telemetry is disabled
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    service_name = os.getenv("OTEL_SERVICE_NAME", "x-agent")
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(service_name)

    class _Span(SpanLike):
        def __init__(self, span: Any):
            self._span = span

        def end(self) -> None:
            self._span.end()

        def add_event(self, name: str, attrs: Attributes | None = None) -> None:
            self._span.add_event(name, attrs)

        def set_attribute(self, key: str, value: Any) -> None:
            self._span.set_attribute(key, value)

        def record_exception(self, err: BaseException) -> None:
            self._span.record_exception(err)

    class _Telemetry(Telemetry):
        def init(self) -> None:
            pass

        def shutdown(self) -> None:
            # TracerProvider has a shutdown in newer SDKs; if absent, ignore
            try:
                provider.shutdown()
            except Exception:
                pass

        def event(self, name: str, attrs: Attributes | None = None) -> None:
            # Simple event on current span if any
            span = trace.get_current_span()
            if span is not None and getattr(span, "is_recording", lambda: False)():
                span.add_event(name, attrs)

        def start_span(self, name: str, attrs: Attributes | None = None) -> SpanLike:
            span = tracer.start_span(name)
            if attrs:
                for k, v in attrs.items():
                    span.set_attribute(k, v)
            return _Span(span)

        def with_span(self, name: str, fn: Any, attrs: Attributes | None = None) -> Any:
            span = tracer.start_span(name)
            try:
                if attrs:
                    for k, v in attrs.items():
                        span.set_attribute(k, v)
                return fn(_Span(span))
            finally:
                span.end()

        def set_user(self, user: dict[str, Any] | None = None) -> None:
            # Best-effort attach attributes on active span
            if not user:
                return
            span = trace.get_current_span()
            if span:
                for k, v in user.items():
                    span.set_attribute(f"user.{k}", v)

        def set_attributes(self, attrs: Attributes) -> None:
            span = trace.get_current_span()
            if span:
                for k, v in attrs.items():
                    span.set_attribute(k, v)

        def record_exception(self, err: BaseException, attrs: Attributes | None = None) -> None:
            span = trace.get_current_span()
            if span:
                span.record_exception(err)
                if attrs:
                    for k, v in attrs.items():
                        span.set_attribute(k, v)

    return _Telemetry()
