"""Tests for the Google Calendar client implementation."""

import os
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from google_calendar_client_impl import GoogleCalendarClient


def test_google_client_connect_mocks() -> None:
    """Test that connect() uses environment variables without real network calls."""
    with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "temp"}):
        client = GoogleCalendarClient()
        # Should not raise
        client.connect()


def test_google_client_connect_warns_when_missing_env(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that connect() prints a warning when credentials env var is missing."""
    with patch.dict(os.environ, {}, clear=True):
        client = GoogleCalendarClient()
        client.connect()
        out = capsys.readouterr().out
        # keep this flexible for scaffold wording
        assert "GOOGLE_APPLICATION_CREDENTIALS" in out



def test_google_client_get_events_scaffold_returns_iterator() -> None:
    """Test get_events returns an iterator in scaffold."""
    client = GoogleCalendarClient()

    start = datetime(2026, 2, 16, 9, 0, tzinfo=UTC)
    end = datetime(2026, 2, 16, 10, 0, tzinfo=UTC)

    events_iter = client.get_events(start_time=start, end_time=end)

    assert hasattr(events_iter, "__iter__")
    assert list(events_iter) == []
