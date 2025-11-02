"""
Tests for OpenTelemetry telemetry integration.

Covers disabled/enabled paths, span creation, and log correlation.
Uses in-memory exporter for hermetic testing (no network calls).
"""

import logging
import os
from unittest.mock import patch

import pytest


def test_telemetry_disabled_by_default():
    """When ENABLE_TELEMETRY is unset or false, telemetry initializes in no-op mode."""
    from src.telemetry import init_telemetry, is_telemetry_enabled

    with patch.dict(os.environ, {}, clear=False):
        if "ENABLE_TELEMETRY" in os.environ:
            del os.environ["ENABLE_TELEMETRY"]

        init_telemetry()
        assert not is_telemetry_enabled()


def test_telemetry_disabled_explicitly():
    """When ENABLE_TELEMETRY=false, telemetry is disabled."""
    from src.telemetry import init_telemetry, is_telemetry_enabled

    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "false"}):
        init_telemetry()
        assert not is_telemetry_enabled()


def test_telemetry_enabled_with_otel_installed():
    """When ENABLE_TELEMETRY=true and OTel is installed, telemetry initializes successfully."""
    pytest.importorskip("opentelemetry")

    from src.telemetry import init_telemetry, is_telemetry_enabled

    with patch.dict(
        os.environ,
        {"ENABLE_TELEMETRY": "true", "OTEL_SERVICE_NAME": "test-service"},
    ):
        init_telemetry()
        assert is_telemetry_enabled()


def test_get_tracer_returns_valid_tracer():
    """get_tracer() returns a tracer that can create spans."""
    pytest.importorskip("opentelemetry")

    from src.telemetry import get_tracer, init_telemetry

    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "true"}):
        init_telemetry()
        tracer = get_tracer("test.module")
        assert tracer is not None

        # Create a span to verify it's functional
        with tracer.start_as_current_span("test-span"):
            pass  # Span created successfully


def test_spans_captured_with_in_memory_exporter():
    """Spans are captured using InMemorySpanExporter for hermetic testing."""
    pytest.importorskip("opentelemetry")

    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from src.telemetry import get_tracer, init_telemetry

    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "true"}):
        init_telemetry()

        # Replace processor with in-memory exporter
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))  # type: ignore

        tracer = get_tracer("test")
        with tracer.start_as_current_span("hermetic-span") as span:
            span.set_attribute("test.key", "test-value")

        # Verify span was captured
        spans = exporter.get_finished_spans()
        assert len(spans) >= 1
        captured = spans[-1]
        assert captured.name == "hermetic-span"
        assert captured.attributes["test.key"] == "test-value"  # type: ignore


def test_log_correlation_when_span_active():
    """Log records include trace_id and span_id when a span is active."""
    pytest.importorskip("opentelemetry")

    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from src.logging_setup import attach_tracecontext_to_logs
    from src.telemetry import get_tracer, init_telemetry

    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "true"}):
        init_telemetry()

        # Set up in-memory exporter
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))  # type: ignore

        # Configure logging with trace context
        logger = logging.getLogger("test_correlation")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        handler = logging.StreamHandler()
        logger.addHandler(handler)
        attach_tracecontext_to_logs(logger)

        # Create span and log within it
        tracer = get_tracer("test")
        with tracer.start_as_current_span("correlated-span") as span:
            # Capture log record
            records = []

            class RecordCapture(logging.Handler):
                def emit(self, record):  # type: ignore
                    records.append(record)

            capture = RecordCapture()
            logger.addHandler(capture)

            logger.info("Test log with correlation")

            # Verify trace context in log record
            assert len(records) == 1
            record = records[0]
            assert hasattr(record, "trace_id")
            assert hasattr(record, "span_id")
            assert record.trace_id is not None
            assert record.span_id is not None
            assert len(record.trace_id) == 32  # W3C hex format
            assert len(record.span_id) == 16  # W3C hex format

            # Verify IDs match span context
            ctx = span.get_span_context()
            assert record.trace_id == format(ctx.trace_id, "032x")
            assert record.span_id == format(ctx.span_id, "016x")


def test_log_correlation_when_no_span_active():
    """Log records have None trace_id/span_id when no span is active."""
    pytest.importorskip("opentelemetry")

    from src.logging_setup import attach_tracecontext_to_logs
    from src.telemetry import init_telemetry

    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "true"}):
        init_telemetry()

        logger = logging.getLogger("test_no_span")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        attach_tracecontext_to_logs(logger)

        records = []

        class RecordCapture(logging.Handler):
            def emit(self, record):  # type: ignore
                records.append(record)

        logger.addHandler(RecordCapture())
        logger.info("Log without span")

        assert len(records) == 1
        record = records[0]
        assert hasattr(record, "trace_id")
        assert hasattr(record, "span_id")
        assert record.trace_id is None
        assert record.span_id is None


def test_telemetry_gracefully_handles_missing_otel_packages():
    """When ENABLE_TELEMETRY=true but OTel not installed, initialization succeeds with no-op."""
    from src.telemetry import get_tracer, init_telemetry, is_telemetry_enabled

    # Simulate missing opentelemetry by patching import
    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "true"}):
        with patch("builtins.__import__", side_effect=ImportError("No module named 'opentelemetry'")):
            init_telemetry()
            # Should fall back to no-op mode
            assert not is_telemetry_enabled()

            # get_tracer should still return something functional (no-op)
            tracer = get_tracer()
            assert tracer is not None
