"""Calendar tool definitions and dispatcher for Gemini tool calling."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ai_client_api.models import ToolDefinition, ToolResult

if TYPE_CHECKING:
    from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient

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
]

# ---------------------------------------------------------------------------
# Tool dispatcher — maps Gemini function-call output → GoogleCalendarClient
# ---------------------------------------------------------------------------


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
        if tool_name == "list_events":
            start = datetime.fromisoformat(args["start"]).astimezone(UTC)
            end = datetime.fromisoformat(args["end"]).astimezone(UTC)
            events = client.list_events(start, end)
            payload = [
                {
                    "id": e.id,
                    "title": e.title,
                    "start": e.start_time.isoformat(),
                    "end": e.end_time.isoformat(),
                    "description": e.description,
                }
                for e in events
            ]
            return ToolResult(tool_name=tool_name, content=json.dumps(payload))

        if tool_name == "create_event":
            start = datetime.fromisoformat(args["start"]).astimezone(UTC)
            end = datetime.fromisoformat(args["end"]).astimezone(UTC)
            event = client.create_event(
                title=args["title"],
                start=start,
                end=end,
                description=args.get("description", ""),
            )
            return ToolResult(
                tool_name=tool_name,
                content=json.dumps(
                    {
                        "id": event.id,
                        "title": event.title,
                        "start": event.start_time.isoformat(),
                        "end": event.end_time.isoformat(),
                    }
                ),
            )

        if tool_name == "get_event":
            event = client.get_event(args["event_id"])
            return ToolResult(
                tool_name=tool_name,
                content=json.dumps(
                    {
                        "id": event.id,
                        "title": event.title,
                        "start": event.start_time.isoformat(),
                        "end": event.end_time.isoformat(),
                        "description": event.description,
                    }
                ),
            )

        if tool_name == "delete_event":
            client.delete_event(args["event_id"])
            return ToolResult(tool_name=tool_name, content="Event deleted successfully.")

        return ToolResult(
            tool_name=tool_name,
            content=f"Unknown tool: {tool_name}",
            is_error=True,
        )

    except Exception as exc:
        logger.exception("Tool call %s failed", tool_name)
        return ToolResult(tool_name=tool_name, content=str(exc), is_error=True)
