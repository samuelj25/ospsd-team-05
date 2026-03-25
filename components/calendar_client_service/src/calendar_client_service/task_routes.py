"""Task CRUD endpoints for the calendar client service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from calendar_client_api.task import Task
from fastapi import APIRouter, Depends
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient  # noqa: TC002

from calendar_client_service.dependencies import get_calendar_client
from calendar_client_service.models import TaskCreate, TaskResponse, TaskUpdate


class _ServiceTask(Task):
    def __init__(  # noqa: PLR0913
        self,
        t_id: str,
        title: str,
        start: datetime,
        end: datetime,
        *,
        completed: bool,
        desc: str | None,
    ) -> None:
        self._id = t_id
        self._title = title
        self._start = start
        self._end = end
        self._completed = completed
        self._desc = desc

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def start_time(self) -> datetime:
        return self._start

    @property
    def end_time(self) -> datetime:
        return self._end

    @property
    def is_completed(self) -> bool:
        return self._completed

    @property
    def description(self) -> str | None:
        return self._desc


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
    tasks = client.get_tasks(start_time, end_time)
    return [
        TaskResponse(
            id=t.id,
            title=t.title,
            start_time=t.start_time,
            end_time=t.end_time,
            description=t.description,
            is_completed=t.is_completed,
        )
        for t in tasks
    ]


@router.get("/{task_id}", response_model=TaskResponse, summary="Get a single task")
def get_task(
    task_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """
    Return the task with the given ``task_id``.

    TODO: Implement using ``client.get_task(task_id)``.
    """
    t = client.get_task(task_id)
    return TaskResponse(
        id=t.id,
        title=t.title,
        start_time=t.start_time,
        end_time=t.end_time,
        description=t.description,
        is_completed=t.is_completed,
    )


@router.post("", response_model=TaskResponse, status_code=201, summary="Create a task")
def create_task(
    payload: TaskCreate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> TaskResponse:
    """
    Create a new task from ``payload``.

    TODO: Build a Task object from payload fields and call ``client.create_task(task)``.
    """
    now = datetime.now(tz=UTC)  # Fallback for tasks which only have end_time in create payload
    tk = _ServiceTask(
        t_id="",
        title=payload.title,
        start=now,
        end=payload.end_time,
        completed=False,
        desc=payload.description,
    )
    t = client.create_task(tk)
    return TaskResponse(
        id=t.id,
        title=t.title,
        start_time=t.start_time,
        end_time=t.end_time,
        description=t.description,
        is_completed=t.is_completed,
    )


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
    now = datetime.now(tz=UTC)
    tk = _ServiceTask(
        t_id=task_id,
        title=payload.title,
        start=now,
        end=payload.end_time,
        completed=payload.is_completed,
        desc=payload.description,
    )
    t = client.update_task(tk)
    return TaskResponse(
        id=t.id,
        title=t.title,
        start_time=t.start_time,
        end_time=t.end_time,
        description=t.description,
        is_completed=t.is_completed,
    )


@router.delete("/{task_id}", status_code=204, summary="Delete a task")
def delete_task(
    task_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> None:
    """
    Delete the task with the given ``task_id``.

    TODO: Implement using ``client.delete_task(task_id)``.
    """
    client.delete_task(task_id)


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
    client.mark_task_completed(task_id)
    t = client.get_task(task_id)
    return TaskResponse(
        id=t.id,
        title=t.title,
        start_time=t.start_time,
        end_time=t.end_time,
        description=t.description,
        is_completed=t.is_completed,
    )
