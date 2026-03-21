import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from calendar_client_service.app import app
from calendar_client_service.dependencies import get_calendar_client
from calendar_client_api.event import Event
from calendar_client_api.task import Task
from calendar_client_adapter.adapter import ServiceAdapterClient

class MockBaseEvent(Event):
    def __init__(self, e_id: str, title: str, start: datetime, end: datetime) -> None:
        self._id = e_id
        self._title = title
        self._start = start
        self._end = end
    @property
    def id(self) -> str: return self._id
    @property
    def title(self) -> str: return self._title
    @property
    def start_time(self) -> datetime: return self._start
    @property
    def end_time(self) -> datetime: return self._end
    @property
    def location(self) -> str | None: return None
    @property
    def description(self) -> str | None: return None

class MockBaseTask(Task):
    def __init__(self, t_id: str, title: str, start: datetime, end: datetime, is_completed: bool) -> None:
        self._id = t_id
        self._title = title
        self._start = start
        self._end = end
        self._is_completed = is_completed
    @property
    def id(self) -> str: return self._id
    @property
    def title(self) -> str: return self._title
    @property
    def start_time(self) -> datetime: return self._start
    @property
    def end_time(self) -> datetime: return self._end
    @property
    def is_completed(self) -> bool: return self._is_completed
    @property
    def description(self) -> str | None: return None

def test_adapter_integration() -> None:
    mock_google_client = MagicMock()
    
    # Mock get_event
    dt = datetime.now(UTC)
    mock_google_client.get_event.return_value = MockBaseEvent("100", "Integro Event", dt, dt)
    mock_google_client.get_task.return_value = MockBaseTask("200", "Integro Task", dt, dt, True)
    
    # Override FastAPI dependency
    app.dependency_overrides[get_calendar_client] = lambda: mock_google_client
    
    # Use TestClient's internal transport to handle synchronous requests
    test_client = TestClient(app)
    adapter = ServiceAdapterClient("http://testserver", "fake_session", httpx_args={"transport": test_client._transport})
    
    # Test Event integration
    event = adapter.get_event("100")
    assert event.id == "100"
    assert event.title == "Integro Event"
    mock_google_client.get_event.assert_called_once_with("100")
    
    # Test Task integration
    task = adapter.get_task("200")
    assert task.id == "200"
    assert task.title == "Integro Task"
    assert task.is_completed is True
    mock_google_client.get_task.assert_called_once_with("200")
    
    app.dependency_overrides.clear()
