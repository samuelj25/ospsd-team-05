"""Unit tests for AI tools dispatching and processing."""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient

from calendar_client_service.ai_tools import dispatch_tool_call


@pytest.fixture
def mock_calendar_client() -> MagicMock:
    """Fixture providing a mock GoogleCalendarClient."""
    return MagicMock(spec=GoogleCalendarClient)


def create_mock_event(
    event_id: str,
    title: str,
    start_time: datetime,
    end_time: datetime,
    description: str = "",
) -> MagicMock:
    """Create a mock event object for testing."""
    mock_event = MagicMock()
    mock_event.id = event_id
    mock_event.title = title
    mock_event.start_time = start_time
    mock_event.end_time = end_time
    mock_event.description = description
    return mock_event


def test_dispatch_tool_call_list_events(mock_calendar_client: MagicMock) -> None:
    """Test dispatching the list_events tool."""
    mock_event = create_mock_event(
        event_id="123",
        title="Test Event",
        start_time=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 23, 11, 0, tzinfo=UTC),
        description="Test Desc",
    )
    mock_calendar_client.list_events.return_value = [mock_event]

    args = {
        "start": "2026-04-23T00:00:00Z",
        "end": "2026-04-24T00:00:00Z"
    }
    result = dispatch_tool_call("list_events", args, mock_calendar_client)

    assert result.tool_name == "list_events"
    assert not result.is_error

    content = json.loads(result.content)
    assert len(content) == 1
    assert content[0]["id"] == "123"
    assert content[0]["title"] == "Test Event"
    assert content[0]["description"] == "Test Desc"


def test_dispatch_tool_call_create_event(mock_calendar_client: MagicMock) -> None:
    """Test dispatching the create_event tool."""
    mock_event = create_mock_event(
        event_id="456",
        title="New Event",
        start_time=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 23, 11, 0, tzinfo=UTC),
        description="New Desc",
    )
    mock_calendar_client.create_event.return_value = mock_event

    args = {
        "title": "New Event",
        "start": "2026-04-23T10:00:00Z",
        "end": "2026-04-23T11:00:00Z",
        "description": "New Desc"
    }
    result = dispatch_tool_call("create_event", args, mock_calendar_client)

    assert result.tool_name == "create_event"
    assert not result.is_error

    content = json.loads(result.content)
    assert content["id"] == "456"
    assert content["title"] == "New Event"


def test_dispatch_tool_call_get_event(mock_calendar_client: MagicMock) -> None:
    """Test dispatching the get_event tool."""
    mock_event = create_mock_event(
        event_id="789",
        title="Get Event",
        start_time=datetime(2026, 4, 23, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 4, 23, 11, 0, tzinfo=UTC),
        description="Get Desc",
    )
    mock_calendar_client.get_event.return_value = mock_event

    args = {"event_id": "789"}
    result = dispatch_tool_call("get_event", args, mock_calendar_client)

    assert result.tool_name == "get_event"
    assert not result.is_error

    content = json.loads(result.content)
    assert content["id"] == "789"
    assert content["title"] == "Get Event"
    assert content["description"] == "Get Desc"


def test_dispatch_tool_call_delete_event(mock_calendar_client: MagicMock) -> None:
    """Test dispatching the delete_event tool."""
    args = {"event_id": "101"}
    result = dispatch_tool_call("delete_event", args, mock_calendar_client)

    assert result.tool_name == "delete_event"
    assert not result.is_error
    assert result.content == "Event deleted successfully."
    mock_calendar_client.delete_event.assert_called_once_with("101")


def test_dispatch_tool_call_unknown_tool(mock_calendar_client: MagicMock) -> None:
    """Test dispatching an unknown tool returns an error."""
    result = dispatch_tool_call("unknown_tool", {}, mock_calendar_client)

    assert result.tool_name == "unknown_tool"
    assert result.is_error
    assert "Unknown tool" in result.content


def test_dispatch_tool_call_exception(mock_calendar_client: MagicMock) -> None:
    """Test that tool exceptions are caught and returned as errors."""
    mock_calendar_client.get_event.side_effect = Exception("Test Exception")

    args = {"event_id": "789"}
    result = dispatch_tool_call("get_event", args, mock_calendar_client)

    assert result.tool_name == "get_event"
    assert result.is_error
    assert "Test Exception" in result.content
