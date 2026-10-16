import pytest

from app.domain.errors import NotificationDeliveryError
from app.domain.notification import Tone
from app.services.signal_parser import parse_signal
from app.services.signal_service import SignalService
from tests.conftest import PINE_LONG, PINE_SHORT, FakeNotifier


async def test_short_signal_becomes_negative_notification():
    notifier = FakeNotifier()

    await SignalService([notifier]).process(parse_signal(PINE_SHORT))

    (sent,) = notifier.sent
    assert sent.title == "🔴 SHORT · EURUSD"
    assert sent.tone is Tone.NEGATIVE
    assert sent.fields["📍 Entry"] == "1.08500"
    assert sent.fields["🎯 TP1"] == "65% at 1R"
    assert sent.fields["📊 Setup"].startswith("ORB Breakdown")
    assert sent.timestamp.isoformat() == "2026-10-13T14:35:00+00:00"


async def test_long_signal_becomes_positive_notification():
    notifier = FakeNotifier()

    await SignalService([notifier]).process(parse_signal(PINE_LONG))

    assert notifier.sent[0].tone is Tone.POSITIVE


async def test_unrecognized_signal_forwards_raw_text():
    notifier = FakeNotifier()

    await SignalService([notifier]).process(parse_signal("something odd"))

    assert notifier.sent[0].body == "something odd"


async def test_one_failing_notifier_does_not_block_the_others():
    broken, healthy = FakeNotifier("broken", fail=True), FakeNotifier("healthy")

    await SignalService([broken, healthy]).process(parse_signal(PINE_LONG))

    assert len(healthy.sent) == 1


async def test_raises_when_every_notifier_fails():
    service = SignalService([FakeNotifier("a", fail=True), FakeNotifier("b", fail=True)])

    with pytest.raises(NotificationDeliveryError):
        await service.process(parse_signal(PINE_LONG))
