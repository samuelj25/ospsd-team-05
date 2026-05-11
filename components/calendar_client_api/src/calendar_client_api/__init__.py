"""
Public export surface for ``calendar_client_api``.

This package is a thin re-export shim over the shared cross-team vertical API
defined in ``ospsd_calendar_api``.  It exists so that all imports of the form
``from calendar_client_api import Event`` continue to work without change.

Team-05 private extensions (Google Tasks support) live in the separate
``calendar_task_api`` package and are intentionally not exported from here.
"""

from ospsd_calendar_api import CalendarClient as CalendarClient
from ospsd_calendar_api import Event as Event
from ospsd_calendar_api.exceptions import CalendarError as CalendarError
from ospsd_calendar_api.exceptions import CalendarOperationError as CalendarOperationError
from ospsd_calendar_api.exceptions import EventNotFoundError as EventNotFoundError
