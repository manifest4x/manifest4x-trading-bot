"""One wide event per request, enriched by any layer and emitted once by the middleware.

Layers call `add_context` / `append_to` without knowing about HTTP. Outside a request
(e.g. a unit test of a service) these calls are no-ops.
"""

from contextvars import ContextVar
from typing import Any

_current: ContextVar[dict[str, Any] | None] = ContextVar("wide_event", default=None)


def begin(**base: Any) -> dict[str, Any]:
    event = dict(base)
    _current.set(event)
    return event


def end() -> None:
    _current.set(None)


def add_context(**fields: Any) -> None:
    event = _current.get()
    if event is None:
        return
    for key, value in fields.items():
        if isinstance(value, dict) and isinstance(event.get(key), dict):
            event[key].update(value)
        else:
            event[key] = value


def append_to(key: str, item: Any) -> None:
    event = _current.get()
    if event is None:
        return
    event.setdefault(key, []).append(item)
