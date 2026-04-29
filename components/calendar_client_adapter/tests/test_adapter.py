from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from calendar_client_api import EventNotFoundError
from calendar_client_service_api_client.models import EventResponse, TaskResponse

from calendar_client_adapter.adapter import ServiceAdapterClient


def test_get_event() -> None:
    client = ServiceAdapterClient("http://test", "fake_session")

    with patch("calendar_client_adapter.adapter.get_event_events_event_id_get.sync") as mock_get:
        mock_get.return_value = EventResponse(
            id="1",
            title="Test Event",
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
            location="Room",
            description="Desc",
        )

        event = client.get_event("1")
        assert event.id == "1"
        assert event.title == "Test Event"
        assert event.location == "Room"
        assert event.description == "Desc"


def test_get_event_not_found() -> None:
    client = ServiceAdapterClient("http://test", "fake_session")

    with patch("calendar_client_adapter.adapter.get_event_events_event_id_get.sync") as mock_get:
        mock_get.return_value = None
        with pytest.raises(EventNotFoundError):
            client.get_event("1")


def test_get_task() -> None:
    client = ServiceAdapterClient("http://test", "fake_session")

    with patch("calendar_client_adapter.adapter.get_task_tasks_task_id_get.sync") as mock_get:
        mock_get.return_value = TaskResponse(
            id="1",
            title="Test Task",
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
            is_completed=True,
            description="Desc",
        )

        task = client.get_task("1")
        assert task.id == "1"
        assert task.title == "Test Task"
        assert task.is_completed is True
