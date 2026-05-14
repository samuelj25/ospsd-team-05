"""
Tests for the calendar_task_api abstract base classes.

Verifies the contracts for Team-05's private task extension — task operations
defined in ``calendar_task_api.Client``.
"""

import datetime as dt
from unittest.mock import Mock

from calendar_client_api import Event

from calendar_task_api import Client, Task


def test_client_from_raw_data_contract() -> None:
    """Verifies and demonstrates the contract for the `from_raw_data` method."""
    mock_event = Mock(spec=Event)
    mock_event.id = "evt_from_json"

    mock_client = Mock(spec=Client)
    mock_client.from_raw_data.return_value = mock_event

    retrieved_event = mock_client.from_raw_data(raw_data='{"id": "evt_from_json"}')

    mock_client.from_raw_data.assert_called_once_with(raw_data='{"id": "evt_from_json"}')
    assert retrieved_event.id == "evt_from_json"


def test_client_get_tasks_contract() -> None:
    """
    Verifies and demonstrates the contract for the `get_tasks` method.

    Any implementation of the Client abstraction must provide `get_tasks`
    which returns an iterator of Task objects for a provided time range.
    """
    start = dt.datetime(2026, 2, 16, 9, 0, tzinfo=dt.UTC)
    end = dt.datetime(2026, 2, 16, 17, 0, tzinfo=dt.UTC)

    mock_task = Mock(spec=Task)
    mock_task.id = "tsk_1"
    mock_task.title = "Code HW1 draft"
    mock_task.is_completed = False

    mock_client = Mock(spec=Client)
    mock_client.get_tasks.return_value = iter([mock_task])

    tasks = mock_client.get_tasks(start_time=start, end_time=end)
    first_task = next(tasks, None)

    mock_client.get_tasks.assert_called_once_with(start_time=start, end_time=end)
    assert first_task is not None
    assert first_task.id == "tsk_1"
    assert first_task.title == "Code HW1 draft"
    assert first_task.is_completed is False


def test_client_get_task_contract() -> None:
    """Verifies and demonstrates the contract for the `get_task` method."""
    mock_task = Mock(spec=Task)
    mock_task.id = "tsk_specific"

    mock_client = Mock(spec=Client)
    mock_client.get_task.return_value = mock_task

    retrieved_task = mock_client.get_task(task_id="tsk_specific")

    mock_client.get_task.assert_called_once_with(task_id="tsk_specific")
    assert retrieved_task.id == "tsk_specific"


def test_client_delete_task_contract() -> None:
    """Verifies and demonstrates the contract for the `delete_task` method."""
    mock_client = Mock(spec=Client)
    mock_client.delete_task.return_value = None

    mock_client.delete_task(task_id="tsk_to_delete")

    mock_client.delete_task.assert_called_once_with(task_id="tsk_to_delete")


def test_client_mark_task_completed_contract() -> None:
    """Verifies and demonstrates the contract for the `mark_task_completed` method."""
    mock_client = Mock(spec=Client)
    mock_client.mark_task_completed.return_value = None

    mock_client.mark_task_completed(task_id="tsk_to_complete")

    mock_client.mark_task_completed.assert_called_once_with(task_id="tsk_to_complete")
