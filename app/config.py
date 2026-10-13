from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "manifest4x-trading-bot"
    service_version: str = "0.1.0"
    log_level: str = "INFO"

    webhook_secret: SecretStr

    # Comma separated provider names, e.g. "discord" or "discord,telegram".
    notifiers: str = "discord"

    discord_bot_token: SecretStr = SecretStr("")
    discord_channel_id: str = ""

    @property
    def notifier_names(self) -> list[str]:
        return [name.strip().lower() for name in self.notifiers.split(",") if name.strip()]
