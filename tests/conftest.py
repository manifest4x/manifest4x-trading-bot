import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.domain.errors import NotificationDeliveryError
from app.domain.notification import Notification
from app.main import create_app

TEST_TOKEN = "test-token"

PINE_SHORT = (
    "MANIFEST4X SHORT | Pair: EURUSD | Entry: 1.08500 | Time: 2026-10-13T14:35:00Z | "
    "Confluence: ORB Breakdown + Fib Zone 45-65% + 5M Bearish Rejection | "
    "SL: above 5M rejection high | TP1 65% at 1R | TP2 35% at 2R"
)
PINE_LONG = (
    "MANIFEST4X LONG | Pair: EURUSD | Entry: 1.08200 | Time: 2026-10-13T14:40:00Z | "
    "Confluence: ORB Breakout + Fib Zone 45-65% + 5M Bullish Rejection | "
    "SL: below 5M rejection low | TP1 65% at 1R | TP2 35% at 2R"
)


class FakeNotifier:
    def __init__(self, name: str = "fake", fail: bool = False) -> None:
        self.name = name
        self.fail = fail
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        if self.fail:
            raise NotificationDeliveryError(self.name, "boom", 500)
        self.sent.append(notification)


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()


@pytest.fixture
def client(notifier: FakeNotifier) -> TestClient:
    settings = Settings(webhook_secret=SecretStr(TEST_TOKEN), _env_file=None)  # type: ignore[call-arg]
    return TestClient(create_app(settings, notifiers=[notifier]))
