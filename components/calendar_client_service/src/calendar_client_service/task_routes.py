"""Task CRUD endpoints for the calendar client service."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Annotated

from fastapi import APIRouter, Depends
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient  # noqa: TC002

from calendar_client_service.dependencies import get_calendar_client
from calendar_client_service.models import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse], summary="List tasks in a time range")
def list_tasks(
    start_time: datetime,
    end_time: datetime,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> list[TaskResponse]:
    """
    Return all tasks between ``start_time`` and ``end_time``.

    TODO: Implement using ``client.get_tasks(start_time, end_time)``.
    """
    raise NotImplementedError


@router.get("/{task_id}", response_model=TaskResponse, summary="Get a single task")
def get_task(
    task_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """
    Return the task with the given ``task_id``.

    TODO: Implement using ``client.get_task(task_id)``.
    """
    raise NotImplementedError


@router.post("", response_model=TaskResponse, status_code=201, summary="Create a task")
def create_task(
    payload: TaskCreate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """
    Create a new task from ``payload``.

    TODO: Build a Task object from payload fields and call ``client.create_task(task)``.
    """
    raise NotImplementedError


@router.put("/{task_id}", response_model=TaskResponse, summary="Update a task")
def update_task(
    task_id: str,
    payload: TaskUpdate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """
    Update the task identified by ``task_id`` with data from ``payload``.

    TODO: Build a Task object and call ``client.update_task(task)``.
    """
    raise NotImplementedError


@router.delete("/{task_id}", status_code=204, summary="Delete a task")
def delete_task(
    task_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> None:
    """
    Delete the task with the given ``task_id``.

    TODO: Implement using ``client.delete_task(task_id)``.
    """
    raise NotImplementedError


@router.post("/{task_id}/complete", response_model=TaskResponse, summary="Mark task complete")
def complete_task(
    task_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """
    Mark the task identified by ``task_id`` as completed.

    TODO: Implement using ``client.mark_task_completed(task_id)``, then fetch
    and return the updated task.
    """
    raise NotImplementedError
