"""Calendar tool definitions and dispatcher for Gemini tool calling."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ai_client_api.models import ToolDefinition, ToolResult
from calendar_task_api.exceptions import TaskNotFoundError
from ospsd_calendar_api.exceptions import CalendarOperationError, EventNotFoundError
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from calendar_task_api.client import Client as CalendarClient


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic arg schemas — validated at dispatch time so the AI cannot pass
# malformed args without an explicit error_category in the ToolResult.
# ---------------------------------------------------------------------------


class _ListEventsArgs(BaseModel):
    start: datetime
    end: datetime


class _CreateEventArgs(BaseModel):
    title: str
    start: datetime
    end: datetime
    location: str = ""
    description: str = ""


class _GetEventArgs(BaseModel):
    event_id: str


class _UpdateEventArgs(BaseModel):
    event_id: str
    title: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    location: str | None = None
    description: str | None = None


class _DeleteEventArgs(BaseModel):
    event_id: str


class _ListTasksArgs(BaseModel):
    start: datetime
    end: datetime


class _CreateTaskArgs(BaseModel):
    title: str
    due: datetime | None = None
    description: str = ""


class _GetTaskArgs(BaseModel):
    task_id: str


class _UpdateTaskArgs(BaseModel):
    task_id: str
    title: str | None = None
    due: datetime | None = None
    description: str | None = None
    is_completed: bool | None = None


class _DeleteTaskArgs(BaseModel):
    task_id: str


class _MarkTaskCompletedArgs(BaseModel):
    task_id: str

# ---------------------------------------------------------------------------
# Tool definitions — passed to GeminiAIClient so the model knows what to call
# ---------------------------------------------------------------------------

CALENDAR_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="list_events",
        description=(
            "List calendar events within a time range. "
            "Use ISO 8601 strings for start and end (e.g. '2026-04-23T00:00:00Z')."
        ),
        parameters={
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "description": "Start of the time range in ISO 8601 format.",
                },
                "end": {
                    "type": "string",
                    "description": "End of the time range in ISO 8601 format.",
                },
            },
            "required": ["start", "end"],
        },
    ),
    ToolDefinition(
        name="create_event",
        description="Create a new calendar event.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title / summary."},
                "start": {
                    "type": "string",
                    "description": "Event start time in ISO 8601 format.",
                },
                "end": {
                    "type": "string",
                    "description": "Event end time in ISO 8601 format.",
                },
                "location": {
                    "type": "string",
                    "description": "Optional event location.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional event description.",
                },
            },
            "required": ["title", "start", "end"],
        },
    ),
    ToolDefinition(
        name="get_event",
        description="Get a single calendar event by its ID.",
        parameters={
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The event ID."},
            },
            "required": ["event_id"],
        },
    ),
    ToolDefinition(
        name="update_event",
        description="Update a calendar event by its ID.",
        parameters={
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The event ID to update."},
                "title": {"type": "string", "description": "Optional new event title."},
                "start": {
                    "type": "string",
                    "description": "Optional new event start time in ISO 8601 format.",
                },
                "end": {
                    "type": "string",
                    "description": "Optional new event end time in ISO 8601 format.",
                },
                "location": {
                    "type": "string",
                    "description": "Optional new event location.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional new event description.",
                },
            },
            "required": ["event_id"],
        },
    ),
    ToolDefinition(
        name="delete_event",
        description="Delete a calendar event by its ID.",
        parameters={
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The event ID to delete."},
            },
            "required": ["event_id"],
        },
    ),
    # ── Tasks ────────────────────────────────────────────────────────
    ToolDefinition(
        name="list_tasks",
        description=(
            "List tasks with a due date within a time range. "
            "Use ISO 8601 strings for start and end."
        ),
        parameters={
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "description": "Start of the due-date range in ISO 8601 format."
                },
                "end": {
                    "type": "string",
                    "description": "End of the due-date range in ISO 8601 format."
                },
            },
            "required": ["start", "end"],
        },
    ),
    ToolDefinition(
        name="create_task",
        description="Create a new task with a title, due date, and optional description.",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title."
                },
                "due": {
                    "type": "string",
                    "description": "Due date/time in ISO 8601 format."
                },
                "description": {
                    "type": "string",
                    "description": "Optional task notes."
                },
            },
            "required": ["title", "due"],
        },
    ),
    ToolDefinition(
        name="get_task",
        description="Get a single task by its ID.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The task ID."},
            },
            "required": ["task_id"],
        },
    ),
    ToolDefinition(
        name="update_task",
        description="Update a task's title, due date, description, or completion status.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The task ID to update."
                },
                "title": {
                    "type": "string",
                    "description": "New task title."
                },
                "due": {
                    "type": "string",
                    "description": "New due date/time in ISO 8601 format."
                },
                "description": {
                    "type": "string",
                    "description": "New task notes."
                },
                "is_completed": {
                    "type": "boolean",
                    "description": "Whether the task is completed."
                },
            },
            "required": ["task_id"],
        },
    ),
    ToolDefinition(
        name="delete_task",
        description="Delete a task by its ID.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The task ID to delete."},
            },
            "required": ["task_id"],
        },
    ),
    ToolDefinition(
        name="mark_task_completed",
        description="Mark a task as completed by its ID.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The task ID to mark as completed."},
            },
            "required": ["task_id"],
        },
    ),
]

# ---------------------------------------------------------------------------
# Tool dispatcher — maps Gemini function-call output → GoogleCalendarClient
# ---------------------------------------------------------------------------


def _dispatch_event_tool(
    tool_name: str,
    args: dict[str, Any],
    client: CalendarClient,
) -> ToolResult | None:
    if tool_name == "list_events":
        list_args = _ListEventsArgs.model_validate(args)
        start = list_args.start.astimezone(UTC)
        end   = list_args.end.astimezone(UTC)
        payload = [
            {"id": e.id, "title": e.title, "start": e.start_time.isoformat(),
             "end": e.end_time.isoformat(), "description": e.description}
            for e in client.list_events(start, end)
        ]
        return ToolResult(tool_name=tool_name, content=json.dumps(payload))

    if tool_name == "create_event":
        create_args = _CreateEventArgs.model_validate(args)
        event = client.create_event(
            title=create_args.title,
            start=create_args.start.astimezone(UTC),
            end=create_args.end.astimezone(UTC),
            location=create_args.location,
            description=create_args.description,
        )
        return ToolResult(tool_name=tool_name, content=json.dumps(
            {"id": event.id, "title": event.title, "location": event.location,
             "start": event.start_time.isoformat(), "end": event.end_time.isoformat()}
        ))

    if tool_name == "get_event":
        get_args = _GetEventArgs.model_validate(args)
        event = client.get_event(get_args.event_id)
        return ToolResult(tool_name=tool_name, content=json.dumps(
            {"id": event.id, "title": event.title, "start": event.start_time.isoformat(),
             "end": event.end_time.isoformat(), "description": event.description}
        ))

    if tool_name == "delete_event":
        del_args = _DeleteEventArgs.model_validate(args)
        client.delete_event(del_args.event_id)
        return ToolResult(tool_name=tool_name, content="Event deleted successfully.")

    return None  # not an event tool

_TASK_COMPLETION_TOOLS = {"delete_task", "mark_task_completed"}


def _dispatch_task_tool(
    tool_name: str,
    args: dict[str, Any],
    client: CalendarClient,
) -> ToolResult | None:
    if tool_name == "list_tasks":
        list_task_args = _ListTasksArgs.model_validate(args)
        start = list_task_args.start.astimezone(UTC)
        end   = list_task_args.end.astimezone(UTC)
        payload = [
            {
                "id": t.id,
                "title": t.title,
                "due": t.end_time.isoformat() if t.end_time else None,
                "description": t.description,
                "is_completed": t.is_completed
            }
            for t in client.get_tasks(start, end)
        ]
        return ToolResult(tool_name=tool_name, content=json.dumps(payload))

    if tool_name == "create_task":
        create_task_args = _CreateTaskArgs.model_validate(args)
        due = create_task_args.due.astimezone(UTC) if create_task_args.due else None
        created = client.create_task(
            title=create_task_args.title, due=due, description=create_task_args.description)
        return ToolResult(tool_name=tool_name, content=json.dumps({
            "id": created.id,
            "title": created.title,
            "due": created.end_time.isoformat() if created.end_time else None
        }))

    if tool_name == "get_task":
        get_task_args = _GetTaskArgs.model_validate(args)
        task = client.get_task(get_task_args.task_id)
        return ToolResult(tool_name=tool_name, content=json.dumps({
            "id": task.id,
            "title": task.title,
            "due": task.end_time.isoformat() if task.end_time else None,
            "description": task.description,
            "is_completed": task.is_completed
        }))

    if tool_name == "update_task":
        upd_task_args = _UpdateTaskArgs.model_validate(args)
        existing = client.get_task(upd_task_args.task_id)
        due = upd_task_args.due.astimezone(UTC) if upd_task_args.due is not None else existing.end_time # noqa: E501
        is_completed = (
            upd_task_args.is_completed
            if upd_task_args.is_completed is not None
            else existing.is_completed
        )
        updated = client.update_task(
            task_id=upd_task_args.task_id,
            title=upd_task_args.title if upd_task_args.title is not None else existing.title,
            due=due,
            is_completed=is_completed,
            description=(
                upd_task_args.description
                if upd_task_args.description is not None
                else (existing.description or "")
            ),
        )
        return ToolResult(tool_name=tool_name, content=json.dumps({
            "id": updated.id,
            "title": updated.title,
            "due": updated.end_time.isoformat() if updated.end_time else None
        }))

    if tool_name in _TASK_COMPLETION_TOOLS:
        if tool_name == "delete_task":
            a_del = _DeleteTaskArgs.model_validate(args)
            client.delete_task(a_del.task_id)
            msg = "Task deleted successfully."
        else:
            a_mc = _MarkTaskCompletedArgs.model_validate(args)
            client.mark_task_completed(a_mc.task_id)
            msg = "Task marked as completed."
        return ToolResult(tool_name=tool_name, content=msg)

    return None  # not a task tool


def dispatch_tool_call(
    tool_name: str,
    args: dict[str, Any],
    client: CalendarClient,
) -> ToolResult:
    """
    Execute a Gemini-requested tool call against the calendar client.

    Args:
        tool_name: Name of the tool Gemini wants to call.
        args: Arguments the model supplied (already parsed from proto).
        client: Calendar client instance conforming to :class:`calendar_client_api.Client`.

    Returns:
        A :class:`ToolResult` with the serialised response or error message.
        On error, ``content`` is a JSON string with ``error_category`` and
        ``detail`` keys so callers and telemetry can distinguish failure modes.

    """
    try:
        result = _dispatch_event_tool(tool_name, args, client)
        if result is None:
            result = _dispatch_task_tool(tool_name, args, client)

    except (EventNotFoundError, TaskNotFoundError) as exc:
        logger.warning("Tool call %s — resource not found: %s", tool_name, exc)
        return ToolResult(
            tool_name=tool_name,
            content=json.dumps({"error_category": "not_found", "detail": str(exc)}),
            is_error=True,
        )

    except CalendarOperationError as exc:
        logger.exception("Tool call %s — calendar operation error", tool_name)
        return ToolResult(
            tool_name=tool_name,
            content=json.dumps({"error_category": "api_error", "detail": str(exc)}),
            is_error=True,
        )

    except (KeyError, ValueError, ValidationError) as exc:
        logger.warning("Tool call %s — invalid arguments: %s", tool_name, exc)
        return ToolResult(
            tool_name=tool_name,
            content=json.dumps({"error_category": "invalid_argument", "detail": str(exc)}),
            is_error=True,
        )

    else:
        if result is None:
            return ToolResult(
                tool_name=tool_name,
                content=json.dumps({
                    "error_category": "unknown_tool",
                    "detail": f"Unknown tool: {tool_name}",
                }),
                is_error=True,
            )
        return result
