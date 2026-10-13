import json
import logging

import pytest

from app.observability.logging import EVENT_LOGGER, JsonFormatter
from tests.conftest import PINE_SHORT, TEST_TOKEN

URL = f"/webhook/tradingview?token={TEST_TOKEN}"


@pytest.fixture
def events(caplog):
    caplog.set_level(logging.INFO, logger=EVENT_LOGGER)

    def collect() -> list[dict]:
        return [r.event for r in caplog.records if r.name == EVENT_LOGGER]

    return collect


def test_emits_one_enriched_event_per_request(client, events):
    client.post(URL, content=PINE_SHORT)

    (event,) = events()
    assert event["method"] == "POST"
    assert event["path"] == "/webhook/tradingview"
    assert event["status_code"] == 200
    assert event["outcome"] == "success"
    assert event["duration_ms"] >= 0
    assert event["parse_format"] == "pine_text"
    assert event["signal"]["direction"] == "SHORT"
    assert event["signal"]["symbol"] == "EURUSD"
    assert event["notifiers"][0]["name"] == "fake"
    assert event["notifiers"][0]["ok"] is True
    assert event["request_id"]


def test_failures_still_emit_an_event_with_error_details(client, notifier, events):
    notifier.fail = True

    client.post(URL, content=PINE_SHORT)

    (event,) = events()
    assert event["status_code"] == 502
    assert event["outcome"] == "error"
    assert event["error"]["type"] == "NotificationDeliveryError"
    assert event["error"]["retriable"] is True
    assert event["notifiers"][0]["ok"] is False


def test_event_never_contains_the_token(client, events):
    client.post(URL, content=PINE_SHORT)
    client.post("/webhook/tradingview?token=wrong", content=PINE_SHORT)

    assert all(TEST_TOKEN not in json.dumps(e) and "wrong" not in json.dumps(e) for e in events())


def test_health_checks_are_not_logged(client, events):
    client.get("/health")

    assert events() == []


def test_formatter_outputs_single_json_line():
    record = logging.LogRecord("n", logging.INFO, "f", 1, "request", None, None)
    record.event = {"path": "/x", "status_code": 200}

    line = JsonFormatter().format(record)

    assert "\n" not in line
    assert json.loads(line)["path"] == "/x"
