"""Tests for task CRUD endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from calendar_client_service.app import app
from calendar_client_service.dependencies import get_calendar_client


# --- Helpers ---

def make_mock_task(
    t_id="task-1",
    title="Test Task",
    start=None,
    end=None,
    completed=False,
    desc="A description",
):
    task = MagicMock()
    task.id = t_id
    task.title = title
    task.start_time = start or datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
    task.end_time = end or datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    task.is_completed = completed
    task.description = desc
    return task


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def api_client(mock_client):
    app.dependency_overrides[get_calendar_client] = lambda: mock_client
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- GET /tasks ---

def test_list_tasks_returns_tasks(api_client, mock_client):
    task = make_mock_task()
    mock_client.get_tasks.return_value = [task]

    response = api_client.get("/tasks", params={
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-02T00:00:00Z",
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "task-1"
    assert data[0]["title"] == "Test Task"


def test_list_tasks_empty(api_client, mock_client):
    mock_client.get_tasks.return_value = []

    response = api_client.get("/tasks", params={
        "start_time": "2025-01-01T00:00:00Z",
        "end_time": "2025-01-02T00:00:00Z",
    })

    assert response.status_code == 200
    assert response.json() == []


# --- GET /tasks/{task_id} ---

def test_get_task_success(api_client, mock_client):
    task = make_mock_task(t_id="abc")
    mock_client.get_task.return_value = task

    response = api_client.get("/tasks/abc")

    assert response.status_code == 200
    assert response.json()["id"] == "abc"
    mock_client.get_task.assert_called_once_with("abc")


# --- POST /tasks ---

def test_create_task_success(api_client, mock_client):
    task = make_mock_task(t_id="new-1", title="New Task")
    mock_client.create_task.return_value = task

    response = api_client.post("/tasks", json={
        "title": "New Task",
        "end_time": "2025-01-01T10:00:00Z",
        "description": "A description",
    })

    assert response.status_code == 201
    assert response.json()["title"] == "New Task"
    mock_client.create_task.assert_called_once()


def test_create_task_no_description(api_client, mock_client):
    task = make_mock_task(t_id="new-2", title="No Desc", desc=None)
    mock_client.create_task.return_value = task

    response = api_client.post("/tasks", json={
        "title": "No Desc",
        "end_time": "2025-01-01T10:00:00Z",
    })

    assert response.status_code == 201
    assert response.json()["description"] is None


# --- PUT /tasks/{task_id} ---

def test_update_task_success(api_client, mock_client):
    updated = make_mock_task(t_id="task-1", title="Updated", completed=True)
    mock_client.update_task.return_value = updated

    response = api_client.put("/tasks/task-1", json={
        "title": "Updated",
        "end_time": "2025-01-01T11:00:00Z",
        "is_completed": True,
        "description": "A description",
    })

    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["is_completed"] is True
    mock_client.update_task.assert_called_once()


# --- DELETE /tasks/{task_id} ---

def test_delete_task_success(api_client, mock_client):
    response = api_client.delete("/tasks/task-1")

    assert response.status_code == 204
    mock_client.delete_task.assert_called_once_with("task-1")


# --- POST /tasks/{task_id}/complete ---

def test_complete_task_success(api_client, mock_client):
    completed_task = make_mock_task(t_id="task-1", completed=True)
    mock_client.get_task.return_value = completed_task

    response = api_client.post("/tasks/task-1/complete")

    assert response.status_code == 200
    assert response.json()["is_completed"] is True
    mock_client.mark_task_completed.assert_called_once_with("task-1")
    mock_client.get_task.assert_called_once_with("task-1")