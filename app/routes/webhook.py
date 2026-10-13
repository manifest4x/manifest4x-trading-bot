from fastapi import APIRouter, Depends, Request

from app.controllers.webhook_controller import WebhookController
from app.routes.dependencies import get_controller, require_token

router = APIRouter()


@router.post("/webhook/tradingview", dependencies=[Depends(require_token)])
async def tradingview_webhook(
    request: Request, controller: WebhookController = Depends(get_controller)
) -> dict[str, str]:
    # TradingView sends text/plain unless the message is valid JSON, so read the raw body.
    return await controller.handle(await request.body())
