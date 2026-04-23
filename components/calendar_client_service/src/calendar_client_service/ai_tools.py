"""Calendar tool definitions and dispatcher for Gemini tool calling."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ai_client_api.models import ToolDefinition, ToolResult

if TYPE_CHECKING:
    from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient

from google_calendar_client_impl.task_impl import GoogleCalendarTask

logger = logging.getLogger(__name__)

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
    client: GoogleCalendarClient,
) -> ToolResult | None:
    if tool_name == "list_events":
        start = datetime.fromisoformat(args["start"]).astimezone(UTC)
        end   = datetime.fromisoformat(args["end"]).astimezone(UTC)
        payload = [
            {"id": e.id, "title": e.title, "start": e.start_time.isoformat(),
             "end": e.end_time.isoformat(), "description": e.description}
            for e in client.list_events(start, end)
        ]
        return ToolResult(tool_name=tool_name, content=json.dumps(payload))

    if tool_name == "create_event":
        start = datetime.fromisoformat(args["start"]).astimezone(UTC)
        end   = datetime.fromisoformat(args["end"]).astimezone(UTC)
        event = client.create_event(
            title=args["title"], start=start, end=end,
            description=args.get("description", ""),
        )
        return ToolResult(tool_name=tool_name, content=json.dumps(
            {"id": event.id, "title": event.title,
             "start": event.start_time.isoformat(), "end": event.end_time.isoformat()}
        ))

    if tool_name == "get_event":
        event = client.get_event(args["event_id"])
        return ToolResult(tool_name=tool_name, content=json.dumps(
            {"id": event.id, "title": event.title, "start": event.start_time.isoformat(),
             "end": event.end_time.isoformat(), "description": event.description}
        ))

    if tool_name == "delete_event":
        client.delete_event(args["event_id"])
        return ToolResult(tool_name=tool_name, content="Event deleted successfully.")

    return None  # not an event tool

_TASK_COMPLETION_TOOLS = {"delete_task", "mark_task_completed"}
def _dispatch_task_tool(
    tool_name: str,
    args: dict[str, Any],
    client: GoogleCalendarClient,
) -> ToolResult | None:
    if tool_name == "list_tasks":
        start = datetime.fromisoformat(args["start"]).astimezone(UTC)
        end   = datetime.fromisoformat(args["end"]).astimezone(UTC)
        payload = [
            {"id": t.id, "title": t.title, "due": t.end_time.isoformat(),
             "description": t.description, "is_completed": t.is_completed}
            for t in client.get_tasks(start, end)
        ]
        return ToolResult(tool_name=tool_name, content=json.dumps(payload))

    if tool_name == "create_task":
        due = datetime.fromisoformat(args["due"]).astimezone(UTC)
        raw = {
            "title": args["title"],
            "due": due.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "status": "needsAction",
            "notes": args.get("description", ""),
        }
        created = client.create_task(GoogleCalendarTask(raw))
        return ToolResult(tool_name=tool_name, content=json.dumps(
            {"id": created.id, "title": created.title, "due": created.end_time.isoformat()}
        ))

    if tool_name == "get_task":
        task = client.get_task(args["task_id"])
        return ToolResult(tool_name=tool_name, content=json.dumps(
            {"id": task.id, "title": task.title, "due": task.end_time.isoformat(),
             "description": task.description, "is_completed": task.is_completed}
        ))

    if tool_name == "update_task":
        existing = client.get_task(args["task_id"])
        due = (
            datetime.fromisoformat(args["due"]).astimezone(UTC)
            if "due" in args
            else existing.end_time
        )
        is_completed = args.get("is_completed", existing.is_completed)
        raw = {
            "id": args["task_id"],
            "title": args.get("title", existing.title),
            "due": due.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "status": "completed" if is_completed else "needsAction",
            "notes": args.get("description", existing.description or ""),
        }
        updated = client.update_task(GoogleCalendarTask(raw))
        return ToolResult(tool_name=tool_name, content=json.dumps(
            {"id": updated.id, "title": updated.title, "due": updated.end_time.isoformat()}
        ))

    if tool_name in _TASK_COMPLETION_TOOLS:
        if tool_name == "delete_task":
            client.delete_task(args["task_id"])
            msg = "Task deleted successfully."
        else:
            client.mark_task_completed(args["task_id"])
            msg = "Task marked as completed."
        return ToolResult(tool_name=tool_name, content=msg)

    return None  # not a task tool


def dispatch_tool_call(
    tool_name: str,
    args: dict[str, Any],
    client: GoogleCalendarClient,
) -> ToolResult:
    """
    Execute a Gemini-requested tool call against the calendar client.

    Args:
        tool_name: Name of the tool Gemini wants to call.
        args: Arguments the model supplied (already parsed from proto).
        client: Authenticated :class:`GoogleCalendarClient` to act on.

    Returns:
        A :class:`ToolResult` with the serialised response or error message.

    """
    try:
        result = _dispatch_event_tool(tool_name, args, client)
        if result is None:
            result = _dispatch_task_tool(tool_name, args, client)
    except Exception as exc:
        logger.exception("Tool call %s failed", tool_name)
        return ToolResult(tool_name=tool_name, content=str(exc), is_error=True)
    else:
        if result is None:
            return ToolResult(
                tool_name=tool_name,
                content=f"Unknown tool: {tool_name}",
                is_error=True,
            )
        return result
