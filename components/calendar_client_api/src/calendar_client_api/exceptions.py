"""
Exceptions for calendar_client_api.

The three shared base exceptions are re-exported from ``ospsd_calendar_api``
so that all callers importing from this package continue to work without
changes.

``TaskNotFoundError`` has been moved to ``calendar_task_api.exceptions`` — it
is a Team-05 private extension and is not part of the shared vertical contract.
"""

from ospsd_calendar_api.exceptions import (
    CalendarError,  # noqa: F401
    CalendarOperationError,  # noqa: F401
    EventNotFoundError,  # noqa: F401
)
