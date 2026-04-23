"""
Public export surface for ``calendar_client_api``.

The shared types (``Event``, ``CalendarClient``, and the base exceptions) are
re-exported from ``ospsd_calendar_api`` so that all existing imports of the
form ``from calendar_client_api import Event`` continue to work without change.

Team-05 private extensions (``Task``, ``TaskNotFoundError``, and the extended
``Client`` ABC with task methods) are also re-exported from here.
"""

# ---------------------------------------------------------------------------
# Re-exports from the shared cross-team common API
# ---------------------------------------------------------------------------
from ospsd_calendar_api import CalendarClient as CalendarClient
from ospsd_calendar_api import Event as Event
from ospsd_calendar_api.exceptions import CalendarError as CalendarError
from ospsd_calendar_api.exceptions import CalendarOperationError as CalendarOperationError
from ospsd_calendar_api.exceptions import EventNotFoundError as EventNotFoundError

# ---------------------------------------------------------------------------
# Team-05 private extensions (Google Tasks — not in the common API)
# ---------------------------------------------------------------------------
from calendar_client_api.client import Client as Client
from calendar_client_api.client import get_client as get_client
from calendar_client_api.exceptions import TaskNotFoundError as TaskNotFoundError
from calendar_client_api.task import Task as Task
