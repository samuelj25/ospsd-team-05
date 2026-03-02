"""
Google OAuth 2.0 authentication manager.

Handles the full OAuth lifecycle:
- Loading cached credentials from ``token.json``
- Refreshing expired access tokens
- Running the interactive consent flow on first use
- Persisting tokens for subsequent runs
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

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
            resolved_token, SCOPES,
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
