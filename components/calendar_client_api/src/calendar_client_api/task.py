"""Task contract - Core task representation."""

from abc import ABC, abstractmethod
from datetime import datetime


class Task(ABC):
    """Abstract base class representing a calendar task."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the task."""
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> str:
        """Return title of the task."""
        raise NotImplementedError

    @property
    @abstractmethod
    def start_time(self) -> datetime:
        """Return time of the task."""
        raise NotImplementedError

    @property
    @abstractmethod
    def end_time(self) -> datetime:
        """Return end time of the task."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Return description of the task."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_completed(self) -> bool:
        """Return whether the task is completed."""
        raise NotImplementedError

# raw data?
def get_task(task_id: str) -> Task:
    """Return an instance of a task given its ID."""
    raise NotImplementedError
