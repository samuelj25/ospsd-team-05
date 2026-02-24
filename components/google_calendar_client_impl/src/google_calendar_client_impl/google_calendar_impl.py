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

    def __init__(self, calendar_id: str = "primary") -> None:
        """
        Initialize the Google Calendar client.

        Args:
            calendar_id: The Google Calendar ID to operate on.
                         Defaults to ``"primary"``.

        """
        super().__init__()
        self.calendar_id = calendar_id

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

    def get_event(self, event_id: str) -> calendar_client_api.Event:
        """Return an event by ID from the configured calendar."""
        _ = (self.calendar_id, event_id)
        raise NotImplementedError

    def create_event(
        self, event: calendar_client_api.Event
    ) -> calendar_client_api.Event:
        """Create a new event in the configured calendar."""
        _ = (self.calendar_id, event)
        raise NotImplementedError

    def update_event(
        self, event: calendar_client_api.Event
    ) -> calendar_client_api.Event:
        """Update an existing event in the configured calendar."""
        _ = (self.calendar_id, event)
        raise NotImplementedError

    def delete_event(self, event_id: str) -> None:
        """Delete an event by ID from the configured calendar."""
        _ = (self.calendar_id, event_id)
        raise NotImplementedError

    def get_events(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Iterator[calendar_client_api.Event]:
        """Yield events in the provided time window from the configured calendar."""
        _ = (self.calendar_id, start_time, end_time)
        return iter(())

    def from_raw_data(self, raw_data: str) -> calendar_client_api.Event:
        """Construct an Event object from raw JSON data."""
        _ = raw_data
        raise NotImplementedError

    def get_task(self, task_id: str) -> calendar_client_api.Task:
        """Return a task by ID."""
        _ = task_id
        raise NotImplementedError

    def create_task(self, task: calendar_client_api.Task) -> calendar_client_api.Task:
        """Create a new task."""
        _ = task
        raise NotImplementedError

    def update_task(self, task: calendar_client_api.Task) -> calendar_client_api.Task:
        """Update an existing task."""
        _ = task
        raise NotImplementedError

    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        _ = task_id
        raise NotImplementedError

    def get_tasks(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Iterator[calendar_client_api.Task]:
        """Yield tasks in the provided time window."""
        _ = (start_time, end_time)
        raise NotImplementedError

    def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        _ = task_id
        raise NotImplementedError


def get_client_impl() -> calendar_client_api.Client:
    """Return a configured GoogleCalendarClient instance."""
    return GoogleCalendarClient()


def register() -> None:
    """Register the Google Calendar client implementation."""
    calendar_client_api.get_client = get_client_impl
