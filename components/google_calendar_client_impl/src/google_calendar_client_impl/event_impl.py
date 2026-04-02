"""Google Calendar Event Implementation colocated with the Google Calendar client."""

import json
from datetime import UTC, datetime, time
from typing import Any

from calendar_client_api import event

_KEY_ID = "id"
_KEY_SUMMARY = "summary"
_KEY_START = "start"
_KEY_END = "end"
_KEY_LOCATION = "location"
_KEY_DESCRIPTION = "description"
_KEY_DATETIME = "dateTime"
_KEY_DATE = "date"
_EMPTY_TITLE = "(No Title)"


class GoogleCalendarEvent(event.Event):
    """Concrete implementation of the Event abstraction for Google Calendar events."""

    def __init__(self, raw_data: str | dict[str, str | dict[str, str]]) -> None:
        """Initialize the event by parsing raw JSON data from the Google Calendar API."""
        parsed = self._parse_raw_data(raw_data)

        event_id = parsed.get(_KEY_ID)
        if not event_id or not isinstance(event_id, str):
            msg = "Event data must contain a valid 'id' field of type string."
            raise TypeError(msg)

        start = parsed.get(_KEY_START)
        if not isinstance(start, dict):
            msg = "Event data must contain a valid 'start' field of type dictionary."
            raise TypeError(msg)

        end = parsed.get(_KEY_END)
        if not isinstance(end, dict):
            msg = "Event data must contain a valid 'end' field of type dictionary."
            raise TypeError(msg)

        self._id: str = event_id
        self._title: str = parsed.get(_KEY_SUMMARY, _EMPTY_TITLE)
        self._start_time: datetime = self._parse_datetime(start)
        self._end_time: datetime = self._parse_datetime(end)
        self._location: str | None = parsed.get(_KEY_LOCATION)
        self._description: str | None = parsed.get(_KEY_DESCRIPTION)

    def _parse_raw_data(self, raw_data: str | dict[str, Any]) -> dict[str, Any]:
        """Parse raw JSON data into a structured dictionary."""
        if isinstance(raw_data, dict):
            return raw_data
        try:
            result = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError) as e:
            msg = f"Failed to parse event data as JSON: {e}"
            raise ValueError(msg) from e
        if not isinstance(result, dict):
            msg = "Parsed JSON data must be a dictionary representing the event."
            raise TypeError(msg)
        return result

    def _parse_datetime(self, data: dict[str, Any]) -> datetime:
        """Parse a Google Calendar start/end time from the event data."""
        if _KEY_DATETIME in data:
            return datetime.fromisoformat(str(data[_KEY_DATETIME]))
        if _KEY_DATE in data:
            d = datetime.fromisoformat(str(data[_KEY_DATE]))
            return datetime.combine(d, time.min, tzinfo=UTC)
        msg = "Event time data must contain either 'dateTime' or 'date' field."
        raise ValueError(msg)

    @property
    def id(self) -> str:
        """Get the unique identifier for the event."""
        return self._id

    @property
    def title(self) -> str:
        """Get the title of the event."""
        return self._title

    @property
    def start_time(self) -> datetime:
        """Get the start time of the event."""
        return self._start_time

    @property
    def end_time(self) -> datetime:
        """Get the end time of the event."""
        return self._end_time

    @property
    def location(self) -> str | None:
        """Get the location of the event."""
        return self._location

    @property
    def description(self) -> str | None:
        """Get the description of the event."""
        return self._description
