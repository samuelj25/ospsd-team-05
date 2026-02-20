"""Public export surface for ``calendar_client_api``."""

from calendar_client_api.client import Client, get_client
from calendar_client_api.event import Event
from calendar_client_api.task import Task
from calendar_client_api.exceptions import (
    CalendarError,
    CalendarOperationError,
    EventNotFoundError,
    TaskNotFoundError,
)
