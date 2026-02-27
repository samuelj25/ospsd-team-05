"""Google Calendar Task Implementation."""

from datetime import datetime

import calendar_client_api

_MISSING_ID_MSG = "Task must have an ID"
_MISSING_DATE_MSG = "Task is missing date field"
_INVALID_DUE_MSG = "Invalid format for due date"


class GoogleCalendarTask(calendar_client_api.Task):
    """Implementation of Task using Google Tasks API data."""

    def __init__(self, raw_data: dict[str, str | dict[str, str]]) -> None:
        """
        Initialize from raw Google API JSON dictionary.

        Args:
            raw_data: The dictionary representation of a Google Task.

        """
        self._data = raw_data

    @property
    def id(self) -> str:
        """Unique identifier for the task."""
        task_id = self._data.get("id")
        if not task_id:
            raise ValueError(_MISSING_ID_MSG)
        return str(task_id)

    @property
    def title(self) -> str:
        """Return title of the task."""
        return str(self._data.get("title", "Untitled Task"))

    def _parse_datetime(self, date_str: str | None) -> datetime:
        """Parse Google Task's custom RFC 3339 datetime string."""
        if not date_str:
            raise ValueError(_MISSING_DATE_MSG)
        return datetime.fromisoformat(date_str)

    @property
    def start_time(self) -> datetime:
        """Return time of the task (using due date for Google Tasks)."""
        due_data = self._data.get("due")
        if not isinstance(due_data, str):
            raise TypeError(_INVALID_DUE_MSG)
        return self._parse_datetime(due_data)

    @property
    def end_time(self) -> datetime:
        """Return end time of the task (same as start time for tasks)."""
        return self.start_time

    @property
    def description(self) -> str | None:
        """Return description of the task."""
        return str(self._data.get("notes")) if "notes" in self._data else None

    @property
    def is_completed(self) -> bool:
        """Return whether the task is completed."""
        return self._data.get("status") == "completed"
