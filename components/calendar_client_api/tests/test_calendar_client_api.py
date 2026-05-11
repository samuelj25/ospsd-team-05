"""
Tests for the calendar_client_api abstract base classes.

Verifies the contracts for the shared vertical API — event operations
defined in ``ospsd_calendar_api.CalendarClient``.
"""

import datetime as dt
from unittest.mock import Mock

from calendar_client_api import CalendarClient, Event


def test_client_list_events_contract() -> None:
    """
    Verifies and demonstrates the contract for the `list_events` method.

    Any implementation of the Client abstraction must provide `list_events`
    which returns a list of Event objects for a provided time range.
    """
    start = dt.datetime(2026, 2, 16, 9, 0, tzinfo=dt.UTC)
    end = dt.datetime(2026, 2, 16, 17, 0, tzinfo=dt.UTC)

    mock_event = Mock(spec=Event)
    mock_event.id = "evt_1"
    mock_event.title = "Team Meeting"

    mock_client = Mock(spec=CalendarClient)
    mock_client.list_events.return_value = [mock_event]

    events = mock_client.list_events(start_time=start, end_time=end)
    first_event = events[0] if events else None

    mock_client.list_events.assert_called_once_with(start_time=start, end_time=end)
    assert first_event is not None
    assert first_event.id == "evt_1"
    assert first_event.title == "Team Meeting"


def test_client_get_event_contract() -> None:
    """Verifies and demonstrates the contract for the `get_event` method."""
    mock_event = Mock(spec=Event)
    mock_event.id = "evt_specific"

    mock_client = Mock(spec=CalendarClient)
    mock_client.get_event.return_value = mock_event

    retrieved_event = mock_client.get_event(event_id="evt_specific")

    mock_client.get_event.assert_called_once_with(event_id="evt_specific")
    assert retrieved_event.id == "evt_specific"


def test_client_delete_event_contract() -> None:
    """Verifies and demonstrates the contract for the `delete_event` method."""
    mock_client = Mock(spec=CalendarClient)
    mock_client.delete_event.return_value = None

    mock_client.delete_event(event_id="evt_to_delete")

    mock_client.delete_event.assert_called_once_with(event_id="evt_to_delete")
