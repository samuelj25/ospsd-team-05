"""Unit tests for the event CRUD routes."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from calendar_client_service.app import create_app
from calendar_client_service.dependencies import get_calendar_client

START = datetime(2025, 6, 1, 9, 0, tzinfo=UTC)
END = datetime(2025, 6, 1, 10, 0, tzinfo=UTC)
START_STR = START.isoformat()
END_STR = END.isoformat()
STAT_CODE_200 = 200
STAT_CODE_204 = 204
STAT_CODE_422 = 422
STAT_CODE_201 = 201


def make_mock_event(
    eid: str = "evt-1",
    title: str = "Test Event",
    location: str | None = "Room 101",
    description: str | None = "A test event",
) -> MagicMock:
    """Return a mock Event with sensible defaults."""
    e = MagicMock()
    e.id = eid
    e.title = title
    e.start_time = START
    e.end_time = END
    e.location = location
    e.description = description
    return e


@pytest.fixture
def mock_calendar_client() -> MagicMock:
    """Return a mock GoogleCalendarClient."""
    return MagicMock()


@pytest.fixture
def client(mock_calendar_client: MagicMock) -> TestClient:
    """Return a TestClient with the calendar client dependency overridden."""
    app = create_app()
    app.dependency_overrides[get_calendar_client] = lambda: mock_calendar_client
    return TestClient(app)


class TestListEvents:
    """Tests for GET /events."""

    def test_returns_200(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """List events returns HTTP 200."""
        mock_calendar_client.list_events.return_value = []
        response = client.get("/events", params={"start_time": START_STR, "end_time": END_STR})
        assert response.status_code == STAT_CODE_200

    def test_returns_list_of_events(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """List events returns a list of serialized event objects."""
        mock_calendar_client.list_events.return_value = [make_mock_event()]
        response = client.get("/events", params={"start_time": START_STR, "end_time": END_STR})
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "evt-1"
        assert data[0]["title"] == "Test Event"

    def test_returns_empty_list_when_no_events(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """List events returns an empty list when no events exist in range."""
        mock_calendar_client.list_events.return_value = []
        response = client.get("/events", params={"start_time": START_STR, "end_time": END_STR})
        assert response.json() == []

    def test_calls_get_events_with_correct_times(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """List events passes start_time and end_time to the client."""
        mock_calendar_client.list_events.return_value = []
        client.get("/events", params={"start_time": START_STR, "end_time": END_STR})
        mock_calendar_client.list_events.assert_called_once()

    def test_returns_422_when_missing_params(self, client: TestClient) -> None:
        """List events returns HTTP 422 when query params are missing."""
        response = client.get("/events")
        assert response.status_code == STAT_CODE_422


class TestGetEvent:
    """Tests for GET /events/{event_id}."""

    def test_returns_200(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """Get event returns HTTP 200 for a valid event."""
        mock_calendar_client.get_event.return_value = make_mock_event()
        response = client.get("/events/evt-1")
        assert response.status_code == STAT_CODE_200

    def test_returns_correct_event(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Get event returns the correct event fields."""
        mock_calendar_client.get_event.return_value = make_mock_event()
        response = client.get("/events/evt-1")
        data = response.json()
        assert data["id"] == "evt-1"
        assert data["title"] == "Test Event"
        assert data["location"] == "Room 101"
        assert data["description"] == "A test event"

    def test_calls_get_event_with_id(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Get event passes the correct event_id to the client."""
        mock_calendar_client.get_event.return_value = make_mock_event()
        client.get("/events/evt-1")
        mock_calendar_client.get_event.assert_called_once_with("evt-1")

    def test_optional_fields_can_be_none(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Get event handles events with no location or description."""
        mock_calendar_client.get_event.return_value = make_mock_event(
            location=None, description=None
        )
        response = client.get("/events/evt-1")
        data = response.json()
        assert data["location"] is None
        assert data["description"] is None


class TestCreateEvent:
    """Tests for POST /events."""

    def test_returns_201(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """Create event returns HTTP 201."""
        mock_calendar_client.create_event.return_value = make_mock_event(eid="new-1")
        response = client.post(
            "/events",
            json={"title": "New Event", "start_time": START_STR, "end_time": END_STR},
        )
        assert response.status_code == STAT_CODE_201

    def test_returns_created_event(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Create event returns the newly created event."""
        mock_calendar_client.create_event.return_value = make_mock_event(
            eid="new-1", title="New Event"
        )
        response = client.post(
            "/events",
            json={"title": "New Event", "start_time": START_STR, "end_time": END_STR},
        )
        assert response.json()["id"] == "new-1"
        assert response.json()["title"] == "New Event"

    def test_calls_create_event_once(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Create event calls client.create_event exactly once."""
        mock_calendar_client.create_event.return_value = make_mock_event()
        client.post(
            "/events",
            json={"title": "New Event", "start_time": START_STR, "end_time": END_STR},
        )
        mock_calendar_client.create_event.assert_called_once()

    def test_returns_422_when_missing_required_fields(self, client: TestClient) -> None:
        """Create event returns HTTP 422 when required fields are missing."""
        response = client.post("/events", json={"title": "No Times"})
        assert response.status_code == STAT_CODE_422

    def test_accepts_optional_location_and_description(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Create event accepts optional location and description fields."""
        mock_calendar_client.create_event.return_value = make_mock_event()
        response = client.post(
            "/events",
            json={
                "title": "Full Event",
                "start_time": START_STR,
                "end_time": END_STR,
                "location": "Room 101",
                "description": "Details here",
            },
        )
        assert response.status_code == STAT_CODE_201


class TestUpdateEvent:
    """Tests for PUT /events/{event_id}."""

    def test_returns_200(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """Update event returns HTTP 200."""
        mock_calendar_client.update_event.return_value = make_mock_event(title="Updated")
        response = client.put(
            "/events/evt-1",
            json={
                "id": "evt-1",
                "title": "Updated",
                "start_time": START_STR,
                "end_time": END_STR,
            },
        )
        assert response.status_code == STAT_CODE_200

    def test_returns_updated_event(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Update event returns the updated event body."""
        mock_calendar_client.update_event.return_value = make_mock_event(title="Updated Title")
        response = client.put(
            "/events/evt-1",
            json={
                "id": "evt-1",
                "title": "Updated Title",
                "start_time": START_STR,
                "end_time": END_STR,
            },
        )
        assert response.json()["title"] == "Updated Title"

    def test_calls_update_event_once(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Update event calls client.update_event exactly once."""
        mock_calendar_client.update_event.return_value = make_mock_event()
        client.put(
            "/events/evt-1",
            json={
                "id": "evt-1",
                "title": "Updated",
                "start_time": START_STR,
                "end_time": END_STR,
            },
        )
        mock_calendar_client.update_event.assert_called_once()

    def test_returns_422_when_missing_required_fields(self, client: TestClient) -> None:
        """Update event returns HTTP 422 when required fields are missing."""
        response = client.put("/events/evt-1", json={"title": "No Times"})
        assert response.status_code == STAT_CODE_422


class TestDeleteEvent:
    """Tests for DELETE /events/{event_id}."""

    def test_returns_204(self, client: TestClient) -> None:
        """Delete event returns HTTP 204 No Content."""
        response = client.delete("/events/evt-1")
        assert response.status_code == STAT_CODE_204

    def test_calls_delete_event_with_id(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Delete event passes the correct event_id to the client."""
        client.delete("/events/evt-1")
        mock_calendar_client.delete_event.assert_called_once_with("evt-1")

    def test_returns_no_body(self, client: TestClient) -> None:
        """Delete event returns an empty response body."""
        response = client.delete("/events/evt-1")
        assert response.content == b""
