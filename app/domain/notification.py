from dataclasses import dataclass, field
from enum import StrEnum


class Tone(StrEnum):
    """Provider-neutral mood of a message; each provider maps it to its own styling."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class Notification:
    """A provider-neutral message. Providers decide how to render it."""

    title: str
    body: str = ""
    fields: dict[str, str] = field(default_factory=dict)
    tone: Tone = Tone.NEUTRAL
    footer: str = ""
