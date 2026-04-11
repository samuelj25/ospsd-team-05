"""
Google Calendar event parser — converts raw Google API dicts to Event dataclasses.

Previously this module contained ``GoogleCalendarEvent(Event)``, a concrete
subclass of the (now deprecated) ``calendar_client_api.event.Event`` ABC.

Now that ``ospsd_calendar_api.models.Event`` is a concrete ``@dataclass``, no
subclassing is needed.  This module exposes a single factory function,
:func:`google_dict_to_event`, which parses a raw Google Calendar API response
dict and returns a fully populated ``Event`` instance.
"""

import json
from datetime import UTC, datetime, time
from typing import Any

from ospsd_calendar_api.models import Event

_KEY_ID = "id"
_KEY_SUMMARY = "summary"
_KEY_START = "start"
_KEY_END = "end"
_KEY_LOCATION = "location"
_KEY_DESCRIPTION = "description"
_KEY_DATETIME = "dateTime"
_KEY_DATE = "date"
_EMPTY_TITLE = "(No Title)"


def _parse_datetime(data: dict[str, Any]) -> datetime:
    """
    Parse a Google Calendar start/end time block into a timezone-aware datetime.

    Google represents datetimes either as ``{"dateTime": "<ISO 8601>"}`` for
    timed events, or as ``{"date": "<YYYY-MM-DD>"}`` for all-day events.
    All-day events are normalised to midnight UTC.

    Args:
        data: The ``start`` or ``end`` sub-dict from the Google API response.

    Raises:
        ValueError: If neither ``dateTime`` nor ``date`` key is present.

    """
    if _KEY_DATETIME in data:
        return datetime.fromisoformat(str(data[_KEY_DATETIME]))
    if _KEY_DATE in data:
        d = datetime.fromisoformat(str(data[_KEY_DATE]))
        return datetime.combine(d, time.min, tzinfo=UTC)
    msg = "Event time data must contain either 'dateTime' or 'date' field."
    raise ValueError(msg)


def _parse_raw_data(raw_data: str | dict[str, Any]) -> dict[str, Any]:
    """
    Coerce raw API output (JSON string or dict) to a dict.

    Args:
        raw_data: Either the raw JSON string from the API or an already-parsed
                  dictionary.

    Raises:
        ValueError: If the string cannot be parsed as JSON.
        TypeError:  If the parsed result is not a dictionary.

    """
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


def google_dict_to_event(raw_data: str | dict[str, Any]) -> Event:
    """
    Parse a Google Calendar API event response into an ``Event`` dataclass.

    Translates Google's nested dict structure (``summary``, ``start.dateTime``,
    etc.) into the flat, provider-agnostic ``Event`` fields defined by
    ``ospsd_calendar_api.models.Event``.

    Args:
        raw_data: Raw event payload — either the full JSON string returned by
                  the Google API, or the already-deserialized Python dict.

    Returns:
        A fully populated :class:`ospsd_calendar_api.models.Event` instance.

    Raises:
        TypeError:  If ``id`` or the ``start``/``end`` blocks are missing or
                    the wrong type.
        ValueError: If the datetime strings cannot be parsed, or the JSON
                    string is malformed.

    """
    parsed = _parse_raw_data(raw_data)

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

    return Event(
        id=event_id,
        title=parsed.get(_KEY_SUMMARY, _EMPTY_TITLE),
        start_time=_parse_datetime(start),
        end_time=_parse_datetime(end),
        location=parsed.get(_KEY_LOCATION),
        description=parsed.get(_KEY_DESCRIPTION),
    )
