from app.observability.wide_event import add_context
from app.services.signal_parser import parse_signal
from app.services.signal_service import SignalService


class WebhookController:
    """Application entry point for a webhook call: body in, response payload out."""

    def __init__(self, service: SignalService) -> None:
        self._service = service

    async def handle(self, body: bytes) -> dict[str, str]:
        signal = parse_signal(body.decode("utf-8", errors="replace"))
        add_context(
            parse_format=signal.source.value,
            signal={
                "direction": signal.direction.value if signal.direction else None,
                "symbol": signal.symbol,
                "price": signal.price,
                "time": signal.time,
            },
        )
        await self._service.process(signal)
        return {"status": "sent"}
