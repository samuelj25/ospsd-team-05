"""End-To-End tests for compiling Task operations together into a full lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from calendar_client_adapter.adapter import ServiceAdapterClient
from calendar_client_api import TaskNotFoundError


@pytest.mark.e2e
def test_task_lifecycle(live_client: ServiceAdapterClient) -> None:
    """Create a task, verify it exists, mark it as completed, verify its status, and delete it."""
    now = datetime.now(tz=UTC)
    due = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Create Task (Passed as positional arguments to resolve kwargs mypy error)
    created = live_client.create_task("E2E Lifecycle Task", due)
    assert created.id is not None
    assert created.title == "E2E Lifecycle Task"
    assert created.is_completed is False

    try:
        # 2. Verify it exists
        fetched = live_client.get_task(created.id)
        assert fetched.title == "E2E Lifecycle Task"
        assert fetched.is_completed is False

        # 3. Mark it completed
        live_client.mark_task_completed(created.id)

        # 4. Verify its status
        refetched = live_client.get_task(created.id)
        assert refetched.is_completed is True

    finally:
        # 5. Delete it
        live_client.delete_task(created.id)

        # Verify it is deleted — the adapter raises TaskNotFoundError on 404.
        with pytest.raises(TaskNotFoundError):
            live_client.get_task(created.id)
