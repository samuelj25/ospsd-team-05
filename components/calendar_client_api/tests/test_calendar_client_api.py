"""
Tests for the calendar client API abstract base classes.

This module contains unit tests that verify the contracts and behavior
of the calendar_client_api.Client, calendar_client_api.Event, and
calendar_client_api.Task abstractions.

These tests use mocks to demonstrate how implementations should behave
and serve as documentation for the expected API contracts.
"""

import datetime as dt
from unittest.mock import Mock

from calendar_client_api import Client, Event, Task


def test_client_get_events_contract() -> None:
    """
    Verifies and demonstrates the contract for the `get_events` method.

    Any implementation of the Client abstraction must provide `get_events`
    which returns an iterator of Event objects for a provided time range.
    """
    # ARRANGE
    start = dt.datetime(2026, 2, 16, 9, 0, tzinfo=dt.UTC)
    end = dt.datetime(2026, 2, 16, 17, 0, tzinfo=dt.UTC)

    mock_event = Mock(spec=Event)
    mock_event.id = "evt_1"
    mock_event.title = "Team Meeting"

    mock_client = Mock(spec=Client)
    mock_client.get_events.return_value = iter([mock_event])

    # ACT
    events = mock_client.get_events(start_time=start, end_time=end)
    first_event = next(events, None)

    # ASSERT
    mock_client.get_events.assert_called_once_with(start_time=start, end_time=end)
    assert first_event is not None
    assert first_event.id == "evt_1"
    assert first_event.title == "Team Meeting"


def test_client_get_event_contract() -> None:
    """Verifies and demonstrates the contract for the `get_event` method."""
    # ARRANGE
    mock_event = Mock(spec=Event)
    mock_event.id = "evt_specific"

    mock_client = Mock(spec=Client)
    mock_client.get_event.return_value = mock_event

    # ACT
    retrieved_event = mock_client.get_event(event_id="evt_specific")

    # ASSERT
    mock_client.get_event.assert_called_once_with(event_id="evt_specific")
    assert retrieved_event.id == "evt_specific"


def test_client_delete_event_contract() -> None:
    """Verifies and demonstrates the contract for the `delete_event` method."""
    # ARRANGE
    mock_client = Mock(spec=Client)
    mock_client.delete_event.return_value = None

    # ACT
    mock_client.delete_event(event_id="evt_to_delete")

    # ASSERT
    mock_client.delete_event.assert_called_once_with(event_id="evt_to_delete")


def test_client_from_raw_data_contract() -> None:
    """Verifies and demonstrates the contract for the `from_raw_data` method."""
    # ARRANGE
    mock_event = Mock(spec=Event)
    mock_event.id = "evt_from_json"

    mock_client = Mock(spec=Client)
    mock_client.from_raw_data.return_value = mock_event

    # ACT
    retrieved_event = mock_client.from_raw_data(raw_data='{"id": "evt_from_json"}')

    # ASSERT
    mock_client.from_raw_data.assert_called_once_with(raw_data='{"id": "evt_from_json"}')
    assert retrieved_event.id == "evt_from_json"


def test_client_get_tasks_contract() -> None:
    """
    Verifies and demonstrates the contract for the `get_tasks` method.

    Any implementation of the Client abstraction must provide `get_tasks`
    which returns an iterator of Task objects for a provided time range.
    """
    # ARRANGE
    start = dt.datetime(2026, 2, 16, 9, 0, tzinfo=dt.UTC)
    end = dt.datetime(2026, 2, 16, 17, 0, tzinfo=dt.UTC)

    mock_task = Mock(spec=Task)
    mock_task.id = "tsk_1"
    mock_task.title = "Code HW1 draft"
    mock_task.is_completed = False

    mock_client = Mock(spec=Client)
    mock_client.get_tasks.return_value = iter([mock_task])

    # ACT
    tasks = mock_client.get_tasks(start_time=start, end_time=end)
    first_task = next(tasks, None)

    # ASSERT
    mock_client.get_tasks.assert_called_once_with(start_time=start, end_time=end)
    assert first_task is not None
    assert first_task.id == "tsk_1"
    assert first_task.title == "Code HW1 draft"
    assert first_task.is_completed is False


def test_client_get_task_contract() -> None:
    """Verifies and demonstrates the contract for the `get_task` method."""
    # ARRANGE
    mock_task = Mock(spec=Task)
    mock_task.id = "tsk_specific"

    mock_client = Mock(spec=Client)
    mock_client.get_task.return_value = mock_task

    # ACT
    retrieved_task = mock_client.get_task(task_id="tsk_specific")

    # ASSERT
    mock_client.get_task.assert_called_once_with(task_id="tsk_specific")
    assert retrieved_task.id == "tsk_specific"


def test_client_delete_task_contract() -> None:
    """Verifies and demonstrates the contract for the `delete_task` method."""
    # ARRANGE
    mock_client = Mock(spec=Client)
    mock_client.delete_task.return_value = None

    # ACT
    mock_client.delete_task(task_id="tsk_to_delete")

    # ASSERT
    mock_client.delete_task.assert_called_once_with(task_id="tsk_to_delete")


def test_client_mark_task_completed_contract() -> None:
    """Verifies and demonstrates the contract for the `mark_task_completed` method."""
    # ARRANGE
    mock_client = Mock(spec=Client)
    mock_client.mark_task_completed.return_value = None

    # ACT
    mock_client.mark_task_completed(task_id="tsk_to_complete")

    # ASSERT
    mock_client.mark_task_completed.assert_called_once_with(task_id="tsk_to_complete")
