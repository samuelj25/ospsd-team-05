"""End-To-End tests for compiling Event operations together into a full lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from google_calendar_client_impl.event_impl import GoogleCalendarEvent
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient
from googleapiclient.errors import HttpError


@pytest.mark.e2e
def test_event_lifecycle(live_client: GoogleCalendarClient) -> None:
    """Create an event, verify it exists, update it, verify the modification, and delete it."""
    now = datetime.now(tz=UTC)
    start = (now + timedelta(hours=1)).replace(microsecond=0)
    end = (start + timedelta(hours=1)).replace(microsecond=0)

    event_data: dict[str, str | dict[str, str]] = {
        "id": "dummy",
        "summary": "E2E Lifecycle Event Original",
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
    }

    # 1. Create Event
    created = live_client.create_event(GoogleCalendarEvent(event_data))
    assert created.id is not None
    assert created.title == "E2E Lifecycle Event Original"

    try:
        # 2. Verify it exists via Get
        fetched = live_client.get_event(created.id)
        assert fetched.title == "E2E Lifecycle Event Original"

        # 3. Update it
        update_data: dict[str, str | dict[str, str]] = {
            "id": created.id,
            "summary": "E2E Lifecycle Event Updated",
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }
        updated = live_client.update_event(GoogleCalendarEvent(update_data))
        assert updated.title == "E2E Lifecycle Event Updated"

        # 4. Verify modification via Get
        refetched = live_client.get_event(created.id)
        assert refetched.title == "E2E Lifecycle Event Updated"

    finally:
        # 5. Delete it
        live_client.delete_event(created.id)

        # Verify it is deleted (404 or cancelled)
        error_caught = None
        try:
            live_client.get_event(created.id)
        except HttpError as exc_info:
            error_caught = exc_info

        if error_caught:
            assert getattr(error_caught, "status_code", 404) in (404, 400, 410)
        else:
            raw_ev = (
                live_client._require_calendar_service()
                .events()
                .get(  # Needed to assert raw Google backend soft-deleted status
                    calendarId=live_client.calendar_id, eventId=created.id
                )
                .execute()
            )
            assert raw_ev.get("status") == "cancelled"


@pytest.mark.e2e
def test_list_events_lifecycle(live_client: GoogleCalendarClient) -> None:
    """Create a couple events, verify they show up in get_events() with date ranges."""
    now = datetime.now(tz=UTC)
    start1 = (now + timedelta(hours=1)).replace(microsecond=0)
    end1 = (start1 + timedelta(hours=1)).replace(microsecond=0)

    start2 = (now + timedelta(hours=3)).replace(microsecond=0)
    end2 = (start2 + timedelta(hours=1)).replace(microsecond=0)

    event_data_1: dict[str, str | dict[str, str]] = {
        "id": "dummy",
        "summary": "E2E List Event 1",
        "start": {"dateTime": start1.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end1.isoformat(), "timeZone": "UTC"},
    }

    event_data_2: dict[str, str | dict[str, str]] = {
        "id": "dummy",
        "summary": "E2E List Event 2",
        "start": {"dateTime": start2.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end2.isoformat(), "timeZone": "UTC"},
    }

    ids_to_clean = []

    try:
        ev1 = live_client.create_event(GoogleCalendarEvent(event_data_1))
        ids_to_clean.append(ev1.id)

        ev2 = live_client.create_event(GoogleCalendarEvent(event_data_2))
        ids_to_clean.append(ev2.id)

        # Fetch events in range
        events_list = list(live_client.get_events(now, now + timedelta(days=1)))

        # Verify our created events are natively returned in the list
        found_ids = [e.id for e in events_list]
        assert ev1.id in found_ids
        assert ev2.id in found_ids

    finally:
        for ev_id in ids_to_clean:
            live_client.delete_event(ev_id)
