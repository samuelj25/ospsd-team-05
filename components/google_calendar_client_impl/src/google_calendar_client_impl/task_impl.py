"""Google Calendar Task Implementation colocated with the Google Calendar client."""

import json
from datetime import datetime
from typing import Any

from calendar_client_api import task


class GoogleCalendarTask(task.Task):
    """Concrete implementation of the Task abstraction for Google Calendar tasks."""

    def __init__(self, raw_data: str | dict[str, Any]) -> None:
        """Initialize a GoogleCalendarTask instance."""
        parsed = self._parse_raw_data(raw_data)

        task_id_error = "Task data must contain a valid 'id' field."
        task_id = parsed.get("id")
        if not task_id or not isinstance(task_id, str):
            raise ValueError(task_id_error)

        title_error = "Task data must contain a valid 'title' field."
        title = parsed.get("title")
        if not isinstance(title, str):
            raise TypeError(title_error)

        self._id: str = task_id
        self._title: str = title
        self._description: str | None = parsed.get("notes")

        due = parsed.get("due")
        start_time = parsed.get("updated", due)

        self._start_time: datetime | None = self._parse_datetime(start_time) if start_time else None
        self._end_time: datetime | None = self._parse_datetime(due) if due else None

        status = parsed.get("status", "needsAction")
        self._is_completed: bool = status == "completed"

    def _parse_raw_data(self, raw_data: str | dict[str, Any]) -> dict[str, Any]:
        """Parse raw JSON data into a structured dictionary."""
        if isinstance(raw_data, dict):
            return raw_data
        try:
            result = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError) as e:
            error_message = "Invalid JSON data"
            raise ValueError(error_message) from e
        if not isinstance(result, dict):
            error_message = "Parsed JSON data is not a dictionary."
            raise TypeError(error_message)
        return result

    def _parse_datetime(self, value: str) -> datetime:
        """Parse ISO 8601 datetime string into datetime object."""
        try:
            return datetime.fromisoformat(value)
        except ValueError as e:
            error_message = "Invalid datetime format"
            raise ValueError(error_message) from e

    @property
    def id(self) -> str:
        """Get the task ID."""
        return self._id

    @property
    def title(self) -> str:
        """Get the task title."""
        return self._title

    @property
    def start_time(self) -> datetime | None:
        """Get the task start time."""
        return self._start_time

    @property
    def end_time(self) -> datetime | None:
        """Get the task end time."""
        return self._end_time

    @property
    def description(self) -> str | None:
        """Get the task description."""
        return self._description

    @property
    def is_completed(self) -> bool:
        """Check if the task is completed."""
        return self._is_completed
