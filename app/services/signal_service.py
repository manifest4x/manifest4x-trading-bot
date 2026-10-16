import time
from collections.abc import Sequence
from datetime import UTC, datetime

from app.domain.errors import NotificationDeliveryError
from app.domain.notification import Notification, Tone
from app.domain.signal import Direction, Signal
from app.observability.wide_event import append_to
from app.providers.notifiers.base import Notifier

_FOOTER = "Manifest4X"


class SignalService:
    """Turns a signal into a notification and delivers it through every notifier.

    One notifier failing never prevents the others from being tried. If every notifier
    fails, the error is raised so the caller can tell TradingView/ops that nothing went out.
    """

    def __init__(self, notifiers: Sequence[Notifier]) -> None:
        self._notifiers = list(notifiers)

    async def process(self, signal: Signal) -> None:
        notification = self._to_notification(signal)
        failures: list[NotificationDeliveryError] = []

        for notifier in self._notifiers:
            started = time.perf_counter()
            result: dict = {"name": notifier.name, "ok": True}
            try:
                await notifier.send(notification)
            except NotificationDeliveryError as exc:
                failures.append(exc)
                result.update(ok=False, error_type=type(exc).__name__, status_code=exc.status_code)
            result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
            append_to("notifiers", result)

        if self._notifiers and len(failures) == len(self._notifiers):
            raise failures[0]

    @staticmethod
    def _to_notification(signal: Signal) -> Notification:
        if signal.direction is None:
            return Notification(
                title="Manifest4X alert", body=signal.raw, tone=Tone.NEUTRAL, footer=_FOOTER
            )

        is_long = signal.direction is Direction.LONG
        marker = "🟢" if is_long else "🔴"
        title = f"{marker} {signal.direction.value}"
        if signal.symbol:
            title += f" · {signal.symbol}"

        candidates = {
            "📍 Entry": signal.price,
            "🛑 Stop loss": signal.sl,
            "🎯 TP1": signal.tp1,
            "🎯 TP2": signal.tp2,
            "📊 Setup": signal.confluence,
        }
        return Notification(
            title=title,
            fields={name: value for name, value in candidates.items() if value},
            tone=Tone.POSITIVE if is_long else Tone.NEGATIVE,
            footer=_FOOTER,
            timestamp=_parse_time(signal.time),
        )


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
