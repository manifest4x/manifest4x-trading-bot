"""Turns a raw webhook body into a Signal. Pure: no I/O, no logging.

Supported bodies:
1. JSON:       {"direction": "LONG", "ticker": "EURUSD", "price": "1.085", "time": "...", ...}
2. Pine text:  MANIFEST4X SHORT | Pair: EURUSD | Entry: 1.085 | Time: ... | SL: ... | TP1 65% at 1R
Anything else becomes an UNRECOGNIZED signal that carries the raw text.
"""

import json
import re

from app.domain.errors import InvalidPayloadError
from app.domain.signal import Direction, Signal, SignalSource

_PINE_HEAD = re.compile(r"^\s*MANIFEST4X\s+(LONG|SHORT)\b", re.IGNORECASE)
_TP = re.compile(r"^TP([12])\s+(.+)$", re.IGNORECASE)


def parse_signal(body: str) -> Signal:
    text = body.strip()
    if not text:
        raise InvalidPayloadError("empty body")

    if text.startswith("{"):
        parsed = _try_json(text)
        if parsed is not None:
            return _from_json(parsed, raw=text)

    if _PINE_HEAD.match(text):
        return _from_pine_text(text)

    return Signal(source=SignalSource.UNRECOGNIZED, raw=text)


def _try_json(text: str) -> dict | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _from_json(data: dict, raw: str) -> Signal:
    try:
        direction = Direction(str(data.get("direction", "")).upper())
    except ValueError:
        raise InvalidPayloadError("direction must be LONG or SHORT") from None

    def get(*keys: str) -> str | None:
        for key in keys:
            if data.get(key) not in (None, ""):
                return str(data[key])
        return None

    return Signal(
        source=SignalSource.JSON,
        raw=raw,
        direction=direction,
        symbol=get("ticker", "symbol", "pair"),
        price=get("price", "entry", "close"),
        time=get("time"),
        confluence=get("confluence"),
        sl=get("sl"),
        tp1=get("tp1"),
        tp2=get("tp2"),
    )


def _from_pine_text(text: str) -> Signal:
    segments = [s.strip() for s in text.split("|")]
    direction = Direction(_PINE_HEAD.match(segments[0]).group(1).upper())  # type: ignore[union-attr]

    values: dict[str, str] = {}
    for segment in segments[1:]:
        tp = _TP.match(segment)
        if tp:
            values[f"tp{tp.group(1)}"] = tp.group(2).strip()
        elif ":" in segment:
            key, _, value = segment.partition(":")
            values[key.strip().lower()] = value.strip()

    return Signal(
        source=SignalSource.PINE_TEXT,
        raw=text,
        direction=direction,
        symbol=values.get("pair"),
        price=values.get("entry"),
        time=values.get("time"),
        confluence=values.get("confluence"),
        sl=values.get("sl"),
        tp1=values.get("tp1"),
        tp2=values.get("tp2"),
    )
