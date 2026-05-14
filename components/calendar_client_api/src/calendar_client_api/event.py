"""
Event contract - Core event representation.

.. deprecated::
    This module is **superseded** by ``ospsd_calendar_api.models.Event`` (a
    concrete ``@dataclass``), which is now the canonical ``Event`` type used
    across all layers of the stack.

    This file is retained for historical reference only and is **no longer
    imported or used** by any active code in this repository.  New code should
    import ``Event`` from ``ospsd_calendar_api`` directly, or via the
    ``calendar_client_api`` package re-export::

        from calendar_client_api import Event        # dataclass from ospsd_calendar_api
        from ospsd_calendar_api.models import Event  # direct import
"""

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
