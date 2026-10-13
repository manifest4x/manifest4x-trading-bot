import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.observability import wide_event
from app.observability.logging import EVENT_LOGGER

logger = logging.getLogger(EVENT_LOGGER)

SKIPPED_PATHS = {"/health"}


class WideEventMiddleware(BaseHTTPMiddleware):
    """Emits exactly one structured event per request, even when the request fails.

    Only the path is logged: the query string carries the webhook token.
    """

    def __init__(self, app: ASGIApp, service: str, version: str) -> None:
        super().__init__(app)
        self._service = service
        self._version = version

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in SKIPPED_PATHS:
            return await call_next(request)

        event = wide_event.begin(
            service=self._service,
            version=self._version,
            request_id=request.headers.get("x-request-id") or uuid.uuid4().hex,
            method=request.method,
            path=request.url.path,
        )
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            wide_event.add_context(error={"type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            event["status_code"] = status_code
            event["outcome"] = "success" if status_code < 400 else "error"
            event["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
            logger.info("request", extra={"event": event})
            wide_event.end()
