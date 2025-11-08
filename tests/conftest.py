import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Global autouse tweak: silence noisy ConsoleSpanExporter when OpenTelemetry is present
# Avoids intermittent "I/O operation on closed file" warnings from ConsoleSpanExporter.

def pytest_configure(config):
    try:
        # Patch the exporter at the source module where create_opentelemetry imports from
        import opentelemetry.sdk.trace.export as exp

        class SilentExporter:  # minimal API
            def export(self, spans):
                return 0

            def shutdown(self):
                pass

        exp.ConsoleSpanExporter = SilentExporter  # type: ignore[attr-defined]
    except Exception:
        # If OpenTelemetry is not installed, ignore silently
        pass
