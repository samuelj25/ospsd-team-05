"""Integration tests for the AI tool dispatcher (dispatch_tool_call)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

import pytest
from calendar_client_service.ai_tools import dispatch_tool_call
from ospsd_calendar_api.models import Event

if TYPE_CHECKING:
    from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient


def _make_event(
    event_id: str = "evt-1",
    title: str = "Test Event",
    start: datetime | None = None,
    end: datetime | None = None,
    description: str = "",
) -> Event:
    """Return a fake :class:`Event` for use as a mock return value."""
    now = datetime.now(tz=UTC)
    return Event(
        id=event_id,
        title=title,
        start_time=start or now,
        end_time=end or (now + timedelta(hours=1)),
        description=description,
    )


@pytest.fixture
def mock_client() -> GoogleCalendarClient:
    """MagicMock satisfying the GoogleCalendarClient interface."""
    return cast("GoogleCalendarClient", MagicMock())


# ---------------------------------------------------------------------------
# list_events
# ---------------------------------------------------------------------------


class TestListEvents:
    """dispatch_tool_call('list_events', ...) scenarios."""

    def test_returns_serialised_event_list(self, mock_client: GoogleCalendarClient) -> None:
        now = datetime.now(tz=UTC).replace(microsecond=0)
        end = now + timedelta(hours=2)
        cast("MagicMock", mock_client).list_events.return_value = [_make_event(start=now, end=end)]

        result = dispatch_tool_call(
            "list_events",
            {"start": now.isoformat(), "end": end.isoformat()},
            mock_client,
        )

        assert not result.is_error
        payload = json.loads(result.content)
        assert len(payload) == 1
        assert payload[0]["id"] == "evt-1"
        cast("MagicMock", mock_client).list_events.assert_called_once()

    def test_empty_calendar_returns_empty_list(self, mock_client: GoogleCalendarClient) -> None:
        now = datetime.now(tz=UTC)
        cast("MagicMock", mock_client).list_events.return_value = []

        result = dispatch_tool_call(
            "list_events",
            {"start": now.isoformat(), "end": (now + timedelta(hours=1)).isoformat()},
            mock_client,
        )

        assert not result.is_error
        assert json.loads(result.content) == []


# ---------------------------------------------------------------------------
# create_event
# ---------------------------------------------------------------------------


class TestCreateEvent:
    """dispatch_tool_call('create_event', ...) scenarios."""

    def test_returns_serialised_new_event(self, mock_client: GoogleCalendarClient) -> None:
        now = datetime.now(tz=UTC).replace(microsecond=0)
        end = now + timedelta(hours=1)
        cast("MagicMock", mock_client).create_event.return_value = _make_event(
            event_id="new-1", title="Standup", start=now, end=end
        )

        result = dispatch_tool_call(
            "create_event",
            {"title": "Standup", "start": now.isoformat(), "end": end.isoformat()},
            mock_client,
        )

        assert not result.is_error
        payload = json.loads(result.content)
        assert payload["id"] == "new-1"
        assert payload["title"] == "Standup"

    def test_description_defaults_to_empty_string(self, mock_client: GoogleCalendarClient) -> None:
        now = datetime.now(tz=UTC).replace(microsecond=0)
        end = now + timedelta(hours=1)
        cast("MagicMock", mock_client).create_event.return_value = _make_event(start=now, end=end)

        dispatch_tool_call(
            "create_event",
            {"title": "No desc", "start": now.isoformat(), "end": end.isoformat()},
            mock_client,
        )

        cast("MagicMock", mock_client).create_event.assert_called_once_with(
            title="No desc", start=now, end=end, description=""
        )


# ---------------------------------------------------------------------------
# get_event
# ---------------------------------------------------------------------------


class TestGetEvent:
    """dispatch_tool_call('get_event', ...) scenarios."""

    def test_returns_serialised_event(self, mock_client: GoogleCalendarClient) -> None:
        cast("MagicMock", mock_client).get_event.return_value = _make_event(
            event_id="evt-42", title="Review"
        )

        result = dispatch_tool_call("get_event", {"event_id": "evt-42"}, mock_client)

        assert not result.is_error
        payload = json.loads(result.content)
        assert payload["id"] == "evt-42"
        cast("MagicMock", mock_client).get_event.assert_called_once_with("evt-42")


# ---------------------------------------------------------------------------
# delete_event
# ---------------------------------------------------------------------------


class TestDeleteEvent:
    """dispatch_tool_call('delete_event', ...) scenarios."""

    def test_returns_success_message(self, mock_client: GoogleCalendarClient) -> None:
        result = dispatch_tool_call("delete_event", {"event_id": "evt-9"}, mock_client)

        assert not result.is_error
        assert "deleted" in result.content.lower()
        cast("MagicMock", mock_client).delete_event.assert_called_once_with("evt-9")


# ---------------------------------------------------------------------------
# Unknown tool / error handling
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Unknown tools and client exceptions."""

    def test_unknown_tool_returns_error(self, mock_client: GoogleCalendarClient) -> None:
        result = dispatch_tool_call("make_coffee", {}, mock_client)

        assert result.is_error
        assert "unknown" in result.content.lower()

    def test_client_exception_is_caught_and_returned(
        self, mock_client: GoogleCalendarClient
    ) -> None:
        cast("MagicMock", mock_client).get_event.side_effect = RuntimeError("API down")

        result = dispatch_tool_call("get_event", {"event_id": "x"}, mock_client)

        assert result.is_error
        assert "API down" in result.content
