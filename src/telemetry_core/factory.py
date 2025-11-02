from __future__ import annotations

import os

from .noop import NoOpTelemetry
from .types import Telemetry


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def create_telemetry(provider: str | None = None) -> Telemetry:
    """Create a Telemetry instance based on environment variables.

    - TELEMETRY_ENABLED: default False; when False, returns NoOpTelemetry
    - TELEMETRY_PROVIDER: currently supports 'opentelemetry'
    - OTEL_SERVICE_NAME / OTEL_EXPORTER_OTLP_ENDPOINT respected by provider
    """

    enabled = _bool_env("ENABLE_TELEMETRY", False) or _bool_env("TELEMETRY_ENABLED", False)
    if not enabled:
        return NoOpTelemetry()

    provider_name = provider or os.getenv("TELEMETRY_PROVIDER", "opentelemetry").strip().lower()

    if provider_name in ("otel", "opentelemetry"):
        try:
            from .providers.opentelemetry_provider import create_opentelemetry

            return create_opentelemetry()
        except Exception:
            # Missing dependency or runtime error; fall back silently
            return NoOpTelemetry()

    # Unknown provider, fall back
    return NoOpTelemetry()
