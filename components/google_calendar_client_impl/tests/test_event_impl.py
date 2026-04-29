"""Unit tests for the GoogleCalendarEvent implementation."""

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from google_calendar_client_impl import event_impl


def _make_raw(  # noqa: PLR0913
    event_id: str = "evt-123",
    summary: str = "Test Event",
    start_dt: str = "2026-03-01T09:00:00+00:00",
    end_dt: str = "2026-03-01T09:30:00+00:00",
    location: str | None = "Zoom",
    description: str | None = "Daily sync",
    *,
    all_day: bool = False,
) -> dict[str, Any]:
    """Build a raw Google Calendar API event dict."""
    raw: dict[str, Any] = {
        "id": event_id,
        "summary": summary,
    }
    if all_day:
        raw["start"] = {"date": start_dt}
        raw["end"] = {"date": end_dt}
    else:
        raw["start"] = {"dateTime": start_dt}
        raw["end"] = {"dateTime": end_dt}
    if location is not None:
        raw["location"] = location
    if description is not None:
        raw["description"] = description
    return raw


class TestProperties:
    """Verify all Event properties are parsed and returned correctly."""

    def test_id(self) -> None:
        """Verify event ID is correctly parsed and returned."""
        evt = event_impl.google_dict_to_event(_make_raw())
        assert evt.id == "evt-123"

    def test_title(self) -> None:
        """Verify title is correctly parsed, with fallback if missing."""
        evt = event_impl.google_dict_to_event(_make_raw())
        assert evt.title == "Test Event"

    def test_start_time(self) -> None:
        """Verify start time is correctly parsed as a datetime with timezone."""
        evt = event_impl.google_dict_to_event(_make_raw())
        assert evt.start_time == datetime(2026, 3, 1, 9, 0, tzinfo=UTC)

    def test_end_time(self) -> None:
        """Verify end time is correctly parsed as a datetime with timezone."""
        evt = event_impl.google_dict_to_event(_make_raw())
        assert evt.end_time == datetime(2026, 3, 1, 9, 30, tzinfo=UTC)

    def test_location(self) -> None:
        """Verify location is correctly parsed."""
        evt = event_impl.google_dict_to_event(_make_raw())
        assert evt.location == "Zoom"

    def test_description(self) -> None:
        """Verify description is correctly parsed."""
        evt = event_impl.google_dict_to_event(_make_raw())
        assert evt.description == "Daily sync"


class TestDefaults:
    """Verify optional fields default to None and title falls back."""

    def test_location_defaults_to_none(self) -> None:
        """Verify location defaults to None if not provided."""
        raw = _make_raw(location=None, description=None)
        evt = event_impl.google_dict_to_event(raw)
        assert evt.location is None

    def test_description_defaults_to_none(self) -> None:
        """Verify description defaults to None if not provided."""
        raw = _make_raw(location=None, description=None)
        evt = event_impl.google_dict_to_event(raw)
        assert evt.description is None

    def test_missing_summary_gives_default_title(self) -> None:
        """Verify missing 'summary' field falls back to default title."""
        raw = _make_raw()
        del raw["summary"]
        evt = event_impl.google_dict_to_event(raw)
        assert evt.title == "(No Title)"

    def test_empty_summary_preserves_empty_string(self) -> None:
        """Verify empty string summary is preserved as-is."""
        raw = _make_raw(summary="")
        evt = event_impl.google_dict_to_event(raw)
        assert evt.title == ""


class TestJsonStringInput:
    """Verify the constructor also accepts a raw JSON string."""

    def test_from_json_string(self) -> None:
        """Verify basic properties are correctly parsed when input is a JSON string."""
        raw = _make_raw()
        evt = event_impl.google_dict_to_event(json.dumps(raw))
        assert evt.id == "evt-123"
        assert evt.title == "Test Event"

    def test_from_json_string_preserves_all_fields(self) -> None:
        """Verify all fields are correctly parsed when input is a JSON string."""
        raw = _make_raw()
        evt = event_impl.google_dict_to_event(json.dumps(raw))
        assert evt.location == "Zoom"
        assert evt.description == "Daily sync"


class TestAllDayEvents:
    """Verify all-day events (date-only, no dateTime) are parsed."""

    def test_all_day_start(self) -> None:
        """Verify all-day event start time is parsed as date with UTC timezone."""
        raw = _make_raw(
            start_dt="2026-03-01",
            end_dt="2026-03-02",
            all_day=True,
        )
        evt = event_impl.google_dict_to_event(raw)
        assert evt.start_time == datetime(2026, 3, 1, tzinfo=UTC)

    def test_all_day_end(self) -> None:
        """Verify all-day event end time is parsed as date with UTC timezone."""
        raw = _make_raw(
            start_dt="2026-03-01",
            end_dt="2026-03-02",
            all_day=True,
        )
        evt = event_impl.google_dict_to_event(raw)
        assert evt.end_time == datetime(2026, 3, 2, tzinfo=UTC)


class TestValidation:
    """Verify appropriate errors for malformed input."""

    def test_missing_id_raises(self) -> None:
        """Verify error if 'id' field is missing from event data."""
        raw = _make_raw()
        del raw["id"]
        with pytest.raises(TypeError, match="'id'"):
            event_impl.google_dict_to_event(raw)

    def test_missing_start_raises(self) -> None:
        """Verify error if 'start' block is missing from event data."""
        raw = _make_raw()
        del raw["start"]
        with pytest.raises(TypeError, match="'start'"):
            event_impl.google_dict_to_event(raw)

    def test_missing_end_raises(self) -> None:
        """Verify error if 'end' block is missing from event data."""
        raw = _make_raw()
        del raw["end"]
        with pytest.raises(TypeError, match="'end'"):
            event_impl.google_dict_to_event(raw)

    def test_invalid_json_string_raises(self) -> None:
        """Verify error if constructor is given a string that isn't valid JSON."""
        with pytest.raises(ValueError, match=r"(?i)json"):
            event_impl.google_dict_to_event("not valid json {{{")

    def test_start_block_missing_datetime_and_date_raises(self) -> None:
        """Verify error if 'start' block is missing both 'dateTime' and 'date'."""
        raw = _make_raw()
        raw["start"] = {"timeZone": "America/New_York"}
        with pytest.raises(ValueError, match=r"'dateTime'|'date'"):
            event_impl.google_dict_to_event(raw)
