import os
import sys
import pytest

# Ensure top-level import resolution like other tests
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


def test_get_tracer_returns_noop_when_opentelemetry_missing():
    # If opentelemetry is installed in the environment, skip this test to avoid false negatives
    try:
        import opentelemetry  # noqa: F401
        pytest.skip("OpenTelemetry is installed; skipping no-op tracer assertion")
    except Exception:
        pass

    import telemetry

    tr = telemetry.get_tracer("test")

    # Confirm this is our minimal no-op tracer implementation
    assert type(tr).__name__ == "_NoOpTracer"

    # And that spans can be started/ended without errors
    span = tr.start_span("unit-test")
    assert hasattr(span, "end")
    span.end()
