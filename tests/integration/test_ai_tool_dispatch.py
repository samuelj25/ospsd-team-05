"""
Integration tests for the AI tool dispatcher.

Uses the real ``GoogleCalendarClient`` connected to live Google Calendar APIs.
HTTP interactions are recorded as VCR cassettes on the first run
(``--record-mode=new_episodes``) and replayed on subsequent runs so CI does
not require live credentials after the cassettes are committed.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from calendar_client_service.ai_tools import dispatch_tool_call

if TYPE_CHECKING:
    from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient

# ---------------------------------------------------------------------------
# Shared time anchors (used as cassette-stable values)
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 5, 12, 10, 0, 0, tzinfo=UTC)   # fixed → stable cassettes
_END = _NOW + timedelta(hours=1)
_WINDOW_END = _NOW + timedelta(hours=3)


# ---------------------------------------------------------------------------
# Tests — each class is @pytest.mark.vcr so cassettes are auto-managed
# ---------------------------------------------------------------------------


@pytest.mark.vcr
class TestListEvents:
    """dispatch_tool_call('list_events') against live Google Calendar."""

    def test_returns_serialised_event_list(
        self, integration_live_client: GoogleCalendarClient
    ) -> None:
        """Create a real event, list it via the dispatcher, assert it appears."""
        created = integration_live_client.create_event(
            title="[VCR] List Test Event", start=_NOW, end=_END
        )
        try:
            result = dispatch_tool_call(
                "list_events",
                {"start": _NOW.isoformat(), "end": _WINDOW_END.isoformat()},
                integration_live_client,
            )
            assert not result.is_error
            payload = json.loads(result.content)
            assert isinstance(payload, list)
            assert any(e["id"] == created.id for e in payload)
        finally:
            integration_live_client.delete_event(created.id)

    def test_far_future_range_returns_empty_list(
        self, integration_live_client: GoogleCalendarClient
    ) -> None:
        """Querying a range 10 years out returns an empty list, not an error."""
        far_start = datetime(2036, 1, 1, tzinfo=UTC)
        far_end = datetime(2036, 1, 2, tzinfo=UTC)
        result = dispatch_tool_call(
            "list_events",
            {"start": far_start.isoformat(), "end": far_end.isoformat()},
            integration_live_client,
        )
        assert not result.is_error
        assert json.loads(result.content) == []


@pytest.mark.vcr
class TestCreateEvent:
    """dispatch_tool_call('create_event') against live Google Calendar."""

    def test_returns_id_and_title(
        self, integration_live_client: GoogleCalendarClient
    ) -> None:
        """Creating an event returns a payload with id and title."""
        result = dispatch_tool_call(
            "create_event",
            {
                "title": "[VCR] Create Test",
                "start": _NOW.isoformat(),
                "end": _END.isoformat(),
            },
            integration_live_client,
        )
        assert not result.is_error
        payload = json.loads(result.content)
        assert payload["title"] == "[VCR] Create Test"
        assert payload["id"]
        # Cleanup
        integration_live_client.delete_event(payload["id"])

    def test_description_defaults_to_empty_string(
        self, integration_live_client: GoogleCalendarClient
    ) -> None:
        """Omitting description creates an event with empty description."""
        result = dispatch_tool_call(
            "create_event",
            {"title": "[VCR] No Desc", "start": _NOW.isoformat(), "end": _END.isoformat()},
            integration_live_client,
        )
        assert not result.is_error
        payload = json.loads(result.content)
        event = integration_live_client.get_event(payload["id"])
        assert (event.description or "") == ""
        integration_live_client.delete_event(payload["id"])


@pytest.mark.vcr
class TestGetEvent:
    """dispatch_tool_call('get_event') against live Google Calendar."""

    def test_returns_correct_fields(
        self, integration_live_client: GoogleCalendarClient
    ) -> None:
        """Fetching a known event returns all expected fields."""
        created = integration_live_client.create_event(
            title="[VCR] Get Test", start=_NOW, end=_END
        )
        try:
            result = dispatch_tool_call(
                "get_event", {"event_id": created.id}, integration_live_client
            )
            assert not result.is_error
            payload = json.loads(result.content)
            assert payload["id"] == created.id
            assert payload["title"] == "[VCR] Get Test"
        finally:
            integration_live_client.delete_event(created.id)

    def test_nonexistent_event_returns_not_found(
        self, integration_live_client: GoogleCalendarClient
    ) -> None:
        """Requesting a non-existent event ID produces a not_found error result."""
        result = dispatch_tool_call(
            "get_event",
            {"event_id": "nonexistent-event-id-xyz-00000"},
            integration_live_client,
        )
        assert result.is_error
        payload = json.loads(result.content)
        assert payload["error_category"] == "not_found"


@pytest.mark.vcr
class TestDeleteEvent:
    """dispatch_tool_call('delete_event') against live Google Calendar."""

    def test_confirms_removal_and_event_is_gone(
        self, integration_live_client: GoogleCalendarClient
    ) -> None:
        """Deleting an event returns a success message and the event is unretrievable."""
        created = integration_live_client.create_event(
            title="[VCR] Delete Test", start=_NOW, end=_END
        )
        result = dispatch_tool_call(
            "delete_event", {"event_id": created.id}, integration_live_client
        )
        assert not result.is_error
        assert "deleted" in result.content.lower()
        # Verify the event is actually gone
        gone = dispatch_tool_call(
            "get_event", {"event_id": created.id}, integration_live_client
        )
        assert gone.is_error


class TestEdgeCases:
    """Pure-logic edge cases — no API calls, no VCR needed."""

    def test_unknown_tool_returns_error(
        self, integration_live_client: GoogleCalendarClient
    ) -> None:
        """An unrecognised tool name returns an is_error result."""
        result = dispatch_tool_call("make_coffee", {}, integration_live_client)
        assert result.is_error
        payload = json.loads(result.content)
        assert payload["error_category"] == "unknown_tool"
