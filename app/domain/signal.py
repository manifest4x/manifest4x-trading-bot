from dataclasses import dataclass
from enum import StrEnum


class Direction(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class SignalSource(StrEnum):
    JSON = "json"
    PINE_TEXT = "pine_text"
    UNRECOGNIZED = "unrecognized"


@dataclass(frozen=True)
class Signal:
    """A trading alert coming from TradingView.

    Values are kept as display strings: the bot only relays them, it never does math on them.
    `direction` is None when the payload could not be understood (`raw` still holds the text).
    """

    source: SignalSource
    raw: str
    direction: Direction | None = None
    symbol: str | None = None
    price: str | None = None
    time: str | None = None
    confluence: str | None = None
    sl: str | None = None
    tp1: str | None = None
    tp2: str | None = None
