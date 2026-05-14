"""OAuth 2.0 endpoints for the calendar client service."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from google_calendar_client_impl.auth import WebOAuthManager  # noqa: TC002

from calendar_client_service.dependencies import get_oauth_manager
from calendar_client_service.models import AuthStatusResponse
from calendar_client_service.slack_routes import map_slack_user_to_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", summary="Start OAuth 2.0 flow")
def login(
    oauth_manager: Annotated[WebOAuthManager, Depends(get_oauth_manager)],
    slack_user_id: str | None = None,
) -> RedirectResponse:
    """Initiate the OAuth 2.0 authorisation flow and redirect to Google."""
    csrf_token = secrets.token_urlsafe(32)
    state = f"{csrf_token}::{slack_user_id}" if slack_user_id else csrf_token
    auth_url, _state = oauth_manager.get_authorization_url(state=state)
    # Store the CSRF token server-side so the callback can verify it
    oauth_manager.register_state(csrf_token)
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback", summary="Handle OAuth 2.0 callback")
def callback(
    code: str,
    response: Response,  # noqa: ARG001
    oauth_manager: Annotated[WebOAuthManager, Depends(get_oauth_manager)],
    state: str | None = None,
) -> HTMLResponse:
    """
    Exchange the authorization code for tokens and create a session.

    Google redirects the user here after they grant (or deny) access.  This
    endpoint exchanges the ``code`` for access and refresh tokens, stores them
    under a new session key, and sets a ``session_id`` cookie on the response.

    Args:
        code: The authorization code from the Google redirect.
        response: The FastAPI response object (used to set the session cookie).
        oauth_manager: The singleton OAuth manager (injected by FastAPI).
        state: Optional state parameter used to map the session back to a Slack user.

    Returns:
        An :class:`HTMLResponse` containing a success message for the user.

    Raises:
        HTTPException(400): If the code exchange fails (e.g. code already used,
            invalid, or mismatched redirect URI).

    """
    # Verify the CSRF state token BEFORE exchanging the code
    csrf_token = state.split("::", 1)[0] if (state and "::" in state) else state
    if not csrf_token or not oauth_manager.consume_state(csrf_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing OAuth state — possible CSRF attack.",
        )

    try:
        session_id, _ = oauth_manager.handle_callback(code=code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth code exchange failed: {exc}",
        ) from exc

    if state and "::" in state:
        _, slack_user_id = state.split("::", 1)
        map_slack_user_to_session(slack_user_id, session_id)

    html_content = """
    <html>
        <head>
            <title>Authenticated</title>
            <style>
                body {
                    font-family: sans-serif; display: flex; justify-content: center;
                    align-items: center; height: 100vh; background-color: #f0f2f5; margin: 0;
                }
                .container {
                    text-align: center; padding: 40px; background: white;
                    border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                h1 { color: #4CAF50; }
                p { color: #555; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Authentication Successful!</h1>
                <p>You have been authenticated. You can close this page now.</p>
            </div>
        </body>
    </html>
    """
    html_response = HTMLResponse(content=html_content)
    # Set the session_id as an HTTP-only cookie so the browser sends it
    # automatically on all subsequent requests.
    html_response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        # secure=True should be set in production (HTTPS only)
    )
    return html_response


@router.get("/status", summary="Check authentication status")
def auth_status(
    oauth_manager: Annotated[WebOAuthManager, Depends(get_oauth_manager)],
    session_id: Annotated[str | None, Cookie()] = None,
) -> AuthStatusResponse:
    """
    Return whether the current request is authenticated.

    Reads the ``session_id`` cookie and checks whether valid credentials are
    stored for it.

    Args:
        oauth_manager: The singleton OAuth manager (injected by FastAPI).
        session_id: The session cookie value, or ``None`` if not present.

    Returns:
        An :class:`AuthStatusResponse` indicating authentication status.

    """
    if session_id is None or not oauth_manager.is_authenticated(session_id):
        return AuthStatusResponse(authenticated=False)
    return AuthStatusResponse(authenticated=True, session_id=session_id)


@router.post("/logout", summary="End the current session")
def logout(
    response: Response,
    oauth_manager: Annotated[WebOAuthManager, Depends(get_oauth_manager)],
    session_id: Annotated[str | None, Cookie()] = None,
) -> AuthStatusResponse:
    """
    Revoke the current session and clear the session cookie.

    Args:
        response: The FastAPI response object (used to clear the cookie).
        oauth_manager: The singleton OAuth manager (injected by FastAPI).
        session_id: The session cookie value, or ``None`` if not present.

    Returns:
        An :class:`AuthStatusResponse` with ``authenticated=False``.

    """
    if session_id is not None:
        oauth_manager.revoke_session(session_id)
    response.delete_cookie("session_id")
    return AuthStatusResponse(authenticated=False)
