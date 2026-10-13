"""Composition root: the only place where concrete classes are wired together."""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import Settings
from app.controllers.webhook_controller import WebhookController
from app.domain.errors import (
    DomainError,
    InvalidPayloadError,
    NotificationDeliveryError,
    UnauthorizedError,
)
from app.observability.logging import configure_logging
from app.observability.middleware import WideEventMiddleware
from app.observability.wide_event import add_context
from app.providers.notifiers.base import Notifier
from app.providers.notifiers.factory import build_notifiers
from app.routes import health, webhook
from app.services.signal_service import SignalService

# TradingView expects an answer within ~3s, so provider calls must give up sooner.
PROVIDER_TIMEOUT_SECONDS = 2.5

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    InvalidPayloadError: 422,
    NotificationDeliveryError: status.HTTP_502_BAD_GATEWAY,
}


def create_app(
    settings: Settings | None = None, notifiers: Sequence[Notifier] | None = None
) -> FastAPI:
    """Build the app. Pass `notifiers` to bypass the provider factory (used by tests)."""
    settings = settings or Settings()  # type: ignore[call-arg]
    configure_logging(settings.log_level)

    client: httpx.AsyncClient | None = None
    if notifiers is None:
        client = httpx.AsyncClient(timeout=PROVIDER_TIMEOUT_SECONDS)
        notifiers = build_notifiers(settings, client)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if client is not None:
            await client.aclose()

    app = FastAPI(title=settings.service_name, version=settings.service_version, lifespan=lifespan)
    app.state.settings = settings
    app.state.controller = WebhookController(SignalService(notifiers))

    app.add_middleware(
        WideEventMiddleware, service=settings.service_name, version=settings.service_version
    )
    app.include_router(health.router)
    app.include_router(webhook.router)

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        add_context(
            error={"type": type(exc).__name__, "message": str(exc), "retriable": exc.retriable}
        )
        code = _STATUS_BY_ERROR.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=code, content={"error": type(exc).__name__})

    return app
