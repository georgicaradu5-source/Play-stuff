"""Coverage tests for logging_setup.py exception paths."""

import builtins
import logging
from unittest.mock import MagicMock, patch


def test_attach_tracecontext_importerror():
    """Test attach_tracecontext_to_logs handles ImportError when opentelemetry unavailable (covers lines 44-47)."""
    from logging_setup import attach_tracecontext_to_logs

    # Patch __import__ to raise ImportError for opentelemetry
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "opentelemetry" or name.startswith("opentelemetry."):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        attach_tracecontext_to_logs()

        # Create a log record to trigger the factory
        factory = logging.getLogRecordFactory()
        record = factory(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

        # Should have None for trace fields when ImportError occurs
        assert hasattr(record, 'trace_id')
        assert record.trace_id is None
        assert hasattr(record, 'span_id')
        assert record.span_id is None


def test_attach_tracecontext_exception_in_get_current_span():
    """Test attach_tracecontext_to_logs handles exceptions from get_current_span (covers lines 44-47)."""
    from logging_setup import attach_tracecontext_to_logs

    # Mock trace module but make get_current_span raise an exception
    mock_trace = MagicMock()
    mock_trace.get_current_span.side_effect = RuntimeError("Failed to get span")

    with patch.dict("sys.modules", {"opentelemetry.trace": mock_trace}):
        attach_tracecontext_to_logs()

        factory = logging.getLogRecordFactory()
        record = factory(
            name="test2",
            level=logging.INFO,
            pathname="test2.py",
            lineno=2,
            msg="test message 2",
            args=(),
            exc_info=None,
        )

        # Should have None for trace fields when exception occurs
        assert record.trace_id is None
        assert record.span_id is None
