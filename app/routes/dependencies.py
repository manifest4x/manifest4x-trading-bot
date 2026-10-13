import hmac

from fastapi import Depends, Query, Request

from app.config import Settings
from app.controllers.webhook_controller import WebhookController
from app.domain.errors import UnauthorizedError


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_controller(request: Request) -> WebhookController:
    return request.app.state.controller


def require_token(
    token: str = Query(default=""), settings: Settings = Depends(get_settings)
) -> None:
    expected = settings.webhook_secret.get_secret_value()
    if not hmac.compare_digest(token.encode(), expected.encode()):
        raise UnauthorizedError("invalid token")
