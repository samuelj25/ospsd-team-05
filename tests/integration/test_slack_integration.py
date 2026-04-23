"""Integration tests for the /slack/events webhook endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest
from calendar_client_service.app import create_app
from calendar_client_service.dependencies import get_ai_client, get_oauth_manager, get_slack_client
from calendar_client_service.slack_routes import map_slack_user_to_session
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

    from ai_client_api.client import AbstractAIClient
    from chat_client_api.client import ChatClient
    from google_calendar_client_impl.auth import WebOAuthManager

_USER = "U_TEST_001"
_CHANNEL = "C_TEST_001"
_SESSION = "session-test-abc"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure SLACK_SIGNING_SECRET is unset so tests skip signature verification."""
    monkeypatch.delenv("SLACK_SIGNING_SECRET", raising=False)


@pytest.fixture
def mock_ai() -> AbstractAIClient:
    """Mocked AI client that immediately returns a canned reply."""
    m = MagicMock()
    m.send_message.return_value = "You have no events today."
    return cast("AbstractAIClient", m)


@pytest.fixture
def mock_chat() -> ChatClient:
    """Mocked Slack chat client."""
    return cast("ChatClient", MagicMock())


@pytest.fixture
def mock_oauth() -> WebOAuthManager:
    """Mocked OAuth manager with a pre-authenticated session."""
    m = MagicMock()
    m.is_authenticated.return_value = True
    m.get_credentials.return_value = MagicMock()
    return cast("WebOAuthManager", m)


@pytest.fixture
def client(
    mock_ai: AbstractAIClient,
    mock_chat: ChatClient,
    mock_oauth: WebOAuthManager,
) -> Generator[TestClient, None, None]:
    """TestClient with all external deps mocked, GoogleCalendarClient patched."""
    map_slack_user_to_session(_USER, _SESSION)
    app = create_app()
    app.dependency_overrides[get_ai_client] = lambda: mock_ai
    app.dependency_overrides[get_slack_client] = lambda: mock_chat
    app.dependency_overrides[get_oauth_manager] = lambda: mock_oauth

    with patch("calendar_client_service.slack_routes.GoogleCalendarClient") as mock_gc:
        mock_gc.return_value = MagicMock()
        yield TestClient(app, raise_server_exceptions=True)


def _msg(text: str, user: str = _USER, channel: str = _CHANNEL) -> dict[str, Any]:
    """Build a minimal Slack message event payload."""
    return {
        "type": "event_callback",
        "event": {"type": "message", "text": text, "channel": channel, "user": user},
    }


# ---------------------------------------------------------------------------
# URL verification
# ---------------------------------------------------------------------------


class TestUrlVerification:
    """Slack url_verification one-time handshake."""

    def test_echoes_challenge(self, client: TestClient) -> None:
        resp = client.post(
            "/slack/events",
            json={"type": "url_verification", "challenge": "abc-xyz"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"challenge": "abc-xyz"}


# ---------------------------------------------------------------------------
# Message events
# ---------------------------------------------------------------------------


class TestMessageEvents:
    """Normal Slack message events trigger the AI + calendar loop."""

    def test_returns_200_with_empty_body(self, client: TestClient) -> None:
        resp = client.post("/slack/events", json=_msg("Hello!"))
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_ai_client_receives_user_text(
        self, client: TestClient, mock_ai: AbstractAIClient
    ) -> None:
        client.post("/slack/events", json=_msg("What's on my calendar today?"))

        cast("MagicMock", mock_ai).send_message.assert_called_once()
        prompt: str = cast("MagicMock", mock_ai).send_message.call_args.kwargs.get("prompt", "")
        assert "What's on my calendar today?" in prompt

    def test_reply_posted_to_correct_channel(
        self, client: TestClient, mock_chat: ChatClient
    ) -> None:
        client.post("/slack/events", json=_msg("Hello!", channel="C_CUSTOM"))

        cast("MagicMock", mock_chat).send_message.assert_called()
        kwargs = cast("MagicMock", mock_chat).send_message.call_args.kwargs
        assert kwargs.get("channel_id") == "C_CUSTOM"

    def test_bot_messages_are_ignored(
        self, client: TestClient, mock_ai: AbstractAIClient
    ) -> None:
        payload: dict[str, Any] = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "text": "Bot reply",
                "channel": _CHANNEL,
                "user": _USER,
                "bot_id": "B_BOT_001",
            },
        }
        client.post("/slack/events", json=payload)
        cast("MagicMock", mock_ai).send_message.assert_not_called()

    def test_slack_retry_header_short_circuits(
        self, client: TestClient, mock_ai: AbstractAIClient
    ) -> None:
        resp = client.post(
            "/slack/events",
            json=_msg("Retry!"),
            headers={"x-slack-retry-num": "1"},
        )
        assert resp.status_code == 200
        cast("MagicMock", mock_ai).send_message.assert_not_called()


# ---------------------------------------------------------------------------
# Unauthenticated user
# ---------------------------------------------------------------------------


class TestUnauthenticatedUser:
    """Users without a valid OAuth session receive a login prompt."""

    def test_login_prompt_sent_when_unauthenticated(
        self,
        mock_ai: AbstractAIClient,
        mock_chat: ChatClient,
    ) -> None:
        unauthed_oauth = MagicMock()
        unauthed_oauth.is_authenticated.return_value = False

        app = create_app()
        app.dependency_overrides[get_ai_client] = lambda: mock_ai
        app.dependency_overrides[get_slack_client] = lambda: mock_chat
        app.dependency_overrides[get_oauth_manager] = lambda: unauthed_oauth

        with patch("calendar_client_service.slack_routes.GoogleCalendarClient"):
            tc = TestClient(app, raise_server_exceptions=True)
            tc.post("/slack/events", json=_msg("Hello!", user="U_UNKNOWN"))

        cast("MagicMock", mock_chat).send_message.assert_called_once()
        text: str = cast("MagicMock", mock_chat).send_message.call_args.kwargs.get("text", "")
        assert "authenticate" in text.lower()
        cast("MagicMock", mock_ai).send_message.assert_not_called()
