from typing import Protocol

from app.domain.notification import Notification


class Notifier(Protocol):
    """Port every chat provider (Discord, Telegram, ...) implements."""

    name: str

    async def send(self, notification: Notification) -> None:
        """Deliver the notification or raise NotificationDeliveryError."""
        ...
