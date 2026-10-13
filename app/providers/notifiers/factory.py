from collections.abc import Callable

import httpx

from app.config import Settings
from app.providers.notifiers.base import Notifier
from app.providers.notifiers.discord import DiscordNotifier


def _build_discord(settings: Settings, client: httpx.AsyncClient) -> Notifier:
    token = settings.discord_bot_token.get_secret_value()
    if not token or not settings.discord_channel_id:
        raise ValueError("discord requires DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID")
    return DiscordNotifier(client, token, settings.discord_channel_id)


# To add a provider (e.g. telegram): implement Notifier and register its builder here.
_BUILDERS: dict[str, Callable[[Settings, httpx.AsyncClient], Notifier]] = {
    "discord": _build_discord,
}


def build_notifiers(settings: Settings, client: httpx.AsyncClient) -> list[Notifier]:
    names = settings.notifier_names
    unknown = [name for name in names if name not in _BUILDERS]
    if unknown:
        raise ValueError(f"unknown notifiers: {', '.join(unknown)}")
    if not names:
        raise ValueError("NOTIFIERS must enable at least one provider")
    return [_BUILDERS[name](settings, client) for name in names]
