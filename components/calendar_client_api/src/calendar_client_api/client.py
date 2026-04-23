"""
Extended calendar client contract — Team-05 superset of the common API.

This module defines :class:`Client`, which **subclasses**
:class:`ospsd_calendar_api.CalendarClient` (the shared cross-team interface)
and extends it with Google-Tasks-specific operations.

Event methods (``list_events``, ``get_event``, ``create_event``,
``update_event``, ``delete_event``) are inherited directly from the common
``CalendarClient`` ABC with their canonical signatures:

- ``create_event(title, start, end, description="", location=None) -> Event``
- ``update_event(event_id, **kwargs) -> Event``
- ``list_events(start, end) -> list[Event]``

Task methods are a Team-05 private extension and are not present in the
shared ``ospsd_calendar_api`` contract.
"""

from abc import abstractmethod
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from ospsd_calendar_api import CalendarClient
from ospsd_calendar_api.models import Event

from calendar_client_api.task import Task


class Client(CalendarClient):
    """
    Extended ``CalendarClient`` that also supports Google Tasks operations.

    All five event methods from :class:`ospsd_calendar_api.CalendarClient` are
    inherited as abstract methods and must be implemented by concrete
    subclasses.  The six task methods below are additional abstract methods
    that are specific to Team-05's Google Tasks integration.
    """

    # ------------------------------------------------------------------
    # Task operations (Team-05 private extension — not in the common API)
    # ------------------------------------------------------------------

    @abstractmethod
    def get_task(self, task_id: str) -> Task:
        """Fetch a task by ID."""
        raise NotImplementedError

    @abstractmethod
    def create_task(self, task: Task) -> Task:
        """Create a new task."""
        raise NotImplementedError

    @abstractmethod
    def update_task(self, task: Task) -> Task:
        """Update an existing task."""
        raise NotImplementedError

    @abstractmethod
    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_tasks(self, start_time: datetime, end_time: datetime) -> Iterator[Task]:
        """Fetch all tasks within a time window."""
        raise NotImplementedError

    @abstractmethod
    def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Legacy helper (not in CalendarClient; retained for internal use)
    # ------------------------------------------------------------------

    @abstractmethod
    def from_raw_data(self, raw_data: str) -> Event:
        """
        Construct an Event from a raw JSON string without an API call.

        Useful for reconstructing events from a database cache or webhook
        payload.
        """
        raise NotImplementedError

    # Keep the unused **kwargs override so that concrete subclasses that
    # implement update_event with typed kwargs still satisfy mypy's strict-mode
    # abstract-method check via CalendarClient.
    @abstractmethod
    def update_event(self, event_id: str, **kwargs: Any) -> Event:  # noqa: ANN401
        """Update fields on an existing event (see CalendarClient for full docs)."""
        raise NotImplementedError


def get_client() -> Client:
    """
    Return an instance of the registered calendar client.

    This function is patched at runtime by the concrete implementation's
    ``register()`` call (e.g. ``google_calendar_client_impl.register()`` or
    ``calendar_client_adapter.register()``).
    """
    raise NotImplementedError
