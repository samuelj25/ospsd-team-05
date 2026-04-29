"""Pytest config for integration tests."""

import os
from pathlib import Path

import pytest
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient


@pytest.fixture(scope="session")
def integration_live_client() -> GoogleCalendarClient:
    """
    Create a real connected GoogleCalendarClient using live APIs.

    If no credentials or tokens are present locally, skips the tests gracefully.
    """
    token_path = os.environ.get("GOOGLE_OAUTH_TOKEN_PATH", "token.json")
    creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_PATH", "credentials.json")

    if not Path(token_path).exists() and not Path(creds_path).exists():
        pytest.fail("Integration tests failed: No token.json or credentials.json found.")

    client = GoogleCalendarClient()
    client.connect()

    return client
