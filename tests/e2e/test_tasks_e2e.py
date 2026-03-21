"""End-To-End tests for compiling Task operations together into a full lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient
from google_calendar_client_impl.task_impl import GoogleCalendarTask
from googleapiclient.errors import HttpError


@pytest.mark.e2e
def test_task_lifecycle(live_client: GoogleCalendarClient) -> None:
    """Create a task, verify it exists, mark it as completed, verify its status, and delete it."""
    now = datetime.now(tz=UTC)
    due = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    task_data = {
        "id": "dummy",
        "title": "E2E Lifecycle Task",
        "due": due.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "status": "needsAction",
    }

    # 1. Create Task
    created = live_client.create_task(GoogleCalendarTask(task_data))
    assert created.id is not None
    assert created.title == "E2E Lifecycle Task"
    assert created.is_completed is False

    try:
        # 2. Verify it exists
        fetched = live_client.get_task(created.id)
        assert fetched.title == "E2E Lifecycle Task"
        assert fetched.is_completed is False

        # 3. Mark it completely
        live_client.mark_task_completed(created.id)

        # 4. Verify its Status
        refetched = live_client.get_task(created.id)
        assert refetched.is_completed is True

    finally:
        # 5. Finally Delete it
        live_client.delete_task(created.id)

        # Verify scrubbed by ensuring get raises HttpError 404
        error_caught = None
        try:
            live_client.get_task(created.id)
        except HttpError as e:
            error_caught = e

        if error_caught:
            assert getattr(error_caught, "status_code", 404) in (404, 400, 410)
        else:
            raw_t = (
                live_client._require_tasks_service()
                .tasks()
                .get(  # Needed to assert raw Google backend soft-deleted status
                    tasklist=live_client.tasklist_id, task=created.id
                )
                .execute()
            )
            assert raw_t.get("deleted") is True or raw_t.get("hidden") is True
