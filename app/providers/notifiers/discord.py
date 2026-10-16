import httpx

from app.domain.errors import NotificationDeliveryError
from app.domain.notification import Notification, Tone

API_BASE = "https://discord.com/api/v10"

_COLORS = {
    Tone.POSITIVE: 0x2ECC71,
    Tone.NEGATIVE: 0xE74C3C,
    Tone.NEUTRAL: 0x95A5A6,
}


class DiscordNotifier:
    """Sends notifications as embeds through Discord's REST API using a bot token.

    Only HTTP is needed to post messages, so there is no gateway connection.
    """

    name = "discord"

    def __init__(self, client: httpx.AsyncClient, bot_token: str, channel_id: str) -> None:
        self._client = client
        self._bot_token = bot_token
        self._url = f"{API_BASE}/channels/{channel_id}/messages"

    async def send(self, notification: Notification) -> None:
        try:
            response = await self._client.post(
                self._url,
                json={"embeds": [self._to_embed(notification)]},
                headers={"Authorization": f"Bot {self._bot_token}"},
            )
        except httpx.HTTPError as exc:
            reason = f"request failed: {type(exc).__name__}"
            raise NotificationDeliveryError(self.name, reason) from exc

        if response.status_code >= 400:
            raise NotificationDeliveryError(
                self.name, f"returned HTTP {response.status_code}", response.status_code
            )

    @staticmethod
    def _to_embed(notification: Notification) -> dict:
        embed: dict = {
            "title": notification.title[:256],
            "color": _COLORS[notification.tone],
        }
        # One "**label:** value" line per field: easier to scan than Discord's column grid.
        lines = [f"**{name}:** {value}" for name, value in notification.fields.items()]
        description = "\n".join(lines)
        if notification.body:
            description += ("\n\n" if lines else "") + notification.body
        if description:
            embed["description"] = description[:4000]
        if notification.footer:
            embed["footer"] = {"text": notification.footer[:2048]}
        if notification.timestamp:
            embed["timestamp"] = notification.timestamp.isoformat()
        return embed
