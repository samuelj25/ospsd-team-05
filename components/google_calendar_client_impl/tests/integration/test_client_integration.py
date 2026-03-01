"""Integration tests for the GoogleCalendarClient over Live Google APIs."""

from datetime import UTC, datetime, timedelta

from googleapiclient.errors import HttpError

from google_calendar_client_impl.event_impl import GoogleCalendarEvent
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient
from google_calendar_client_impl.task_impl import GoogleCalendarTask


def test_get_event_parsed_abstraction(integration_live_client: GoogleCalendarClient) -> None:
    """
    Test that client.get_event() correctly returns a parsed Event abstraction.

    It returns a Google Event without mocking.
    """
    now = datetime.now(tz=UTC)
    start = (now + timedelta(hours=1)).replace(microsecond=0)
    end = (start + timedelta(hours=1)).replace(microsecond=0)

    event_data: dict[str, str | dict[str, str]] = {
        "id": "dummy",
        "summary": "Integration Get Event",
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"}
    }

    # Pre-requisite: create the event
    created = integration_live_client.create_event(GoogleCalendarEvent(event_data))

    try:
        # Test get_event verifies Event abstraction correctness.
        fetched = integration_live_client.get_event(created.id)

        # Verify it correctly returns a parsed Event abstraction
        assert isinstance(fetched, GoogleCalendarEvent)
        assert fetched.id == created.id
        assert fetched.title == "Integration Get Event"
        assert fetched.start_time == start
        assert fetched.end_time == end
    finally:
        integration_live_client.delete_event(created.id)


def test_create_event_properly_pushes_abstraction(
    integration_live_client: GoogleCalendarClient,
) -> None:
    """
    Test that client.create_event() properly pushes the Event abstraction.

    It pushes to the underlying Google API and can be retrieved.
    """
    now = datetime.now(tz=UTC)
    start = (now + timedelta(hours=2)).replace(microsecond=0)
    end = (start + timedelta(hours=2)).replace(microsecond=0)

    event_data: dict[str, str | dict[str, str]] = {
        "id": "dummy",
        "summary": "Integration Create Event",
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"}
    }

    event_to_create = GoogleCalendarEvent(event_data)
    created_id = None
    try:
        # Test create_event pushing abstraction to API
        created = integration_live_client.create_event(event_to_create)
        created_id = created.id
        assert created.id is not None
        assert created.title == "Integration Create Event"

        # Verify it can be retrieved from the API as proof that it was pushed natively
        fetched = integration_live_client.get_event(created.id)
        assert fetched.id == created.id
        assert fetched.title == created.title
    finally:
        if created_id:
            integration_live_client.delete_event(created_id)


def test_task_conversions_via_endpoints(integration_live_client: GoogleCalendarClient) -> None:
    """
    Test GoogleCalendarTask conversions via the client.create_task() endpoint.

    It uses client.get_task() endpoints over Live APIs.
    """
    now = datetime.now(tz=UTC)
    due = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    task_data = {
        "id": "dummy",
        "title": "Integration Task Conversions",
        "due": due.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "status": "needsAction",
    }

    task_to_create = GoogleCalendarTask(task_data)
    created_id = None
    try:
        # Test create_task conversion
        created = integration_live_client.create_task(task_to_create)
        created_id = created.id
        assert isinstance(created, GoogleCalendarTask)
        assert created.id is not None
        assert created.title == "Integration Task Conversions"
        assert created.is_completed is False

        # Test get_task conversion
        fetched = integration_live_client.get_task(created.id)
        assert isinstance(fetched, GoogleCalendarTask)
        assert fetched.id == created.id
        assert fetched.title == created.title
        assert fetched.is_completed is False
    finally:
        if created_id:
            integration_live_client.delete_task(created_id)


def test_cleanup_functions_verify_resources_scrubbed(
    integration_live_client: GoogleCalendarClient,
) -> None:
    """Test cleanup functions verifying resources have been scrubbed."""
    now = datetime.now(tz=UTC)

    start = (now + timedelta(hours=3)).replace(microsecond=0)
    end = (start + timedelta(hours=3)).replace(microsecond=0)

    # 1. Setup - Create an event and a task to delete
    event_data: dict[str, str | dict[str, str]] = {
        "id": "dummy",
        "summary": "Integration Cleanup Event",
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"}
    }
    event = integration_live_client.create_event(GoogleCalendarEvent(event_data))

    due = (now + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    task_data = {
        "id": "dummy",
        "title": "Integration Cleanup Task",
        "due": due.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "status": "needsAction",
    }
    task = integration_live_client.create_task(GoogleCalendarTask(task_data))

    # 2. Test cleanup explicit calls
    integration_live_client.delete_event(event.id)
    integration_live_client.delete_task(task.id)

    # 3. Verify scrubbed by ensuring get raises HttpError 404 or is marked cancelled.
    error_caught_ev = None
    try:
        integration_live_client.get_event(event.id)
    except HttpError as exc_info:
        error_caught_ev = exc_info

    if error_caught_ev:
        assert getattr(error_caught_ev, "status_code", 404) in (404, 400, 410)
    else:
        # If it didn't 404, verify the resource is "cancelled" in the raw API.
        raw_ev = integration_live_client._require_calendar_service().events().get(  # noqa: SLF001 # Needed to assert raw Google backend soft-deleted status
            calendarId=integration_live_client.calendar_id, eventId=event.id
        ).execute()
        assert raw_ev.get("status") == "cancelled"

    error_caught_task = None
    try:
        integration_live_client.get_task(task.id)
    except HttpError as e:
        error_caught_task = e

    if error_caught_task:
        assert getattr(error_caught_task, "status_code", 404) in (404, 400, 410)
    else:
        # If it didn't 404, verify it was marked deleted or hidden.
        raw_t = integration_live_client._require_tasks_service().tasks().get(  # noqa: SLF001 # Needed to assert raw Google backend soft-deleted status
            tasklist=integration_live_client.tasklist_id, task=task.id
        ).execute()
        assert raw_t.get("deleted") is True or raw_t.get("hidden") is True
