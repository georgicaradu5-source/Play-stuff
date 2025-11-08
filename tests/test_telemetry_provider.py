import pytest


def test_provider_console_exporter_silent(monkeypatch):
    pytest.importorskip("opentelemetry")
    from src.telemetry_core.providers import opentelemetry_provider as prov

    # Replace ConsoleSpanExporter with a no-op to avoid I/O on closed file warnings
    class SilentExporter:
        def export(self, spans):
            return 0

        def shutdown(self):
            pass

    # Patch import of sdk.trace.export to provide Silent ConsoleSpanExporter
    import builtins
    import sys
    real_import = builtins.__import__
    def fake_import(name, *args, **kwargs):
        if name == "opentelemetry.sdk.trace.export":
            mod = type("E", (), {})()
            class SilentBatch:
                def __init__(self, exporter):
                    self.exporter = exporter
                def on_start(self, span, parent_context=None):
                    pass
                def on_end(self, span):
                    pass
                def shutdown(self):
                    pass
            setattr(mod, "BatchSpanProcessor", SilentBatch)
            setattr(mod, "ConsoleSpanExporter", SilentExporter)
            return mod
        return real_import(name, *args, **kwargs)
    # Ensure our fake is used instead of cached module
    sys.modules.pop("opentelemetry.sdk.trace.export", None)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    telemetry = prov.create_opentelemetry()
    telemetry.init()

    # Should be able to create span and set attributes
    span = telemetry.start_span("provider.span")
    span.set_attribute("k", "v")
    span.add_event("e1", {"a": 1})
    span.end()

    # shutdown should not raise even if provider has no explicit shutdown
    telemetry.shutdown()


def test_provider_otlp_branch_silent(monkeypatch):
    # Only run if otel is available
    pytest.importorskip("opentelemetry")
    from src.telemetry_core.providers import opentelemetry_provider as prov

    class DummyOTLP:
        def __init__(self, *a, **k):
            pass

        def export(self, spans):
            return 0

        def shutdown(self):
            pass

    class SilentBatch:
        def __init__(self, exporter):
            # Accept any exporter
            self.exporter = exporter

        def on_start(self, span, parent_context=None):
            pass

        def on_end(self, span):
            pass

        def shutdown(self):
            pass

    # Force OTLP branch
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

    # Patch imports performed inside create_opentelemetry to return our dummies
    import builtins
    import sys

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "opentelemetry.exporter.otlp.proto.http.trace_exporter":
            mod = type("M", (), {})()
            setattr(mod, "OTLPSpanExporter", DummyOTLP)
            return mod
        if name == "opentelemetry.sdk.trace.export":
            mod = type("E", (), {})()
            setattr(mod, "BatchSpanProcessor", lambda exporter: SilentBatch(exporter))
            # Provide ConsoleSpanExporter symbol too (unused in OTLP path)
            setattr(mod, "ConsoleSpanExporter", object)
            return mod
        return real_import(name, *args, **kwargs)

    # Ensure our fake is used instead of cached module
    sys.modules.pop("opentelemetry.sdk.trace.export", None)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    telemetry = prov.create_opentelemetry()
    s = telemetry.start_span("otlp.span")
    s.end()
    telemetry.shutdown()


def test_provider_otlp_exporter_failure(monkeypatch):
    """If OTLP exporter construction fails, the error should propagate."""
    pytest.importorskip("opentelemetry")
    from src.telemetry_core.providers import opentelemetry_provider as prov

    class FailingOTLP:
        def __init__(self, *a, **k):
            raise RuntimeError("exporter boom")

    # Force OTLP branch
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "opentelemetry.exporter.otlp.proto.http.trace_exporter":
            mod = type("M", (), {})()
            setattr(mod, "OTLPSpanExporter", FailingOTLP)
            return mod
        if name == "opentelemetry.sdk.trace.export":
            mod = type("E", (), {})()
            # Minimal placeholders; not reached due to exporter failure
            setattr(mod, "BatchSpanProcessor", object)
            setattr(mod, "ConsoleSpanExporter", object)
            return mod
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError):
        prov.create_opentelemetry()


def test_provider_shutdown_ignores_provider_exception(monkeypatch):
    """Shutdown should swallow provider.shutdown exceptions (console branch)."""
    pytest.importorskip("opentelemetry")
    from src.telemetry_core.providers import opentelemetry_provider as prov

    class FakeTracerProvider:
        def __init__(self, *a, **k):
            pass
        def add_span_processor(self, proc):
            pass
        def shutdown(self):
            raise RuntimeError("shutdown boom")

    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "opentelemetry.sdk.trace":
            mod = type("T", (), {})()
            setattr(mod, "TracerProvider", FakeTracerProvider)
            return mod
        if name == "opentelemetry.sdk.trace.export":
            mod = type("E", (), {})()
            # Simple pass-through BatchSpanProcessor/ConsoleSpanExporter
            setattr(mod, "BatchSpanProcessor", lambda exporter: exporter)
            class SilentExporter:
                def export(self, spans):
                    return 0
                def shutdown(self):
                    pass
            setattr(mod, "ConsoleSpanExporter", SilentExporter)
            return mod
        return real_import(name, *args, **kwargs)

    # Ensure console branch (no OTLP endpoint)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    import os as _os
    _os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)

    import builtins as _b
    monkeypatch.setattr(_b, "__import__", fake_import)

    telemetry = prov.create_opentelemetry()
    # Should swallow shutdown exception
    telemetry.shutdown()



def test_provider_otlp_import_error_fallback(monkeypatch):
    """If OTLP import fails, ImportError should be raised (no fallback)."""
    import builtins
    pytest.importorskip("opentelemetry")
    from src.telemetry_core.providers import opentelemetry_provider as prov

    # Simulate import error for OTLP exporter
    real_import = builtins.__import__
    def fake_import(name, *args, **kwargs):
        if name == "opentelemetry.exporter.otlp.proto.http.trace_exporter":
            raise ImportError("No OTLP exporter")
        if name == "opentelemetry.sdk.trace.export":
            mod = type("E", (), {})()
            # Provide a silent ConsoleSpanExporter
            class SilentExporter:
                def export(self, spans):
                    return 0
                def shutdown(self):
                    pass
            setattr(mod, "BatchSpanProcessor", lambda exporter: exporter)
            setattr(mod, "ConsoleSpanExporter", SilentExporter)
            return mod
        return real_import(name, *args, **kwargs)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError):
        prov.create_opentelemetry()
