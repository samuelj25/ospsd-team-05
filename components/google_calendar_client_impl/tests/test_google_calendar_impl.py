"""Tests for the Google Calendar client implementation."""

# ruff: noqa: SLF001

import os
from datetime import UTC, datetime
from unittest.mock import patch

import calendar_client_api
import pytest

from google_calendar_client_impl import GoogleCalendarClient
from google_calendar_client_impl.event_impl import GoogleCalendarEvent

# ---------------------------------------------------------------------------
# connect() tests
# ---------------------------------------------------------------------------


def test_google_client_connect_mocks() -> None:
    """Test that connect() calls get_credentials and builds services."""
    with patch("google_calendar_client_impl.google_calendar_impl.get_credentials"), \
         patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient()
        # Should not raise
        client.connect()
        assert client._service is not None
        assert client._tasks_service is not None


def test_google_client_connect_picks_up_calendar_id_from_env() -> None:
    """Test that connect() reads GOOGLE_CALENDAR_ID env var when calendar_id is default."""
    with patch.dict(os.environ, {"GOOGLE_CALENDAR_ID": "custom@group.calendar.google.com"}), \
         patch("google_calendar_client_impl.google_calendar_impl.get_credentials"), \
         patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient()
        client.connect()
        assert client.calendar_id == "custom@group.calendar.google.com"


# ---------------------------------------------------------------------------
# Event tests
# ---------------------------------------------------------------------------


def test_google_client_get_events_with_mock() -> None:
    """Test get_events returns an iterator mapping Google JSON to GoogleCalendarEvent objects."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient(calendar_id="primary")

        mock_service = patch("googleapiclient.discovery.Resource").start()
        client._service = mock_service

        mock_events = mock_service.events.return_value
        mock_list = mock_events.list.return_value
        mock_list.execute.return_value = {
            "items": [
                {
                    "id": "event_123",
                    "summary": "Team Meeting",
                    "start": {"dateTime": "2026-02-16T09:00:00+00:00"},
                    "end": {"dateTime": "2026-02-16T10:00:00+00:00"},
                },
            ],
        }

        start = datetime(2026, 2, 16, 9, 0, tzinfo=UTC)
        end = datetime(2026, 2, 16, 10, 0, tzinfo=UTC)

        events_iter = client.get_events(start_time=start, end_time=end)

        events_list = list(events_iter)
        assert len(events_list) == 1

        event = events_list[0]
        assert event.id == "event_123"
        assert event.title == "Team Meeting"
        assert event.start_time.isoformat() == "2026-02-16T09:00:00+00:00"


def test_google_calendar_event_missing_id() -> None:
    """Test ValueError is raised when id is missing from raw data."""
    event = GoogleCalendarEvent({"summary": "no id"})
    with pytest.raises(ValueError, match="Event must have an ID"):
        _ = event.id


# ---------------------------------------------------------------------------
# MockEvent helper
# ---------------------------------------------------------------------------


class MockEvent(calendar_client_api.Event):
    """Mock Event for testing CRUD methods."""

    def __init__(  # noqa: PLR0913
        self,
        e_id: str,
        title: str,
        start: datetime,
        end: datetime,
        loc: str | None = None,
        desc: str | None = None,
    ) -> None:
        """Initialize mock event."""
        self._id = e_id
        self._title = title
        self._start_time = start
        self._end_time = end
        self._location = loc
        self._description = desc

    @property
    def id(self) -> str:
        """Return event ID."""
        return self._id

    @property
    def title(self) -> str:
        """Return event title."""
        return self._title

    @property
    def start_time(self) -> datetime:
        """Return event start time."""
        return self._start_time

    @property
    def end_time(self) -> datetime:
        """Return event end time."""
        return self._end_time

    @property
    def location(self) -> str | None:
        """Return event location."""
        return self._location

    @property
    def description(self) -> str | None:
        """Return event description."""
        return self._description


def test_google_client_get_event_with_mock() -> None:
    """Test get_event retrieves and parses a single event."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient(calendar_id="primary")
        mock_service = patch("googleapiclient.discovery.Resource").start()
        client._service = mock_service

        mock_events = mock_service.events.return_value
        mock_get = mock_events.get.return_value
        mock_get.execute.return_value = {
            "id": "single_123",
            "summary": "Single Event",
            "start": {"dateTime": "2026-02-18T10:00:00+00:00"},
            "end": {"dateTime": "2026-02-18T11:00:00+00:00"},
            "location": "Room 1",
            "description": "Desc",
        }

        event = client.get_event("single_123")
        assert event.id == "single_123"
        assert event.title == "Single Event"
        assert event.location == "Room 1"
        assert event.description == "Desc"


def test_google_client_create_event_with_mock() -> None:
    """Test create_event calls the insert API with correctly formatted body."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient(calendar_id="primary")
        mock_service = patch("googleapiclient.discovery.Resource").start()
        client._service = mock_service

        mock_events = mock_service.events.return_value
        mock_insert = mock_events.insert.return_value

        mock_insert.execute.return_value = {
            "id": "new_123",
            "summary": "New Event",
            "start": {"dateTime": "2026-02-20T10:00:00+00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-02-20T11:00:00+00:00", "timeZone": "UTC"},
        }

        start = datetime(2026, 2, 20, 10, 0, tzinfo=UTC)
        end = datetime(2026, 2, 20, 11, 0, tzinfo=UTC)
        input_event = MockEvent("ignore", "New Event", start, end)

        new_event = client.create_event(input_event)

        mock_events.insert.assert_called_once()
        _, kwargs = mock_events.insert.call_args
        assert kwargs["calendarId"] == "primary"
        assert kwargs["body"]["summary"] == "New Event"
        assert kwargs["body"]["start"]["dateTime"] == "2026-02-20T10:00:00+00:00"

        assert new_event.id == "new_123"


def test_google_client_update_event_with_mock() -> None:
    """Test update_event calls the update API."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient(calendar_id="primary")
        mock_service = patch("googleapiclient.discovery.Resource").start()
        client._service = mock_service

        mock_events = mock_service.events.return_value
        mock_update = mock_events.update.return_value
        mock_update.execute.return_value = {
            "id": "update_123",
            "summary": "Updated Event",
            "start": {"dateTime": "2026-02-21T10:00:00+00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-02-21T11:00:00+00:00", "timeZone": "UTC"},
        }

        start = datetime(2026, 2, 21, 10, 0, tzinfo=UTC)
        end = datetime(2026, 2, 21, 11, 0, tzinfo=UTC)
        input_event = MockEvent("update_123", "Updated Event", start, end)

        updated_event = client.update_event(input_event)

        mock_events.update.assert_called_once()
        _, kwargs = mock_events.update.call_args
        assert kwargs["eventId"] == "update_123"
        assert updated_event.id == "update_123"
        assert updated_event.title == "Updated Event"


# ---------------------------------------------------------------------------
# MockTask helper
# ---------------------------------------------------------------------------


class MockTask(calendar_client_api.Task):
    """Mock Task for testing CRUD methods."""

    def __init__(
        self,
        t_id: str,
        title: str,
        end: datetime,
        *,
        is_completed: bool,
        desc: str | None = None,
    ) -> None:
        """Initialize mock task."""
        self._id = t_id
        self._title = title
        self._start_time = end
        self._end_time = end
        self._is_completed = is_completed
        self._description = desc

    @property
    def id(self) -> str:
        """Return task ID."""
        return self._id

    @property
    def title(self) -> str:
        """Return task title."""
        return self._title

    @property
    def start_time(self) -> datetime:
        """Return task start time."""
        return self._start_time

    @property
    def end_time(self) -> datetime:
        """Return task end time."""
        return self._end_time

    @property
    def is_completed(self) -> bool:
        """Return whether the task is completed."""
        return self._is_completed

    @property
    def description(self) -> str | None:
        """Return task description."""
        return self._description


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


def test_google_client_get_task_with_mock() -> None:
    """Test get_task retrieves and parses a single task."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient()
        mock_tasks_svc = patch("googleapiclient.discovery.Resource").start()
        client._tasks_service = mock_tasks_svc

        mock_tasks = mock_tasks_svc.tasks.return_value
        mock_get = mock_tasks.get.return_value
        mock_get.execute.return_value = {
            "id": "task_123",
            "title": "Buy Milk",
            "due": "2026-02-28T00:00:00.000Z",
            "status": "needsAction",
            "notes": "Testing task fetch",
        }

        task = client.get_task("task_123")
        assert task.id == "task_123"
        assert task.title == "Buy Milk"
        assert not task.is_completed


def test_google_client_create_task_with_mock() -> None:
    """Test create_task calls the insert API with correctly formatted body."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient()
        mock_tasks_svc = patch("googleapiclient.discovery.Resource").start()
        client._tasks_service = mock_tasks_svc

        mock_tasks = mock_tasks_svc.tasks.return_value
        mock_insert = mock_tasks.insert.return_value
        mock_insert.execute.return_value = {
            "id": "new_task",
            "title": "New Task",
            "due": "2026-03-01T00:00:00.000Z",
            "status": "completed",
            "notes": "Testing creation",
        }

        end = datetime(2026, 3, 1, tzinfo=UTC)
        input_task = MockTask("ignore", "New Task", end, is_completed=True, desc="Testing creation")

        new_task = client.create_task(input_task)
        assert new_task.id == "new_task"
        assert new_task.is_completed
        mock_tasks.insert.assert_called_once()
        _, kwargs = mock_tasks.insert.call_args
        assert kwargs["body"]["title"] == "New Task"
        assert kwargs["body"]["status"] == "completed"


def test_google_client_update_task_with_mock() -> None:
    """Test update_task calls the update API."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient()
        mock_tasks_svc = patch("googleapiclient.discovery.Resource").start()
        client._tasks_service = mock_tasks_svc

        mock_tasks = mock_tasks_svc.tasks.return_value
        mock_update = mock_tasks.update.return_value
        mock_update.execute.return_value = {
            "id": "update_task",
            "title": "Updated Task",
            "due": "2026-03-02T00:00:00.000Z",
            "status": "needsAction",
        }

        end = datetime(2026, 3, 2, tzinfo=UTC)
        input_task = MockTask("update_task", "Updated Task", end, is_completed=False)

        updated_task = client.update_task(input_task)
        assert updated_task.title == "Updated Task"
        mock_tasks.update.assert_called_once()
        _, kwargs = mock_tasks.update.call_args
        assert kwargs["task"] == "update_task"


def test_google_client_delete_task_with_mock() -> None:
    """Test delete_task calls the delete API."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient()
        mock_tasks_svc = patch("googleapiclient.discovery.Resource").start()
        client._tasks_service = mock_tasks_svc

        mock_tasks = mock_tasks_svc.tasks.return_value

        client.delete_task("del_task_123")
        mock_tasks.delete.assert_called_once()
        _, kwargs = mock_tasks.delete.call_args
        assert kwargs["task"] == "del_task_123"


def test_google_client_get_tasks_with_mock() -> None:
    """Test get_tasks returns an iterator of parsed tasks."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient()
        mock_tasks_svc = patch("googleapiclient.discovery.Resource").start()
        client._tasks_service = mock_tasks_svc

        mock_tasks = mock_tasks_svc.tasks.return_value
        mock_list = mock_tasks.list.return_value
        mock_list.execute.return_value = {
            "items": [
                {
                    "id": "task_1",
                    "title": "Task 1",
                    "due": "2026-02-16T09:00:00.000Z",
                    "status": "completed",
                },
            ],
        }

        start = datetime(2026, 2, 16, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 16, 23, 59, tzinfo=UTC)

        tasks_iter = client.get_tasks(start_time=start, end_time=end)
        tasks_list = list(tasks_iter)

        assert len(tasks_list) == 1
        assert tasks_list[0].id == "task_1"
        assert tasks_list[0].is_completed


def test_google_client_mark_task_completed_with_mock() -> None:
    """Test mark_task_completed patches the task status to completed."""
    with patch("google_calendar_client_impl.google_calendar_impl.build"):
        client = GoogleCalendarClient()
        mock_tasks_svc = patch("googleapiclient.discovery.Resource").start()
        client._tasks_service = mock_tasks_svc

        mock_tasks = mock_tasks_svc.tasks.return_value

        # Mock the get call that mark_task_completed does first
        mock_get = mock_tasks.get.return_value
        mock_get.execute.return_value = {
            "id": "task_to_mark",
            "title": "Pending",
            "status": "needsAction",
        }

        client.mark_task_completed("task_to_mark")

        mock_tasks.update.assert_called_once()
        _, kwargs = mock_tasks.update.call_args
        assert kwargs["body"]["status"] == "completed"
