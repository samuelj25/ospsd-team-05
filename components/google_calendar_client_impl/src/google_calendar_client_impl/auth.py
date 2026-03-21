"""
Google OAuth 2.0 authentication manager.

Provides two distinct authentication strategies:

1. **Local / CLI flow** (``get_credentials``): Uses ``InstalledAppFlow`` to
   run an interactive browser-based consent flow and persist a ``token.json``
   to disk. This is the HW1 workaround and remains fully usable for local dev.

2. **Web server flow** (``WebOAuthManager``): Implements the OAuth 2.0
   Authorization Code Flow for deployed web services. Redirects the user to
   the provider's consent page, handles the callback, and stores per-session
   credentials in memory. This is the correct approach for HW2's FastAPI
   service where multiple users authenticate with their own accounts.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Final

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow

#: OAuth scopes required by the Google Calendar + Tasks integration.
SCOPES: Final[list[str]] = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]

#: Default path to the OAuth client-secrets file downloaded from GCP.
_DEFAULT_CREDENTIALS_PATH: Final[str] = "credentials.json"

#: Default path where the user's access / refresh token is cached.
_DEFAULT_TOKEN_PATH: Final[str] = "token.json"  # noqa: S105


def get_credentials(
    credentials_path: str | None = None,
    token_path: str | None = None,
) -> Credentials:
    """
    Obtain valid Google OAuth 2.0 credentials.

    Acts as the primary authentication boundary for the Google API.
    The resolution order is:

    1. If *token_path* exists, load cached credentials via
       ``Credentials.from_authorized_user_file``.
    2. If the loaded token is expired **and** a refresh token is available,
       silently refresh it via ``creds.refresh(Request())`` without user
       intervention.
    3. If no cached token exists (first run), read client secrets from
       *credentials_path* and launch the browser-based OAuth consent flow
       via ``InstalledAppFlow``.
    4. Persist the resulting credentials back to *token_path* as JSON,
       ensuring subsequent runs are fully headless.

    Args:
        credentials_path: Path to the ``credentials.json`` client-secrets
            file.  Falls back to the ``GOOGLE_OAUTH_CREDENTIALS_PATH``
            environment variable, then to ``"credentials.json"``.
        token_path: Path to the cached ``token.json`` file.  Falls back to
            the ``GOOGLE_OAUTH_TOKEN_PATH`` environment variable, then to
            ``"token.json"``.

    Returns:
        A valid ``google.oauth2.credentials.Credentials`` instance ready
        for use with ``googleapiclient.discovery.build``.

    Raises:
        FileNotFoundError: If *credentials_path* does not exist when a new
            OAuth flow is required.

    """
    resolved_credentials = credentials_path or os.environ.get(
        "GOOGLE_OAUTH_CREDENTIALS_PATH",
        _DEFAULT_CREDENTIALS_PATH,
    )
    resolved_token = token_path or os.environ.get(
        "GOOGLE_OAUTH_TOKEN_PATH",
        _DEFAULT_TOKEN_PATH,
    )

    creds: Credentials | None = None

    # ---- 1. Try to load an existing token --------------------------------
    if Path(resolved_token).exists():
        creds = Credentials.from_authorized_user_file(  # type: ignore[no-untyped-call]
            resolved_token,
            SCOPES,
        )

    # ---- 2 / 3. Refresh or run the consent flow -------------------------
    if creds is None or not creds.valid:
        if creds is not None and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(resolved_credentials).exists():
                msg = (
                    f"OAuth client-secrets file not found at "
                    f"'{resolved_credentials}'. Download it from the Google "
                    f"Cloud Console (APIs & Services → Credentials)."
                )
                raise FileNotFoundError(msg)

            flow = InstalledAppFlow.from_client_secrets_file(
                resolved_credentials,
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        # ---- 4. Persist the token ----------------------------------------
        Path(resolved_token).write_text(creds.to_json())

    return creds


# ---------------------------------------------------------------------------
# Web server OAuth 2.0 flow
# ---------------------------------------------------------------------------


class WebOAuthManager:
    """
    Manage OAuth 2.0 Authorization Code Flow for web server applications.

    Unlike ``get_credentials`` (which spins up a local browser window via
    ``InstalledAppFlow``), this class implements the standard redirect-based
    flow required by deployed services:

    1. Call :meth:`get_authorization_url` to obtain a URL that the user's
       browser should be redirected to.
    2. After the user grants consent, the provider calls back to your
       ``/auth/callback`` endpoint with a ``code`` query parameter.
    3. Pass that code to :meth:`handle_callback`, which exchanges it for
       access + refresh tokens and stores them under a session key.
    4. Retrieve stored credentials later via :meth:`get_credentials`.

    Credentials are held in-process memory. For production a persistent store
    (e.g. Redis, a database) should replace ``_sessions``, but for this
    assignment in-memory is sufficient per the HW2 FAQ.

    Configuration is driven by environment variables so that the same code
    works in local development and on the deployed platform:

    * ``GOOGLE_OAUTH_CLIENT_ID`` — OAuth client ID.
    * ``GOOGLE_OAUTH_CLIENT_SECRET`` — OAuth client secret.
    * ``OAUTH_REDIRECT_URI`` — Callback URL registered in GCP Console.
      Use ``http://localhost:8000/auth/callback`` locally and your
      platform URL in production.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
    ) -> None:
        """
        Initialise the manager.

        Args:
            client_id: OAuth client ID. Falls back to ``GOOGLE_OAUTH_CLIENT_ID``.
            client_secret: OAuth client secret. Falls back to
                ``GOOGLE_OAUTH_CLIENT_SECRET``.
            redirect_uri: Redirect URI registered in the OAuth application.
                Falls back to ``OAUTH_REDIRECT_URI``.

        Raises:
            ValueError: If any of the three required values cannot be resolved.

        """
        self.client_id: str = client_id or os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
        self.client_secret: str = client_secret or os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
        self.redirect_uri: str = redirect_uri or os.environ.get(
            "OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"
        )

        if not self.client_id:
            msg = (
                "OAuth client ID is not set. "
                "Pass client_id or set the GOOGLE_OAUTH_CLIENT_ID environment variable."
            )
            raise ValueError(msg)
        if not self.client_secret:
            msg = (
                "OAuth client secret is not set. "
                "Pass client_secret or set the GOOGLE_OAUTH_CLIENT_SECRET environment variable."
            )
            raise ValueError(msg)

        # In-memory session store: session_id -> Credentials
        self._sessions: dict[str, Credentials] = {}

    def _build_flow(self) -> Flow:
        """Construct a ``Flow`` instance from the stored client credentials."""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri],
            },
        }
        return Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )

    def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """
        Build the Google OAuth 2.0 consent URL.

        Args:
            state: An optional opaque value that will be round-tripped through
                the redirect. If *None*, a cryptographically random token is
                generated automatically.

        Returns:
            A ``(authorization_url, state)`` tuple.  Redirect the user's
            browser to ``authorization_url``.  Store ``state`` server-side
            so the callback can verify it to prevent CSRF.

        """
        if state is None:
            state = secrets.token_urlsafe(32)
        flow = self._build_flow()
        auth_url, returned_state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",  # force refresh token on every consent
        )
        return auth_url, returned_state

    def handle_callback(self, code: str) -> tuple[str, Credentials]:
        """
        Exchange an authorization code for credentials and start a session.

        This should be called from the ``/auth/callback`` endpoint after
        Google redirects the user back with a ``code`` query parameter.

        Args:
            code: The authorization code received from the provider.

        Returns:
            A ``(session_id, credentials)`` tuple.  The ``session_id`` should
            be stored in a cookie or returned to the client so subsequent
            requests can be authenticated via :meth:`get_credentials`.

        """
        flow = self._build_flow()
        flow.fetch_token(code=code)
        creds: Credentials = flow.credentials
        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = creds
        return session_id, creds

    def get_credentials(self, session_id: str) -> Credentials | None:
        """
        Retrieve stored credentials for an active session.

        Args:
            session_id: The value returned by :meth:`handle_callback`.

        Returns:
            The ``Credentials`` object for the session, or *None* if the
            session does not exist.

        """
        return self._sessions.get(session_id)

    def revoke_session(self, session_id: str) -> None:
        """
        Remove a session's credentials from the in-memory store.

        Args:
            session_id: The session to revoke.

        """
        self._sessions.pop(session_id, None)

    def is_authenticated(self, session_id: str) -> bool:
        """
        Check whether a session has valid stored credentials.

        Args:
            session_id: The session to check.

        Returns:
            ``True`` if credentials exist for the session, ``False`` otherwise.

        """
        return session_id in self._sessions
