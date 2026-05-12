"""
Exceptions for calendar_task_api.

``TaskNotFoundError`` is a Team-05 private extension — Google Tasks is not
part of the shared ``ospsd_calendar_api`` contract.
"""

from ospsd_calendar_api.exceptions import CalendarError


class TaskNotFoundError(CalendarError):
    """
    Raised when a requested task does not exist.

    This exception is a Team-05 private extension — Google Tasks is not part
    of the shared ``ospsd_calendar_api`` contract.
    """
