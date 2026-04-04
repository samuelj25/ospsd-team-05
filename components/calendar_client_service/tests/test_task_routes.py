"""Unit tests for the task CRUD routes."""

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


def make_mock_task(
    tid: str = "task-1",
    title: str = "Test Task",
    *,
    is_completed: bool = False,
    description: str | None = "A test task",
) -> MagicMock:
    """Return a mock Task with sensible defaults."""
    t = MagicMock()
    t.id = tid
    t.title = title
    t.start_time = START
    t.end_time = END
    t.is_completed = is_completed
    t.description = description
    return t





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





class TestListTasks:
    """Tests for GET /tasks."""

    def test_returns_200(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """List tasks returns HTTP 200."""
        mock_calendar_client.get_tasks.return_value = []
        response = client.get("/tasks", params={"start_time": START_STR, "end_time": END_STR})
        assert response.status_code == STAT_CODE_200

    def test_returns_list_of_tasks(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """List tasks returns a list of serialized task objects."""
        mock_calendar_client.get_tasks.return_value = [make_mock_task()]
        response = client.get("/tasks", params={"start_time": START_STR, "end_time": END_STR})
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "task-1"
        assert data[0]["title"] == "Test Task"

    def test_returns_empty_list_when_no_tasks(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """List tasks returns an empty list when no tasks exist in range."""
        mock_calendar_client.get_tasks.return_value = []
        response = client.get("/tasks", params={"start_time": START_STR, "end_time": END_STR})
        assert response.json() == []

    def test_calls_get_tasks_with_correct_times(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """List tasks passes start_time and end_time to the client."""
        mock_calendar_client.get_tasks.return_value = []
        client.get("/tasks", params={"start_time": START_STR, "end_time": END_STR})
        mock_calendar_client.get_tasks.assert_called_once()

    def test_returns_422_when_missing_params(self, client: TestClient) -> None:
        """List tasks returns HTTP 422 when query params are missing."""
        response = client.get("/tasks")
        assert response.status_code == STAT_CODE_422





class TestGetTask:
    """Tests for GET /tasks/{task_id}."""

    def test_returns_200(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """Get task returns HTTP 200 for a valid task."""
        mock_calendar_client.get_task.return_value = make_mock_task()
        response = client.get("/tasks/task-1")
        assert response.status_code == STAT_CODE_200

    def test_returns_correct_task(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Get task returns the correct task fields."""
        mock_calendar_client.get_task.return_value = make_mock_task()
        response = client.get("/tasks/task-1")
        data = response.json()
        assert data["id"] == "task-1"
        assert data["title"] == "Test Task"
        assert data["is_completed"] is False
        assert data["description"] == "A test task"

    def test_calls_get_task_with_id(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Get task passes the correct task_id to the client."""
        mock_calendar_client.get_task.return_value = make_mock_task()
        client.get("/tasks/task-1")
        mock_calendar_client.get_task.assert_called_once_with("task-1")

    def test_returns_completed_task(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Get task correctly reflects is_completed=True."""
        mock_calendar_client.get_task.return_value = make_mock_task(is_completed=True)
        response = client.get("/tasks/task-1")
        assert response.json()["is_completed"] is True

    def test_optional_description_can_be_none(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Get task handles tasks with no description."""
        mock_calendar_client.get_task.return_value = make_mock_task(description=None)
        response = client.get("/tasks/task-1")
        assert response.json()["description"] is None





class TestCreateTask:
    """Tests for POST /tasks."""

    def test_returns_201(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """Create task returns HTTP 201."""
        mock_calendar_client.create_task.return_value = make_mock_task(tid="new-1")
        response = client.post(
            "/tasks",
            json={"title": "New Task", "end_time": END_STR},
        )
        assert response.status_code == STAT_CODE_201

    def test_returns_created_task(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Create task returns the newly created task."""
        mock_calendar_client.create_task.return_value = make_mock_task(
            tid="new-1", title="New Task"
        )
        response = client.post(
            "/tasks",
            json={"title": "New Task", "end_time": END_STR},
        )
        assert response.json()["id"] == "new-1"
        assert response.json()["title"] == "New Task"

    def test_new_task_is_not_completed(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Create task returns a task with is_completed=False."""
        mock_calendar_client.create_task.return_value = make_mock_task(is_completed=False)
        response = client.post(
            "/tasks",
            json={"title": "New Task", "end_time": END_STR},
        )
        assert response.json()["is_completed"] is False

    def test_calls_create_task_once(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Create task calls client.create_task exactly once."""
        mock_calendar_client.create_task.return_value = make_mock_task()
        client.post("/tasks", json={"title": "New Task", "end_time": END_STR})
        mock_calendar_client.create_task.assert_called_once()

    def test_returns_422_when_missing_required_fields(self, client: TestClient) -> None:
        """Create task returns HTTP 422 when required fields are missing."""
        response = client.post("/tasks", json={"title": "No End Time"})
        assert response.status_code == STAT_CODE_422

    def test_accepts_optional_description(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Create task accepts an optional description field."""
        mock_calendar_client.create_task.return_value = make_mock_task()
        response = client.post(
            "/tasks",
            json={"title": "Task With Desc", "end_time": END_STR, "description": "Details"},
        )
        assert response.status_code == STAT_CODE_201




class TestUpdateTask:
    """Tests for PUT /tasks/{task_id}."""

    def test_returns_200(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """Update task returns HTTP 200."""
        mock_calendar_client.update_task.return_value = make_mock_task(title="Updated")
        response = client.put(
            "/tasks/task-1",
            json={"id": "task-1", "title": "Updated", "end_time": END_STR},
        )
        assert response.status_code == STAT_CODE_200

    def test_returns_updated_task(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Update task returns the updated task body."""
        mock_calendar_client.update_task.return_value = make_mock_task(title="Updated Title")
        response = client.put(
            "/tasks/task-1",
            json={"id": "task-1", "title": "Updated Title", "end_time": END_STR},
        )
        assert response.json()["title"] == "Updated Title"

    def test_can_mark_completed_via_update(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Update task can set is_completed=True."""
        mock_calendar_client.update_task.return_value = make_mock_task(is_completed=True)
        response = client.put(
            "/tasks/task-1",
            json={
                "id": "task-1",
                "title": "Done Task",
                "end_time": END_STR,
                "is_completed": True,
            },
        )
        assert response.json()["is_completed"] is True

    def test_calls_update_task_once(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Update task calls client.update_task exactly once."""
        mock_calendar_client.update_task.return_value = make_mock_task()
        client.put(
            "/tasks/task-1",
            json={"id": "task-1", "title": "Updated", "end_time": END_STR},
        )
        mock_calendar_client.update_task.assert_called_once()

    def test_returns_422_when_missing_required_fields(self, client: TestClient) -> None:
        """Update task returns HTTP 422 when required fields are missing."""
        response = client.put("/tasks/task-1", json={"title": "No End Time"})
        assert response.status_code == STAT_CODE_422




class TestDeleteTask:
    """Tests for DELETE /tasks/{task_id}."""

    def test_returns_204(self, client: TestClient) -> None:
        """Delete task returns HTTP 204 No Content."""
        response = client.delete("/tasks/task-1")
        assert response.status_code == STAT_CODE_204

    def test_calls_delete_task_with_id(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Delete task passes the correct task_id to the client."""
        client.delete("/tasks/task-1")
        mock_calendar_client.delete_task.assert_called_once_with("task-1")

    def test_returns_no_body(self, client: TestClient) -> None:
        """Delete task returns an empty response body."""
        response = client.delete("/tasks/task-1")
        assert response.content == b""




class TestCompleteTask:
    """Tests for POST /tasks/{task_id}/complete."""

    def test_returns_200(self, client: TestClient, mock_calendar_client: MagicMock) -> None:
        """Complete task returns HTTP 200."""
        mock_calendar_client.get_task.return_value = make_mock_task(is_completed=True)
        response = client.post("/tasks/task-1/complete")
        assert response.status_code == STAT_CODE_200

    def test_returns_task_with_is_completed_true(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Complete task returns the task with is_completed=True."""
        mock_calendar_client.get_task.return_value = make_mock_task(is_completed=True)
        response = client.post("/tasks/task-1/complete")
        assert response.json()["is_completed"] is True

    def test_calls_mark_task_completed_with_id(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Complete task calls mark_task_completed with the correct task_id."""
        mock_calendar_client.get_task.return_value = make_mock_task(is_completed=True)
        client.post("/tasks/task-1/complete")
        mock_calendar_client.mark_task_completed.assert_called_once_with("task-1")

    def test_fetches_updated_task_after_completing(
        self, client: TestClient, mock_calendar_client: MagicMock
    ) -> None:
        """Complete task calls get_task to fetch the updated state after marking complete."""
        mock_calendar_client.get_task.return_value = make_mock_task(is_completed=True)
        client.post("/tasks/task-1/complete")
        mock_calendar_client.get_task.assert_called_once_with("task-1")
