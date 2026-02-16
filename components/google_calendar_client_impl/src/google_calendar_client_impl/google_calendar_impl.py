"""Google Calendar Client implementation."""

import os
from collections.abc import Iterator
from datetime import datetime

import calendar_client_api


class GoogleCalendarClient(calendar_client_api.Client):
    """
    Concrete implementation of the Client abstraction using Google Calendar API.

    Current implementation is a scaffold intended to satisfy the
    calendar_client_api.Client interface and type-check under mypy --strict.
    """

    def __init__(self) -> None:
        """Initialize the Google Calendar client."""
        super().__init__()

    def connect(self) -> None:
        """
        Authenticate and connect to Google Calendar API.

        Current implementation is a scaffold checking for environment variables.
        """
        print("Connecting to Google Calendar...")
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if not creds_path:
            print(
                "Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable "
                "not set."
            )
        else:
            print(f"Using credentials from: {creds_path}")

    def get_events(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Iterator[calendar_client_api.Event]:
        """Yield events in the provided time window."""
        _ = (start_time, end_time)
        return iter(())

    def get_event(self, event_id: str) -> calendar_client_api.Event:
        """Return an event by ID."""
        _ = event_id
        raise NotImplementedError

    def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID."""
        _ = event_id
        raise NotImplementedError

    def get_tasks(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Iterator[calendar_client_api.Task]:
        """Yield tasks in the provided time window."""
        _ = (start_time, end_time)
        raise NotImplementedError

    def get_task(self, task_id: str) -> calendar_client_api.Task:
        """Return a task by ID."""
        _ = task_id
        raise NotImplementedError

    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID."""
        _ = task_id
        raise NotImplementedError

    def mark_task_completed(self, task_id: str) -> bool:
        """Mark a task as completed."""
        _ = task_id
        raise NotImplementedError


def get_client_impl() -> calendar_client_api.Client:
    """Return a configured GoogleCalendarClient instance."""
    return GoogleCalendarClient()


def register() -> None:
    """Register the Google Calendar client implementation."""
    calendar_client_api.get_client = get_client_impl
