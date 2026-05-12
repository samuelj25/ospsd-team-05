"""
Team-05 private extension package for Google Tasks support.

This package is **not** part of the shared vertical API contract defined in
``ospsd_calendar_api``.  It extends ``ospsd_calendar_api.CalendarClient`` with
Google-Tasks-specific operations for Team-05's internal use only.

Exports:
    Task: Abstract base class for a calendar task.
    Client: Extended CalendarClient ABC that adds task methods.
    TaskNotFoundError: Raised when a requested task does not exist.
    get_client: Returns the registered Client instance.
"""

from calendar_task_api.client import Client as Client
from calendar_task_api.client import get_client as get_client
from calendar_task_api.exceptions import TaskNotFoundError as TaskNotFoundError
from calendar_task_api.task import Task as Task
