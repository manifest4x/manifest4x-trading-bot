import pytest

from app.domain.errors import InvalidPayloadError
from app.domain.signal import Direction, SignalSource
from app.services.signal_parser import parse_signal
from tests.conftest import PINE_LONG, PINE_SHORT


def test_parses_pine_short_text():
    signal = parse_signal(PINE_SHORT)

    assert signal.source is SignalSource.PINE_TEXT
    assert signal.direction is Direction.SHORT
    assert signal.symbol == "EURUSD"
    assert signal.price == "1.08500"
    assert signal.time == "2026-10-13T14:35:00Z"
    assert signal.confluence.startswith("ORB Breakdown")
    assert signal.sl == "above 5M rejection high"
    assert signal.tp1 == "65% at 1R"
    assert signal.tp2 == "35% at 2R"


def test_parses_pine_long_text():
    signal = parse_signal(PINE_LONG)

    assert signal.direction is Direction.LONG
    assert signal.price == "1.08200"


def test_parses_json():
    body = '{"direction": "long", "ticker": "EURUSD", "price": 1.085, "sl": 1.08, "tp1": 1.09}'

    signal = parse_signal(body)

    assert signal.source is SignalSource.JSON
    assert signal.direction is Direction.LONG
    assert signal.symbol == "EURUSD"
    assert signal.price == "1.085"
    assert signal.sl == "1.08"
    assert signal.tp1 == "1.09"
    assert signal.tp2 is None


def test_json_with_invalid_direction_is_rejected():
    with pytest.raises(InvalidPayloadError):
        parse_signal('{"direction": "SIDEWAYS"}')


def test_unrecognized_text_is_kept_raw():
    body = "MANIFEST4X SIGNAL | EURUSD | 1.085 | 2026-10-13 | Check your chart now."

    signal = parse_signal(body)

    assert signal.source is SignalSource.UNRECOGNIZED
    assert signal.direction is None
    assert signal.raw == body


@pytest.mark.parametrize("body", ["", "   \n"])
def test_empty_body_is_rejected(body):
    with pytest.raises(InvalidPayloadError):
        parse_signal(body)
