"""Exceptions for calendar_client_api."""

class CalendarError(Exception):
    """Base exception for calendar_client_api errors."""
    pass

class EventNotFoundError(CalendarError):
    """Raised when an event is not found."""
    pass

class TaskNotFoundError(CalendarError):
    """Raised when a task is not found."""
    pass

class CalendarOperationError(CalendarError):
    """Raised when a calendar operation fails."""
    pass
