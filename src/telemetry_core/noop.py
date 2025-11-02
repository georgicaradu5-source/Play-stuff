from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .types import Attributes, SpanLike, Telemetry


class _NoOpSpan:
    def end(self) -> None:  # noqa: D401
        pass

    def add_event(self, name: str, attrs: Attributes | None = None) -> None:  # noqa: D401, ARG002
        pass

    def set_attribute(self, key: str, value: Any) -> None:  # noqa: D401, ARG002
        pass

    def record_exception(self, err: BaseException) -> None:  # noqa: D401, ARG002
        pass


class NoOpTelemetry(Telemetry):
    def init(self) -> None:  # noqa: D401
        pass

    def shutdown(self) -> None:  # noqa: D401
        pass

    def event(self, name: str, attrs: Attributes | None = None) -> None:  # noqa: D401, ARG002
        pass

    def start_span(self, name: str, attrs: Attributes | None = None) -> SpanLike:  # noqa: D401, ARG002
        return _NoOpSpan()

    def with_span(self, name: str, fn: Callable[[SpanLike], Any], attrs: Attributes | None = None) -> Any:  # noqa: D401, ARG002
        return fn(_NoOpSpan())

    def set_user(self, user: dict[str, Any] | None = None) -> None:  # noqa: D401, ARG002
        pass

    def set_attributes(self, attrs: Attributes) -> None:  # noqa: D401, ARG002
        pass

    def record_exception(self, err: BaseException, attrs: Attributes | None = None) -> None:  # noqa: D401, ARG002
        pass
