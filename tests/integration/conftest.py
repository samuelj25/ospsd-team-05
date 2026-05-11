"""
Pytest config for integration tests.

Provides:
- ``integration_live_client``: a real ``GoogleCalendarClient`` connected via ``token.json``.
- ``CaptureChatClient``: a real ``ChatClient`` ABC impl that stores sent messages in memory
  instead of calling the Slack API.  Used to assert on outbound replies without polluting
  a real Slack workspace.
- ``capture_chat``: fixture that yields a fresh ``CaptureChatClient`` per test.
- ``live_app_client``: FastAPI ``TestClient`` wired to real Gemini + Calendar + OAuth
  credentials, with ``CaptureChatClient`` injected as the Slack adapter.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from chat_client_api.client import (
    Channel,
    ChannelNotFoundError,
    ChatClient,
    Message,
    MessageDeleteError,
    MessageNotFoundError,
)
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient

if TYPE_CHECKING:
    from collections.abc import Generator


# ---------------------------------------------------------------------------
# VCR configuration — strip credentials before cassettes are written to disk
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, object]:
    """
    Configure vcrpy to redact sensitive headers from cassette YAML files.

    ``authorization`` contains the live OAuth Bearer token.
    ``x-goog-api-client`` contains SDK version metadata (not a secret, but
    version-specific and not needed for replay).

    Both are replaced with the literal string ``FILTERED`` in the cassette.
    vcrpy ignores request headers that are marked as filtered when matching
    recorded interactions during replay.

    ``oauth2.googleapis.com`` is added to ``ignore_hosts`` so that OAuth token
    refresh calls are never intercepted by VCR.  These are auth-layer calls
    (not business logic) and must be allowed through to the live endpoint when
    the access token has expired — both locally and in CI.
    """
    return {
        "filter_headers": ["authorization", "x-goog-api-client"],
        "ignore_hosts": ["oauth2.googleapis.com"],
    }


# ---------------------------------------------------------------------------
# CaptureChatClient — real ChatClient ABC, no Slack API calls
# ---------------------------------------------------------------------------


class CaptureChatClient(ChatClient):  # type: ignore[misc]
    """
    Real implementation of ChatClient that stores outbound messages in memory.

    This is **not** a mock — it satisfies the full ABC contract.  Tests use it
    to assert that the correct reply was sent without posting to a live Slack
    workspace.
    """

    def __init__(self) -> None:
        """Initialize the capture client with an empty message list."""
        self.messages: list[Message] = []

    def send_message(self, channel_id: str, text: str) -> Message:
        msg = Message(
            message_id=f"{channel_id}:capture-{len(self.messages)}",
            channel=channel_id,
            text=text,
            sender="bot",
            timestamp=datetime.now(UTC),
        )
        self.messages.append(msg)
        return msg

    def get_channels(self) -> list[Channel]:
        return []

    def get_channel(self, channel_id: str) -> Channel:
        raise ChannelNotFoundError(channel_id)

    def get_messages(
        self,
        channel_id: str,
        limit: int = 10,
        cursor: str | None = None,
    ) -> list[Message]:
        del limit, cursor  # unused but required by ABC
        return [m for m in self.messages if m.channel == channel_id]

    def get_message(self, message_id: str) -> Message:
        raise MessageNotFoundError(message_id)

    def delete_message(self, message_id: str) -> None:
        raise MessageDeleteError(message_id)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def integration_live_client() -> GoogleCalendarClient:
    """
    Create a real connected GoogleCalendarClient using live APIs.

    Uses ``function`` scope (not ``session``) so that each test gets its own
    client instance.  This prevents the ``connect()`` authentication HTTP call
    from being recorded inside the first VCR cassette and then failing to
    replay in subsequent tests or bleeding into non-VCR tests such as those
    in ``test_client_integration.py``.

    Fails fast if ``token.json`` / ``credentials.json`` are absent.
    In CI these files are decoded from ``GCP_TOKEN_JSON_BASE64`` /
    ``GCP_CREDENTIALS_JSON_BASE64`` by the ``setup_gcp_credentials`` command.
    """
    token_path = os.environ.get("GOOGLE_OAUTH_TOKEN_PATH", "token.json")
    creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_PATH", "credentials.json")

    if not Path(token_path).exists() and not Path(creds_path).exists():
        pytest.fail("Integration tests failed: No token.json or credentials.json found.")

    client = GoogleCalendarClient()
    client.connect()
    return client


@pytest.fixture
def capture_chat() -> CaptureChatClient:
    """Return a fresh :class:`CaptureChatClient` for each test."""
    return CaptureChatClient()


@pytest.fixture
def live_app_client(
    capture_chat: CaptureChatClient,
) -> Generator[tuple[Any, CaptureChatClient], None, None]:
    """
    FastAPI ``TestClient`` wired to real credentials.

    Substitutes ``CaptureChatClient`` for the Slack adapter.
    Resets the dependency singletons before each test so credential state
    does not leak between tests.
    """
    import calendar_client_service.dependencies as _deps  # noqa: PLC0415

    # Reset singletons so each test gets a fresh provider instance.
    _deps._oauth_manager = None  # noqa: SLF001
    _deps._ai_client = None  # noqa: SLF001
    _deps._slack_client = None  # noqa: SLF001

    # Ensure the OAuth manager seeds from token.json via E2E_SESSION_ID.
    os.environ.setdefault("E2E_SESSION_ID", "integration-test-session")

    from calendar_client_service.app import create_app  # noqa: PLC0415
    from calendar_client_service.dependencies import get_slack_client  # noqa: PLC0415
    from fastapi.testclient import TestClient  # noqa: PLC0415

    app = create_app()
    app.dependency_overrides[get_slack_client] = lambda: capture_chat

    yield TestClient(app, raise_server_exceptions=False), capture_chat

    app.dependency_overrides.clear()
    # Reset singletons after test too.
    _deps._oauth_manager = None  # noqa: SLF001
    _deps._ai_client = None  # noqa: SLF001
    _deps._slack_client = None  # noqa: SLF001
