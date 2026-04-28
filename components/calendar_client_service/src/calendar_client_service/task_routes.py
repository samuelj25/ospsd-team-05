"""Task CRUD endpoints for the calendar client service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient  # noqa: TC002

from calendar_client_service.dependencies import get_calendar_client
from calendar_client_service.models import TaskCreate, TaskResponse, TaskUpdate

if TYPE_CHECKING:
    from calendar_client_api.task import Task


def _to_task_response(t: Task) -> TaskResponse:
    # Provide fallback for strict datetime Pydantic models when Google returns None
    now = datetime.now(tz=UTC)
    return TaskResponse(
        id=t.id,
        title=t.title,
        start_time=t.start_time or now,
        end_time=t.end_time or now,
        description=t.description,
        is_completed=t.is_completed,
    )


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse], summary="List tasks in a time range")
def list_tasks(
    start_time: datetime,
    end_time: datetime,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> list[TaskResponse]:
    """Return all tasks between ``start_time`` and ``end_time``."""
    tasks = client.get_tasks(start_time, end_time)
    return [_to_task_response(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse, summary="Get a single task")
def get_task(
    task_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """Return the task with the given ``task_id``."""
    t = client.get_task(task_id)
    return _to_task_response(t)


@router.post("", response_model=TaskResponse, status_code=201, summary="Create a task")
def create_task(
    payload: TaskCreate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """Create a new task from ``payload``."""
    # Pass properties directly instead of building a middleman class
    t = client.create_task(
        title=payload.title,
        due=payload.end_time,
        description=payload.description
    )
    return _to_task_response(t)


@router.put("/{task_id}", response_model=TaskResponse, summary="Update a task")
def update_task(
    task_id: str,
    payload: TaskUpdate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """Update the task identified by ``task_id`` with data from ``payload``."""
    if task_id != payload.id:
        raise HTTPException(status_code=422, detail="Task ID in path and payload must match")

    t = client.update_task(
        task_id=task_id,
        title=payload.title,
        due=payload.end_time,
        is_completed=payload.is_completed,
        description=payload.description
    )
    return _to_task_response(t)


@router.delete("/{task_id}", status_code=204, summary="Delete a task")
def delete_task(
    task_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> None:
    """Delete the task with the given ``task_id``."""
    client.delete_task(task_id)


@router.post("/{task_id}/complete", response_model=TaskResponse, summary="Mark task complete")
def complete_task(
    task_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """Mark the task identified by ``task_id`` as completed."""
    client.mark_task_completed(task_id)
    t = client.get_task(task_id)
    return _to_task_response(t)
