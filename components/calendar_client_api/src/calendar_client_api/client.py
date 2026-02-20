"""Core calendar client contract definitions and factory placeholder."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime

from calendar_client_api.event import Event
from calendar_client_api.task import Task

class Client(ABC):
    """Abstract base class representing a calendar client for calendar operations."""

    @abstractmethod
    def get_event(self, calendar_id: str, event_id: str) -> Event:
        """Fetch event by ID from a specific calendar."""
        raise NotImplementedError

    @abstractmethod
    def create_event(self, calendar_id: str, event: Event) -> Event:
        """Create a new event in a specific calendar."""
        raise NotImplementedError

    @abstractmethod
    def update_event(self, calendar_id: str, event: Event) -> Event:
        """Update an existing event in a specific calendar."""
        raise NotImplementedError

    @abstractmethod
    def delete_event(self, calendar_id: str, event_id: str) -> None:
        """Delete event by ID from a specific calendar."""
        raise NotImplementedError

    @abstractmethod
    def get_events(
        self, calendar_id: str, start_time: datetime, end_time: datetime
    ) -> Iterator[Event]:
        """Fetch all events from a specific calendar."""
        raise NotImplementedError

    @abstractmethod
    def from_raw_data(self, raw_data: str) -> Event:
        """Construct an Event object from raw JSON data."""
        raise NotImplementedError

    @abstractmethod
    def get_task(self, task_id: str) -> Task:
        """Fetch task by ID."""
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
        """Delete task by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_tasks(self, start_time: datetime, end_time: datetime) -> Iterator[Task]:
        """Fetch all tasks."""
        raise NotImplementedError

    @abstractmethod
    def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        raise NotImplementedError

    # Discuss if more

def get_client() -> Client:
    """Return an instance of a calendar client."""
    raise NotImplementedError
