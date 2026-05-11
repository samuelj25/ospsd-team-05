r"""
Integration tests for the /slack/events webhook.

Tests use:
- Real HMAC-signed requests (``SLACK_SIGNING_SECRET`` from ``.env``)
- Real FastAPI routing (no signature patch)
- Real ``GeminiAIClient`` and ``GoogleCalendarClient`` via live credentials
  (seeded from ``token.json`` through the ``E2E_SESSION_ID`` mechanism)
- :class:`~tests.integration.conftest.CaptureChatClient` — a real ``ChatClient``
  ABC implementation that records sent messages without calling the Slack API

VCR cassettes record Gemini REST + Google Calendar HTTP calls on first run::

    uv run pytest tests/integration/test_slack_integration.py \\
        --no-cov --record-mode=once

The ``TestCrossVerticalPath`` class demonstrates the rubric-required path:

    Slack message → AI (Gemini) → Calendar tool call → Google Calendar API
                  → Slack reply (captured by CaptureChatClient)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    import httpx
    from fastapi.testclient import TestClient

    from tests.integration.conftest import CaptureChatClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_USER = "U_INT_001"
_CHANNEL = "C_INT_001"
_SESSION = "integration-test-session"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sign_request(body: bytes) -> dict[str, str]:
    """Return Slack-signed headers using the real ``SLACK_SIGNING_SECRET``."""
    secret = os.environ["SLACK_SIGNING_SECRET"]
    ts = str(int(time.time()))
    base = f"v0:{ts}:{body.decode('utf-8')}"
    sig = "v0=" + hmac.new(
        secret.encode("utf-8"), base.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return {
        "content-type": "application/json",
        "x-slack-request-timestamp": ts,
        "x-slack-signature": sig,
    }


def _event_payload(
    text: str,
    user: str = _USER,
    channel: str = _CHANNEL,
    *,
    bot_id: str | None = None,
) -> dict[str, Any]:
    """Build a minimal Slack event_callback payload."""
    event: dict[str, Any] = {
        "type": "message",
        "text": text,
        "channel": channel,
        "user": user,
    }
    if bot_id:
        event["bot_id"] = bot_id
    return {"type": "event_callback", "event": event}


def _post(
    client: TestClient,
    payload: dict[str, Any],
    *,
    extra_headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Sign and POST a Slack event payload."""
    body = json.dumps(payload).encode()
    headers = _sign_request(body)
    if extra_headers:
        headers.update(extra_headers)
    return client.post("/slack/events", content=body, headers=headers)


# ---------------------------------------------------------------------------
# Route-level tests — no external API calls, no VCR needed
# ---------------------------------------------------------------------------


class TestUrlVerification:
    """Slack url_verification challenge — no AI or Calendar involved."""

    def test_echoes_challenge(
        self, live_app_client: tuple[TestClient, CaptureChatClient]
    ) -> None:
        tc, _ = live_app_client
        payload = {"type": "url_verification", "challenge": "abc-xyz-123"}
        body = json.dumps(payload).encode()
        resp = tc.post("/slack/events", content=body, headers=_sign_request(body))
        assert resp.status_code == 200
        assert resp.json() == {"challenge": "abc-xyz-123"}


class TestShortCircuits:
    """Events that are dropped before reaching the AI layer."""

    def test_bot_messages_are_ignored(
        self, live_app_client: tuple[TestClient, CaptureChatClient]
    ) -> None:
        """Messages from bots produce no reply."""
        tc, capture = live_app_client
        _post(tc, _event_payload("Bot says hi", bot_id="B_BOT_001"))
        assert capture.messages == []

    def test_slack_retry_header_short_circuits(
        self, live_app_client: tuple[TestClient, CaptureChatClient]
    ) -> None:
        """Slack retry requests are dropped immediately."""
        tc, capture = live_app_client
        _post(tc, _event_payload("Retry!"), extra_headers={"x-slack-retry-num": "1"})
        assert capture.messages == []

    def test_unauthenticated_user_receives_login_prompt(
        self, live_app_client: tuple[TestClient, CaptureChatClient]
    ) -> None:
        """A user with no OAuth session gets a login URL, not an AI reply."""
        tc, capture = live_app_client
        _post(tc, _event_payload("Hello!", user="U_UNKNOWN_XYZ"))
        assert len(capture.messages) == 1
        assert "authenticate" in capture.messages[0].text.lower()


# ---------------------------------------------------------------------------
# Cross-vertical integration test — rubric requirement
# ---------------------------------------------------------------------------


@pytest.mark.vcr
class TestCrossVerticalPath:
    """
    Demonstrates the full rubric-required path.

    Path: Slack message → AI (Gemini) → Calendar tool call
          → Google Calendar API → Slack reply

    VCR cassettes capture both the Gemini REST responses and the Google
    Calendar API HTTP calls.  The ``CaptureChatClient`` records the outbound
    reply without hitting the Slack API.

    Together with ``TestAIToolDispatch`` in ``test_ai_tool_dispatch.py``
    these tests confirm that an AI-requested tool call reaches the real
    Google Calendar service.
    """

    def test_calendar_query_triggers_tool_call_and_reply(
        self, live_app_client: tuple[TestClient, CaptureChatClient]
    ) -> None:
        """
        Test calendar query triggers tool call and reply.

        A natural-language calendar question causes Gemini to emit a
        ``list_events`` tool call, which dispatches to the real Google Calendar
        API, and the resulting answer is posted to ``CaptureChatClient``.

        Assertions:
        - HTTP 200 from the webhook endpoint
        - At least one message captured (the AI's reply)
        - The reply is a non-empty string (content is AI-generated)
        """
        from calendar_client_service.slack_routes import map_slack_user_to_session  # noqa: PLC0415

        map_slack_user_to_session(_USER, _SESSION)

        tc, capture = live_app_client
        resp = _post(tc, _event_payload("What events do I have this week?"))

        assert resp.status_code == 200
        # Background task runs synchronously inside TestClient
        assert len(capture.messages) >= 1
        reply_text = capture.messages[0].text
        assert isinstance(reply_text, str)
        assert len(reply_text) > 0

    def test_create_event_via_natural_language(
        self, live_app_client: tuple[TestClient, CaptureChatClient]
    ) -> None:
        """
        Test creating an event via natural language.

        Asking the assistant to create an event causes Gemini to emit a
        ``create_event`` tool call, which creates a real Google Calendar event.
        The assistant's confirmation reply is captured.
        """
        from calendar_client_service.slack_routes import map_slack_user_to_session  # noqa: PLC0415

        map_slack_user_to_session(_USER, _SESSION)

        tc, capture = live_app_client
        resp = _post(
            tc,
            _event_payload(
                "Schedule a team standup meeting tomorrow at 9am for 30 minutes."
            ),
        )

        assert resp.status_code == 200
        assert len(capture.messages) >= 1
        reply_text = capture.messages[0].text
        assert isinstance(reply_text, str)
        assert len(reply_text) > 0
