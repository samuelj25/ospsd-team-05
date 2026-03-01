"""Unit tests for the GoogleCalendarTask implementation."""

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from calendar_client_api import task

from google_calendar_client_impl import task_impl


def _make_raw(  # noqa: PLR0913
    task_id: str = "task-123",
    title: str = "Buy groceries",
    due: str = "2026-03-01T17:00:00+00:00",
    updated: str = "2026-03-01T10:00:00+00:00",
    status: str = "needsAction",
    notes: str | None = "Milk, eggs, bread",
) -> dict[str, Any]:
    """Build a raw Google Tasks API task dict."""
    raw: dict[str, Any] = {
        "id": task_id,
        "title": title,
        "due": due,
        "updated": updated,
        "status": status,
    }
    if notes is not None:
        raw["notes"] = notes
    return raw


class TestProperties:
    """Verify all Task properties are parsed and returned correctly."""

    def test_id(self) -> None:
        """Verify task ID is correctly parsed and returned."""
        t = task_impl.GoogleCalendarTask(_make_raw())
        assert t.id == "task-123"

    def test_title(self) -> None:
        """Verify title is correctly parsed and returned."""
        t = task_impl.GoogleCalendarTask(_make_raw())
        assert t.title == "Buy groceries"

    def test_start_time_uses_updated(self) -> None:
        """Verify start time uses the 'updated' field when present."""
        t = task_impl.GoogleCalendarTask(_make_raw())
        assert t.start_time == datetime(2026, 3, 1, 10, 0, tzinfo=UTC)

    def test_end_time_uses_due(self) -> None:
        """Verify end time uses the 'due' field."""
        t = task_impl.GoogleCalendarTask(_make_raw())
        assert t.end_time == datetime(2026, 3, 1, 17, 0, tzinfo=UTC)

    def test_description(self) -> None:
        """Verify description is parsed from the 'notes' field."""
        t = task_impl.GoogleCalendarTask(_make_raw())
        assert t.description == "Milk, eggs, bread"

    def test_is_completed_false(self) -> None:
        """Verify task with 'needsAction' status is not completed."""
        t = task_impl.GoogleCalendarTask(_make_raw())
        assert t.is_completed is False

    def test_is_completed_true(self) -> None:
        """Verify task with 'completed' status is completed."""
        t = task_impl.GoogleCalendarTask(_make_raw(status="completed"))
        assert t.is_completed is True


class TestDefaults:
    """Verify optional fields and fallback behavior."""

    def test_description_defaults_to_none(self) -> None:
        """Verify description is None when 'notes' is not provided."""
        t = task_impl.GoogleCalendarTask(_make_raw(notes=None))
        assert t.description is None

    def test_status_defaults_to_needs_action(self) -> None:
        """Verify missing status defaults to needsAction (not completed)."""
        raw = _make_raw()
        del raw["status"]
        t = task_impl.GoogleCalendarTask(raw)
        assert t.is_completed is False

    def test_start_time_falls_back_to_due_when_no_updated(self) -> None:
        """Verify start time falls back to 'due' when 'updated' is missing."""
        raw = _make_raw()
        del raw["updated"]
        t = task_impl.GoogleCalendarTask(raw)
        assert t.start_time == datetime(2026, 3, 1, 17, 0, tzinfo=UTC)


class TestJsonStringInput:
    """Verify the constructor also accepts a raw JSON string."""

    def test_from_json_string(self) -> None:
        """Verify basic properties are correctly parsed from a JSON string."""
        raw = _make_raw()
        t = task_impl.GoogleCalendarTask(json.dumps(raw))
        assert t.id == "task-123"
        assert t.title == "Buy groceries"

    def test_from_json_string_preserves_all_fields(self) -> None:
        """Verify all fields are correctly parsed from a JSON string."""
        raw = _make_raw()
        t = task_impl.GoogleCalendarTask(json.dumps(raw))
        assert t.description == "Milk, eggs, bread"
        assert t.is_completed is False


class TestValidation:
    """Verify appropriate errors for malformed input."""

    def test_missing_id_raises(self) -> None:
        """Verify error if 'id' field is missing from task data."""
        raw = _make_raw()
        del raw["id"]
        with pytest.raises(ValueError, match=r"'id'"):
            task_impl.GoogleCalendarTask(raw)

    def test_missing_title_raises(self) -> None:
        """Verify error if 'title' field is missing from task data."""
        raw = _make_raw()
        del raw["title"]
        with pytest.raises(TypeError, match=r"'title'"):
            task_impl.GoogleCalendarTask(raw)

    def test_missing_due_raises(self) -> None:
        """Verify error if 'due' field is missing from task data."""
        raw = _make_raw()
        del raw["due"]
        with pytest.raises(TypeError, match=r"'due'"):
            task_impl.GoogleCalendarTask(raw)

    def test_invalid_json_string_raises(self) -> None:
        """Verify error if constructor is given a string that isn't valid JSON."""
        with pytest.raises(ValueError, match=r"(?i)json"):
            task_impl.GoogleCalendarTask("not valid json {{{")

    def test_invalid_datetime_format_raises(self) -> None:
        """Verify error if 'due' contains an unparseable datetime string."""
        raw = _make_raw(due="not-a-date")
        with pytest.raises(ValueError, match=r"(?i)datetime"):
            task_impl.GoogleCalendarTask(raw)


class TestAbstractContract:
    """Verify GoogleCalendarTask satisfies the Task ABC."""

    def test_isinstance_of_task(self) -> None:
        """GoogleCalendarTask should be recognized as a Task instance."""
        t = task_impl.GoogleCalendarTask(_make_raw())
        assert isinstance(t, task.Task)
