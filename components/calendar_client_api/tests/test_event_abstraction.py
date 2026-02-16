"""Tests for the calendar_client_api event abstraction."""

import datetime as dt
from unittest.mock import Mock

from calendar_client_api import Event


def test_event_abstraction_comprehensive() -> None:
    """Verifies all properties work together in a comprehensive test."""
    mock_event = Mock(spec=Event)
    mock_event.id = "evt_7"
    mock_event.title = "Test Event"
    mock_event.start_time = dt.datetime(2026, 2, 16, 14, 45, tzinfo=dt.UTC)
    mock_event.end_time = dt.datetime(2026, 2, 16, 15, 15, tzinfo=dt.UTC)

    # Optional fields (your base class defines them but currently returns None by default)
    mock_event.location = "NYU Tandon"
    mock_event.description = "Test description."

    properties = {
        "id": mock_event.id,
        "title": mock_event.title,
        "start_time": mock_event.start_time,
        "end_time": mock_event.end_time,
        "location": mock_event.location,
        "description": mock_event.description,
    }

    assert properties["id"] == "evt_7"
    assert properties["title"] == "Test Event"
    assert properties["start_time"] == dt.datetime(2026, 2, 16, 14, 45, tzinfo=dt.UTC)
    assert properties["end_time"] == dt.datetime(2026, 2, 16, 15, 15, tzinfo=dt.UTC)
    assert properties["location"] == "NYU Tandon"
    assert properties["description"] == "Test description."

    # Type checks (note start/end are datetime, not str)
    assert isinstance(properties["id"], str)
    assert isinstance(properties["title"], str)
    assert isinstance(properties["start_time"], dt.datetime)
    assert isinstance(properties["end_time"], dt.datetime)
    assert isinstance(properties["location"], str)
    assert isinstance(properties["description"], str)
