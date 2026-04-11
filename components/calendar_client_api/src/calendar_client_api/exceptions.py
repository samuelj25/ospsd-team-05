"""
Exceptions for calendar_client_api.

The three shared base exceptions are re-exported from ``ospsd_calendar_api``
so that all callers importing from this package continue to work without
changes.  ``TaskNotFoundError`` is a Team-05 private extension not present in
the common API.
"""

# Re-export the shared exceptions from the common cross-team API contract.
from ospsd_calendar_api.exceptions import (
    CalendarError,
    CalendarOperationError,  # noqa: F401
    EventNotFoundError,  # noqa: F401
)


class TaskNotFoundError(CalendarError):
    """
    Raised when a requested task does not exist.

    This exception is a Team-05 private extension — Google Tasks is not part
    of the shared ``ospsd_calendar_api`` contract.
    """
