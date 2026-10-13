import json
import logging
import sys
from datetime import UTC, datetime

ROOT_LOGGER = "manifest4x"
EVENT_LOGGER = f"{ROOT_LOGGER}.events"


class JsonFormatter(logging.Formatter):
    """Renders a record as a single JSON line.

    Wide events travel in `record.event`; any other record becomes {"message": ...}.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
        }
        event = getattr(record, "event", None)
        if event is not None:
            payload.update(event)
        else:
            payload["message"] = record.getMessage()
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    logger = logging.getLogger(ROOT_LOGGER)
    logger.setLevel(level.upper())
    if not any(isinstance(h.formatter, JsonFormatter) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
