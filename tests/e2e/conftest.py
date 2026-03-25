"""Pytest config for E2E tests."""

import os
from pathlib import Path

import pytest
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient


@pytest.fixture(scope="session")
def live_client() -> GoogleCalendarClient:
    """
    Create a real connected GoogleCalendarClient using live APIs for E2E testing.

    If no credentials or tokens are present locally, it will purposefully fail the test.
    """
    token_path = os.environ.get("GOOGLE_OAUTH_TOKEN_PATH", "token.json")
    creds_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_PATH", "credentials.json")

    if not Path(token_path).exists() and not Path(creds_path).exists():
        pytest.fail("E2E tests failed: No token.json or credentials.json found.")

    client = GoogleCalendarClient()
    client.connect()

    return client
