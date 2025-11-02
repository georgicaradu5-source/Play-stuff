"""
Logging setup with W3C TraceContext correlation for X Agent.

Injects trace_id and span_id from active OpenTelemetry spans into log records.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def attach_tracecontext_to_logs(logger: logging.Logger | None = None) -> None:
    """
    Configure logging to inject W3C TraceContext IDs into log records.

    When an OpenTelemetry span is active, adds 'trace_id' and 'span_id' fields
    to every log record. IDs are formatted as zero-padded hex per W3C spec.

    Args:
        logger: Logger to configure (default: root logger).
    """
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):  # type: ignore
        record = old_factory(*args, **kwargs)

        # Inject trace context if available
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                ctx = span.get_span_context()
                # Format as 32-char hex for trace_id, 16-char hex for span_id (W3C spec)
                record.trace_id = format(ctx.trace_id, "032x")
                record.span_id = format(ctx.span_id, "016x")
            else:
                record.trace_id = None
                record.span_id = None
        except (ImportError, Exception):
            # OTel not available or error getting context
            record.trace_id = None
            record.span_id = None

        return record

    logging.setLogRecordFactory(record_factory)

    # Update formatter to include trace context if present
    if logger is None:
        logger = logging.getLogger()

    # Add trace context to existing formatters or create a new one
    for handler in logger.handlers:
        if handler.formatter:
            # Preserve existing format, append trace context
            old_format = handler.formatter._fmt or "%(message)s"
            if "trace_id" not in old_format:
                new_format = old_format.rstrip() + " [trace_id=%(trace_id)s span_id=%(span_id)s]"
                handler.setFormatter(logging.Formatter(new_format))
        else:
            # Default format with trace context
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
                    "[trace_id=%(trace_id)s span_id=%(span_id)s]"
                )
            )
