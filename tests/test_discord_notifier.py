from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.domain.errors import NotificationDeliveryError
from app.domain.notification import Notification, Tone
from app.providers.notifiers.discord import DiscordNotifier

URL = "https://discord.com/api/v10/channels/123/messages"


@pytest.fixture
async def notifier():
    async with httpx.AsyncClient() as client:
        yield DiscordNotifier(client, bot_token="bot-secret", channel_id="123")


@respx.mock
async def test_posts_embed_with_bot_authorization(notifier):
    route = respx.post(URL).respond(200, json={"id": "1"})

    await notifier.send(
        Notification(
            title="🔴 SHORT · EURUSD",
            fields={"Entry": "1.085", "TP1": "65% at 1R"},
            tone=Tone.NEGATIVE,
            footer="Manifest4X",
            timestamp=datetime(2026, 10, 16, 14, 45, tzinfo=UTC),
        )
    )

    request = route.calls.last.request
    assert request.headers["authorization"] == "Bot bot-secret"
    embed = httpx.Response(200, content=request.content).json()["embeds"][0]
    assert embed["title"] == "🔴 SHORT · EURUSD"
    assert embed["description"] == "**Entry:** 1.085\n**TP1:** 65% at 1R"
    assert embed["timestamp"] == "2026-10-16T14:45:00+00:00"
    assert embed["footer"] == {"text": "Manifest4X"}
    assert embed["color"] == 0xE74C3C


@respx.mock
async def test_http_error_status_raises_delivery_error(notifier):
    respx.post(URL).respond(403)

    with pytest.raises(NotificationDeliveryError) as exc_info:
        await notifier.send(Notification(title="x"))

    assert exc_info.value.status_code == 403


@respx.mock
async def test_network_error_raises_delivery_error(notifier):
    respx.post(URL).mock(side_effect=httpx.ConnectTimeout("slow"))

    with pytest.raises(NotificationDeliveryError):
        await notifier.send(Notification(title="x"))
