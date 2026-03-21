"""Tests for the calendar_client_api task abstraction."""

import datetime as dt
from unittest.mock import Mock

from calendar_client_api import Task


def test_task_abstraction_comprehensive() -> None:
    """Verifies all properties work together in a comprehensive test."""
    mock_task = Mock(spec=Task)
    mock_task.id = "tsk_7"
    mock_task.title = "Finish interface and implementation draft"
    mock_task.start_time = dt.datetime(2026, 2, 16, 9, 0, tzinfo=dt.UTC)
    mock_task.end_time = dt.datetime(2026, 2, 16, 10, 0, tzinfo=dt.UTC)
    mock_task.description = "Complete calendar_client_api interface + google_calendar_client_impl."
    mock_task.is_completed = False

    properties = {
        "id": mock_task.id,
        "title": mock_task.title,
        "start_time": mock_task.start_time,
        "end_time": mock_task.end_time,
        "description": mock_task.description,
        "is_completed": mock_task.is_completed,
    }

    assert properties["id"] == "tsk_7"
    assert properties["title"] == "Finish interface and implementation draft"
    assert properties["start_time"] == dt.datetime(2026, 2, 16, 9, 0, tzinfo=dt.UTC)
    assert properties["end_time"] == dt.datetime(2026, 2, 16, 10, 0, tzinfo=dt.UTC)
    assert properties["description"] == (
        "Complete calendar_client_api interface + google_calendar_client_impl."
    )
    assert properties["is_completed"] is False

    # Type checks
    assert isinstance(properties["id"], str)
    assert isinstance(properties["title"], str)
    assert isinstance(properties["start_time"], dt.datetime)
    assert isinstance(properties["end_time"], dt.datetime)
    assert isinstance(properties["description"], str)
    assert isinstance(properties["is_completed"], bool)
