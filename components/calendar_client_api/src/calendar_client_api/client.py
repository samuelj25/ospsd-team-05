"""Core calendar client contract definitions and factory placeholder."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime

from calendar_client_api.event import Event
from calendar_client_api.task import Task

__all__ = ["Client", "get_client"]

class Client(ABC):
    """Abstract base class representing a calendar client for calendar operations."""

    @abstractmethod
    def get_event(self, event_id: str) -> Event:
        """Fetch event by ID."""
        raise NotImplementedError

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete event by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_events(self, start_time: datetime, end_time: datetime) -> Iterator[Event]:
        """Fetch all events."""
        raise NotImplementedError

    # Kinda redundant
    @abstractmethod
    def get_task(self, task_id: str) -> Task:
        """Fetch task by ID."""
        raise NotImplementedError

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """Delete task by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_tasks(self, start_time: datetime, end_time: datetime) -> Iterator[Task]:
        """Fetch all tasks."""
        raise NotImplementedError

    @abstractmethod
    def mark_task_completed(self, task_id: str) -> bool:
        """Mark a task as completed."""
        raise NotImplementedError

    # Discuss if more

def get_client() -> Client:
    """Return an instance of a calendar client."""
    raise NotImplementedError
