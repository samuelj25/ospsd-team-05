"""Google Calendar Event Implementation."""

from datetime import datetime

import calendar_client_api

_MISSING_ID_MSG = "Event must have an ID"
_MISSING_DATETIME_MSG = "Event is missing dateTime field"
_INVALID_START_MSG = "Invalid format for start time"
_INVALID_END_MSG = "Invalid format for end time"


class GoogleCalendarEvent(calendar_client_api.Event):
    """Implementation of Event using Google Calendar API data."""

    def __init__(self, raw_data: dict[str, str | dict[str, str]]) -> None:
        """
        Initialize from raw Google API JSON dictionary.

        Args:
            raw_data: The dictionary representation of a Google Calendar event.

        """
        self._data = raw_data

    @property
    def id(self) -> str:
        """Unique identifier for the event."""
        event_id = self._data.get("id")
        if not event_id:
            raise ValueError(_MISSING_ID_MSG)
        return str(event_id)

    @property
    def title(self) -> str:
        """Return title of the event."""
        return str(self._data.get("summary", "Untitled Event"))

    def _parse_datetime(self, time_dict: dict[str, str] | None) -> datetime:
        """Parse Google Calendar's custom datetime dict."""
        if not time_dict or "dateTime" not in time_dict:
            raise ValueError(_MISSING_DATETIME_MSG)
        return datetime.fromisoformat(time_dict["dateTime"])

    @property
    def start_time(self) -> datetime:
        """Return start time of the event."""
        start_data = self._data.get("start")
        if not isinstance(start_data, dict):
            raise TypeError(_INVALID_START_MSG)
        return self._parse_datetime(start_data)

    @property
    def end_time(self) -> datetime:
        """Return end time of the event."""
        end_data = self._data.get("end")
        if not isinstance(end_data, dict):
            raise TypeError(_INVALID_END_MSG)
        return self._parse_datetime(end_data)

    @property
    def location(self) -> str | None:
        """Return location of the event."""
        return str(self._data.get("location")) if "location" in self._data else None

    @property
    def description(self) -> str | None:
        """Return description of the event."""
        return str(self._data.get("description")) if "description" in self._data else None
