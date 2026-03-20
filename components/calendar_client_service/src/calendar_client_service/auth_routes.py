"""OAuth 2.0 endpoints for the calendar client service."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from google_calendar_client_impl.auth import WebOAuthManager  # noqa: TC002

from calendar_client_service.dependencies import get_oauth_manager
from calendar_client_service.models import AuthStatusResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", summary="Start OAuth 2.0 flow")
def login(
    oauth_manager: Annotated[WebOAuthManager, Depends(get_oauth_manager)],
) -> RedirectResponse:
    """
    Redirect the user's browser to the Google OAuth 2.0 consent page.

    After the user grants access, Google will redirect back to ``/auth/callback``
    with an authorization ``code`` query parameter.

    Returns:
        A 302 redirect to the Google authorization URL.

    """
    auth_url, _state = oauth_manager.get_authorization_url()
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback", summary="Handle OAuth 2.0 callback")
def callback(
    code: str,
    response: Response,
    oauth_manager: Annotated[WebOAuthManager, Depends(get_oauth_manager)],
) -> AuthStatusResponse:
    """
    Exchange the authorization code for tokens and create a session.

    Google redirects the user here after they grant (or deny) access.  This
    endpoint exchanges the ``code`` for access and refresh tokens, stores them
    under a new session key, and sets a ``session_id`` cookie on the response.

    Args:
        code: The authorization code from the Google redirect.
        response: The FastAPI response object (used to set the session cookie).
        oauth_manager: The singleton OAuth manager (injected by FastAPI).

    Returns:
        An :class:`AuthStatusResponse` with ``authenticated=True`` and the new
        ``session_id``.

    Raises:
        HTTPException(400): If the code exchange fails (e.g. code already used,
            invalid, or mismatched redirect URI).

    """
    try:
        session_id, _ = oauth_manager.handle_callback(code=code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth code exchange failed: {exc}",
        ) from exc

    # Set the session_id as an HTTP-only cookie so the browser sends it
    # automatically on all subsequent requests.
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        # secure=True should be set in production (HTTPS only)
    )
    return AuthStatusResponse(authenticated=True, session_id=session_id)


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
