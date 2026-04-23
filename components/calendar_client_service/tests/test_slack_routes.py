"""Unit tests for Slack webhook routes."""

import hashlib
import hmac
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from calendar_client_service.app import app
from calendar_client_service.slack_routes import _handle_message_event, _verify_slack_signature


@pytest.fixture
def mock_clients() -> dict[str, Any]:
    """Fixture providing mock AI, OAuth, and Chat clients."""
    return {
        "oauth": MagicMock(),
        "ai": MagicMock(),
        "chat": MagicMock(),
    }


def test_verify_slack_signature_no_secret() -> None:
    """Test signature verification when no secret is configured."""
    with patch.dict("os.environ", clear=True):
        assert _verify_slack_signature(b"body", {}) is True


def test_verify_slack_signature_valid() -> None:
    """Test signature verification with a valid signature."""
    signing_key = "test_key"
    ts = str(int(time.time()))
    body = b"test_body"

    base = f"v0:{ts}:test_body"
    expected = "v0=" + hmac.new(
        signing_key.encode("utf-8"), base.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    headers = {
        "x-slack-request-timestamp": ts,
        "x-slack-signature": expected
    }

    with patch.dict("os.environ", {"SLACK_SIGNING_SECRET": signing_key}):
        assert _verify_slack_signature(body, headers) is True


def test_verify_slack_signature_invalid_timestamp() -> None:
    """Test signature verification with an invalid timestamp."""
    signing_key = "test_key"
    ts = str(int(time.time()) - 600) # 10 mins ago
    body = b"test_body"

    headers = {
        "x-slack-request-timestamp": ts,
        "x-slack-signature": "v0=invalid"
    }

    with patch.dict("os.environ", {"SLACK_SIGNING_SECRET": signing_key}):
        assert _verify_slack_signature(body, headers) is False


def test_verify_slack_signature_invalid_signature() -> None:
    """Test signature verification with an invalid signature."""
    signing_key = "test_key"
    ts = str(int(time.time()))
    body = b"test_body"

    headers = {
        "x-slack-request-timestamp": ts,
        "x-slack-signature": "v0=invalid"
    }

    with patch.dict("os.environ", {"SLACK_SIGNING_SECRET": signing_key}):
        assert _verify_slack_signature(body, headers) is False


@pytest.fixture
def anyio_backend() -> str:
    """Fixture providing the AnyIO backend to use."""
    return "asyncio"


@pytest.mark.anyio
async def test_handle_message_event(mock_clients: dict[str, Any]) -> None:
    """Test handling a basic Slack message event."""
    event = {
        "text": "Hello",
        "channel": "C123",
        "user": "U123"
    }

    mock_clients["ai"].send_message.return_value = "Hi there!"
    mock_clients["oauth"].is_authenticated.return_value = True
    mock_clients["oauth"].get_credentials.return_value = MagicMock()

    with patch.dict(
        "calendar_client_service.slack_routes._slack_user_sessions",
        {"U123": "session1"},
    ), patch("calendar_client_service.slack_routes.GoogleCalendarClient"):
        await _handle_message_event(
            event,
            mock_clients["oauth"],
            mock_clients["ai"],
            mock_clients["chat"],
            "http://testserver",
        )

    mock_clients["ai"].send_message.assert_called_once()
    mock_clients["chat"].send_message.assert_called_once_with(
        channel_id="C123",
        text="Hi there!"
    )


@pytest.mark.anyio
async def test_handle_message_event_bot_message(mock_clients: dict[str, Any]) -> None:
    """Test that bot messages are ignored."""
    event = {
        "text": "Hello",
        "channel": "C123",
        "bot_id": "B123"
    }

    await _handle_message_event(
        event,
        mock_clients["oauth"],
        mock_clients["ai"],
        mock_clients["chat"],
        "http://testserver",
    )

    mock_clients["ai"].send_message.assert_not_called()


@pytest.mark.anyio
async def test_handle_message_event_exception(mock_clients: dict[str, Any]) -> None:
    """Test handling exceptions during message processing."""
    event = {
        "text": "Hello",
        "channel": "C123",
        "user": "U123"
    }

    mock_clients["ai"].send_message.side_effect = Exception("Test Exception")
    mock_clients["oauth"].is_authenticated.return_value = True
    mock_clients["oauth"].get_credentials.return_value = MagicMock()

    with patch.dict(
        "calendar_client_service.slack_routes._slack_user_sessions",
        {"U123": "session1"},
    ), patch("calendar_client_service.slack_routes.GoogleCalendarClient"):
        await _handle_message_event(
            event,
            mock_clients["oauth"],
            mock_clients["ai"],
            mock_clients["chat"],
            "http://testserver",
        )

    mock_clients["chat"].send_message.assert_called_once_with(
        channel_id="C123",
        text="Sorry, I encountered an error processing your request."
    )


def test_slack_events_url_verification() -> None:
    """Test the URL verification challenge."""
    client = TestClient(app)
    payload = {
        "type": "url_verification",
        "challenge": "test_challenge"
    }

    with patch("calendar_client_service.slack_routes._verify_slack_signature", return_value=True):
        response = client.post("/slack/events", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"challenge": "test_challenge"}


def test_slack_events_invalid_signature() -> None:
    """Test event payload with an invalid signature."""
    client = TestClient(app)

    with patch("calendar_client_service.slack_routes._verify_slack_signature", return_value=False):
        response = client.post("/slack/events", json={})

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_slack_events_message() -> None:
    """Test handling a valid message event via the webhook endpoint."""
    client = TestClient(app)
    payload = {
        "event": {
            "type": "message",
            "text": "Hello",
            "channel": "C123"
        }
    }

    with patch("calendar_client_service.slack_routes._verify_slack_signature", return_value=True), \
         patch("calendar_client_service.slack_routes.BackgroundTasks.add_task") as mock_add_task, \
         patch("calendar_client_service.slack_routes.get_oauth_manager"), \
         patch("calendar_client_service.slack_routes.get_ai_client"), \
         patch("calendar_client_service.slack_routes.get_slack_client"):

        # The overrides are set in the app.dependency_overrides directly

        response = client.post("/slack/events", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}
    mock_add_task.assert_called_once()


def test_slack_events_retry() -> None:
    """Test that Slack retries are ignored."""
    client = TestClient(app)
    payload = {
        "event": {
            "type": "message"
        }
    }

    with patch("calendar_client_service.slack_routes._verify_slack_signature", return_value=True):
        response = client.post("/slack/events", json=payload, headers={"x-slack-retry-num": "1"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}
