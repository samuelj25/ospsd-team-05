"""FastAPI dependency providers for the calendar client service."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Annotated

from dotenv import load_dotenv
from fastapi import Cookie, Depends, HTTPException, status
from gemini_ai_client_impl.client import GeminiAIClient
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import firestore as firestore_lib
from google_calendar_client_impl.auth import WebOAuthManager
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient
from slack_chat_adapter.adapter import SlackChatAdapter

if TYPE_CHECKING:
    from ai_client_api.client import AbstractAIClient
    from chat_client_api.client import ChatClient

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton OAuth manager
# ---------------------------------------------------------------------------

# One WebOAuthManager instance is shared for the lifetime of the process.
# It reads GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET / OAUTH_REDIRECT_URI
# from the environment at startup (see README.md for required env vars).
_oauth_manager: WebOAuthManager | None = None
_firestore_unavailable: bool = False
_firestore_client: firestore_lib.Client | None = None

def get_firestore() -> firestore_lib.Client | None:
    """Get the singleton firestore client."""
    global _firestore_client, _firestore_unavailable  # noqa: PLW0603
    if _firestore_client is not None:
        return _firestore_client
    if _firestore_unavailable:
        return None
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        logger.info("Firestore: GOOGLE_CLOUD_PROJECT not set — using in-memory fallback.")
        _firestore_unavailable = True
        return None
    try:
        _firestore_client = firestore_lib.Client(project=project)
        _firestore_client.collection("_health").document("ping").get()
        logger.info("Firestore: client initialised (project=%s).", project)
    except DefaultCredentialsError:
        logger.warning("Firestore: no credentials found — falling back to in-memory store.")
        _firestore_client = None
        _firestore_unavailable = True
    except Exception:  # noqa: BLE001
        logger.warning("Firestore: failed to connect — falling back to in-memory store.", exc_info=True)  # noqa: E501
        _firestore_client = None
        _firestore_unavailable = True
    return _firestore_client

def get_oauth_manager() -> WebOAuthManager:
    """
    Return the singleton WebOAuthManager, constructing it on first call.

    If the ``E2E_SESSION_ID`` environment variable is set the manager is also
    seeded with credentials from the local ``token.json`` under that session
    ID.  This lets E2E tests bypass the interactive OAuth redirect flow by
    spawning the server with a known ``E2E_SESSION_ID`` and constructing the
    adapter client with the same value.

    Raises:
        RuntimeError: If required OAuth env vars are not set.

    """
    global _oauth_manager  # noqa: PLW0603
    if _oauth_manager is None:
        load_dotenv()
        _oauth_manager = WebOAuthManager(firestore_client=get_firestore())

        e2e_session_id = os.environ.get("E2E_SESSION_ID")
        if e2e_session_id:
            _oauth_manager.seed_session_from_token_file(e2e_session_id)
    return _oauth_manager


# ---------------------------------------------------------------------------
# Per-request calendar client (requires authenticated session)
# ---------------------------------------------------------------------------


def get_calendar_client(
    oauth_manager: Annotated[WebOAuthManager, Depends(get_oauth_manager)],
    session_id: Annotated[str | None, Cookie()] = None,
) -> GoogleCalendarClient:
    """
    Return a connected GoogleCalendarClient for the current request's session.

    Reads the ``session_id`` cookie set by ``/auth/callback``, retrieves the
    stored credentials from the ``WebOAuthManager``, and builds a
    ``GoogleCalendarClient`` connected with those credentials.

    Args:
        oauth_manager: The singleton OAuth manager (injected by FastAPI).
        session_id: The session cookie value, or ``None`` if not present.

    Raises:
        HTTPException(401): If no session cookie is present or the session has
            expired / is unknown.

    """
    # Fallback to the pre-seeded service account session for background workers/webhooks
    if session_id is None:
        session_id = os.environ.get("E2E_SESSION_ID")

    if session_id is None or not oauth_manager.is_authenticated(session_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Visit /auth/login to start the OAuth flow.",
        )

    creds = oauth_manager.get_credentials(session_id)
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session credentials not found. Please re-authenticate.",
        )

    client = GoogleCalendarClient()
    client.connect_with_credentials(creds)
    return client


# ---------------------------------------------------------------------------
# AI client (singleton, env-var driven)
# ---------------------------------------------------------------------------

_ai_client: AbstractAIClient | None = None


def get_ai_client() -> AbstractAIClient:
    """
    Return the singleton GeminiAIClient, constructing it on first call.

    Reads ``GEMINI_API_KEY`` from the environment.

    Raises:
        RuntimeError: If ``GEMINI_API_KEY`` is not set.

    """
    global _ai_client  # noqa: PLW0603
    if _ai_client is None:
        load_dotenv()
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        _ai_client = GeminiAIClient(model_name=model_name)
    return _ai_client


# ---------------------------------------------------------------------------
# Chat client (singleton, env-var driven, backend-agnostic)
# ---------------------------------------------------------------------------

_slack_client: ChatClient | None = None


def get_chat_client() -> ChatClient:
    """
    Return the singleton chat backend client, constructing it on first call.

    The backend is selected by the ``CHAT_BACKEND`` environment variable
    (default: ``"slack"``).  This makes the chat layer swappable without
    touching any route code — only this factory changes when a new backend
    (e.g. Discord) is added.

    Currently supported backends:
    - ``"slack"``: :class:`~slack_chat_adapter.adapter.SlackChatAdapter`
      (reads ``SLACK_BOT_TOKEN`` from the environment).

    Raises:
        RuntimeError: If ``SLACK_BOT_TOKEN`` is not set (for the ``slack``
            backend) or an unknown backend is requested.

    """
    global _slack_client  # noqa: PLW0603
    if _slack_client is None:
        load_dotenv()
        backend = os.environ.get("CHAT_BACKEND", "slack")
        if backend == "slack":
            _slack_client = SlackChatAdapter()
        else:
            msg = f"Unknown CHAT_BACKEND: {backend!r}"
            raise RuntimeError(msg)
    return _slack_client
