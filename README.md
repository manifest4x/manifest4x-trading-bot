# manifest4x-trading-bot

Receives TradingView alerts from the Manifest4X indicator and forwards them to a chat provider
(Discord for now).

```
TradingView alert ──POST /webhook/tradingview?token=…──▶ bot ──▶ Discord channel
```

## Run

```bash
cp .env.example .env        # then fill it in
docker compose up --build
curl localhost:8000/health
```

Local development:

```bash
uv venv --python 3.12 && uv pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/uvicorn app.main:create_app --factory --reload --no-access-log
```

## Configuration (`.env`)

| Variable | Description |
| --- | --- |
| `WEBHOOK_SECRET` | Shared secret. TradingView must call `/webhook/tradingview?token=<secret>`. |
| `DISCORD_BOT_TOKEN` | Bot token. |
| `DISCORD_CHANNEL_ID` | Channel the bot posts to. |
| `NOTIFIERS` | Comma separated providers (`discord`). |
| `LOG_LEVEL` | `INFO` by default. |

## Create the Discord bot

1. <https://discord.com/developers/applications> → New Application → Bot → Reset Token (copy it).
2. OAuth2 → URL Generator → scope `bot`, permissions `Send Messages` + `Embed Links` → open the URL and add the bot to your server.
3. Discord Settings → Advanced → enable Developer Mode, then right-click the channel → Copy Channel ID.

## TradingView setup

1. The bot must be reachable over public HTTPS (VPS + reverse proxy, or `cloudflared`/`ngrok` for testing).
2. Create one alert for **Manifest4X LONG** and one for **Manifest4X SHORT**
   (not "Any Signal": it carries no direction).
3. Alert → Notifications → Webhook URL: `https://<your-host>/webhook/tradingview?token=<WEBHOOK_SECRET>`.
4. Leave the message as the indicator defines it. A JSON message also works:
   `{"direction":"LONG","ticker":"{{ticker}}","price":"{{close}}","time":"{{time}}"}`
   (optional keys: `confluence`, `sl`, `tp1`, `tp2`).

Responses: `200` sent, `401` bad token, `422` unusable payload, `502` every provider failed.

## Architecture

```
routes/        HTTP binding + token check
controllers/   body → Signal → service
services/      signal_parser (pure), signal_service (Signal → Notification → notifiers)
providers/     notifiers/base.py (Notifier protocol), discord.py, factory.py
domain/        Signal, Notification, errors
observability/ wide event (one structured JSON log line per request)
main.py        composition root
```

### Add a provider (e.g. Telegram)

1. Create `app/providers/notifiers/telegram.py` with a class implementing `Notifier`
   (`name` + `async send(Notification)`), rendering the neutral `Notification` its own way.
2. Register its builder in `app/providers/notifiers/factory.py`.
3. Add `telegram` to `NOTIFIERS` and its settings to `config.py`.

Nothing else changes.

### Logging

One JSON line per request (wide event) with request, signal, per-notifier results, status and
duration. The token and bot credentials are never logged. Uvicorn's access log is disabled
because it would print the query string.
