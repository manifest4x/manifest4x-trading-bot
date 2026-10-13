from tests.conftest import PINE_SHORT, TEST_TOKEN

URL = "/webhook/tradingview"


def test_valid_pine_text_is_delivered(client, notifier):
    response = client.post(f"{URL}?token={TEST_TOKEN}", content=PINE_SHORT)

    assert response.status_code == 200
    assert response.json() == {"status": "sent"}
    assert len(notifier.sent) == 1


def test_valid_json_is_delivered(client, notifier):
    response = client.post(
        f"{URL}?token={TEST_TOKEN}", json={"direction": "LONG", "ticker": "EURUSD", "price": 1.1}
    )

    assert response.status_code == 200
    assert notifier.sent[0].title == "🟢 LONG · EURUSD"


def test_missing_token_is_unauthorized(client, notifier):
    response = client.post(URL, content=PINE_SHORT)

    assert response.status_code == 401
    assert notifier.sent == []


def test_wrong_token_is_unauthorized(client, notifier):
    response = client.post(f"{URL}?token=nope", content=PINE_SHORT)

    assert response.status_code == 401
    assert notifier.sent == []


def test_empty_body_is_unprocessable(client):
    response = client.post(f"{URL}?token={TEST_TOKEN}", content="")

    assert response.status_code == 422


def test_provider_failure_returns_bad_gateway(client, notifier):
    notifier.fail = True

    response = client.post(f"{URL}?token={TEST_TOKEN}", content=PINE_SHORT)

    assert response.status_code == 502


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
