"""Slack Event API webhook — receives messages and dispatches AI+calendar actions."""

from __future__ import annotations

import datetime
import hashlib
import hmac
import logging
import os
import time
from typing import Annotated, Any

from ai_client_api.client import AbstractAIClient  # noqa: TC002
from chat_client_api.client import ChatClient  # noqa: TC002
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from google_calendar_client_impl.auth import WebOAuthManager  # noqa: TC002
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient

from calendar_client_service.ai_tools import CALENDAR_TOOLS, dispatch_tool_call
from calendar_client_service.dependencies import (
    get_ai_client,
    get_oauth_manager,
    get_slack_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack", tags=["slack"])

_SLACK_TIMESTAMP_TOLERANCE_S = 300  # 5 minutes — Slack's replay-attack window

# In-memory context store mapping channel_id -> list of prior messages
_conversation_history: dict[str, list[dict[str, Any]]] = {}

# In-memory mapping of Slack user ID -> OAuth session ID
_slack_user_sessions: dict[str, str] = {}


def map_slack_user_to_session(user_id: str, session_id: str) -> None:
    """Map a Slack user ID to an OAuth session ID."""
    _slack_user_sessions[user_id] = session_id


def _verify_slack_signature(request_body: bytes, headers: dict[str, str]) -> bool:
    """
    Return True if the request body matches the Slack signing secret.

    Args:
        request_body: Raw bytes of the incoming request body.
        headers: Request headers dict (lowercase keys).

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.

    """
    secret = os.environ.get("SLACK_SIGNING_SECRET", "")
    if not secret:
        logger.warning("SLACK_SIGNING_SECRET not set — skipping signature verification.")
        return True

    ts = headers.get("x-slack-request-timestamp", "")
    sig = headers.get("x-slack-signature", "")

    # Reject stale requests
    try:
        if abs(time.time() - float(ts)) > _SLACK_TIMESTAMP_TOLERANCE_S:
            return False
    except ValueError:
        return False

    base = f"v0:{ts}:{request_body.decode('utf-8')}"
    expected = "v0=" + hmac.new(
        secret.encode("utf-8"), base.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig)


async def _handle_message_event(
    event: dict[str, Any],
    oauth_manager: WebOAuthManager,
    ai_client: AbstractAIClient,
    chat_client: ChatClient,
    base_url: str,
) -> None:
    """
    Process a Slack message event in the background.

    Sends the user's text to Gemini with calendar tool definitions, executes
    any tool calls, and posts the AI's final reply back to Slack.

    Args:
        event: The Slack ``event`` payload dict.
        oauth_manager: Authenticated OAuth manager.
        ai_client: Gemini AI client instance.
        chat_client: Slack chat client for sending replies.
        base_url: Base URL of the API.

    """
    text: str = event.get("text", "").strip()
    channel_id: str = event.get("channel", "")

    if not text or not channel_id:
        return

    # Ignore messages from bots (including our own replies) to avoid loops
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return

    user_id = event.get("user")
    if not user_id:
        return

    logger.info("Processing Slack message in channel %s: %r", channel_id, text)

    # Check authentication
    session_id = _slack_user_sessions.get(user_id)
    if not session_id or not oauth_manager.is_authenticated(session_id):
        # Allow fallback to E2E session for tests
        session_id = os.environ.get("E2E_SESSION_ID")
        if not session_id or not oauth_manager.is_authenticated(session_id):
            login_url = f"{base_url}/auth/login?slack_user_id={user_id}"
            chat_client.send_message(
                channel_id=channel_id,
                text=f"Please authenticate your Google Calendar account first: {login_url}",
            )
            return

    creds = oauth_manager.get_credentials(session_id)
    if not creds:
        chat_client.send_message(
            channel_id=channel_id,
            text="Session credentials not found. Please re-authenticate.",
        )
        return

    calendar_client = GoogleCalendarClient()
    calendar_client.connect_with_credentials(creds)

    try:
        def dispatcher(
            tool_name: str, args: dict[str, Any]
        ) -> Any:  # noqa: ANN401
            return dispatch_tool_call(tool_name, args, calendar_client)

        current_time = datetime.datetime.now(datetime.UTC).strftime("%A, %B %d, %Y")
        enhanced_prompt = (
            f"System context: The current date is {current_time}. "
            f"CRITICAL INSTRUCTION: Be extremely concise. NEVER repeat yourself. "
            f"User message: {text}"
        )

        channel_history = _conversation_history.get(channel_id, [])

        reply = ai_client.send_message(
            prompt=enhanced_prompt,
            tools=CALENDAR_TOOLS,
            tool_dispatcher=dispatcher,
            context=channel_history,
        )

        # Store the raw text and reply in history (limit to last 10 turns to save tokens)
        channel_history.append({"role": "user", "content": text})
        channel_history.append({"role": "model", "content": reply})
        _conversation_history[channel_id] = channel_history[-10:]

        chat_client.send_message(channel_id=channel_id, text=reply)
    except Exception:
        logger.exception("Failed to process Slack message")
        chat_client.send_message(
            channel_id=channel_id,
            text="Sorry, I encountered an error processing your request.",
        )


@router.post("/events", summary="Slack Event API webhook")
async def slack_events(
    request: Request,
    background_tasks: BackgroundTasks,
    oauth_manager: Annotated[WebOAuthManager, Depends(get_oauth_manager)],
    ai_client: Annotated[AbstractAIClient, Depends(get_ai_client)],
    chat_client: Annotated[ChatClient, Depends(get_slack_client)],
) -> dict[str, str]:
    """
    Handle incoming Slack Events API payloads.

    Supports:
    - ``url_verification`` challenges (one-time setup).
    - ``message`` events: dispatches AI + calendar tool loop in the background
      and posts the reply to Slack.

    Returns HTTP 200 immediately to satisfy Slack's 3-second timeout.

    Args:
        request: The incoming FastAPI request.
        background_tasks: FastAPI background task queue.
        oauth_manager: The OAuth manager for credential lookup.
        ai_client: GeminiAIClient (injected).
        chat_client: SlackChatAdapter (injected).

    Returns:
        Empty dict ``{}`` for message events, or ``{"challenge": "..."}`` for
        url_verification.

    Raises:
        HTTPException(403): If the Slack request signature is invalid.

    """
    body_bytes = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    if not _verify_slack_signature(body_bytes, headers):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Slack signature.",
        )

    payload: dict[str, Any] = await request.json()

    # Slack url_verification challenge (one-time during app setup)
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge", "")}

    # Ignore Slack retries for older messages that previously failed
    if "x-slack-retry-num" in headers:
        return {}

    event: dict[str, Any] = payload.get("event", {})
    event_type: str = event.get("type", "")

    if event_type in ("message", "app_mention"):
        background_tasks.add_task(
            _handle_message_event,
            event,
            oauth_manager,
            ai_client,
            chat_client,
            str(request.base_url).rstrip("/"),
        )

    return {}
