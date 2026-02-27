"""Event contract - Core event representation."""

from abc import ABC, abstractmethod
from datetime import datetime


class Event(ABC):
    """Abstract base class representing a calendar event."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the event."""
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> str:
        """Return title of the event."""
        raise NotImplementedError

    @property
    @abstractmethod
    def start_time(self) -> datetime:
        """Return start time of the event."""
        raise NotImplementedError

    @property
    @abstractmethod
    def end_time(self) -> datetime:
        """Return end time of the event."""
        raise NotImplementedError

    @property
    @abstractmethod
    def location(self) -> str | None:
        """Return location of the event."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str | None:
        """Return description of the event."""
        raise NotImplementedError

