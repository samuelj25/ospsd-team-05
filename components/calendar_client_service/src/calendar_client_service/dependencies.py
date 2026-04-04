"""FastAPI dependency providers for the calendar client service."""

from __future__ import annotations

import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Cookie, Depends, HTTPException, status
from google_calendar_client_impl.auth import WebOAuthManager
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient

# ---------------------------------------------------------------------------
# Singleton OAuth manager
# ---------------------------------------------------------------------------

# One WebOAuthManager instance is shared for the lifetime of the process.
# It reads GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET / OAUTH_REDIRECT_URI
# from the environment at startup (see README.md for required env vars).
_oauth_manager: WebOAuthManager | None = None


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
        load_dotenv()  # Load variables from .env right before we parse them
        _oauth_manager = WebOAuthManager()  # reads from env vars

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
